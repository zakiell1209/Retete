import os
import time
import json
import logging
import requests
from flask import Flask, request
import telebot
from telebot import types

API_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 5000))
REPLICATE_MODEL = "c1d5b02687df6081c7953c74bcc527858702e8c153c9382012ccc3906752d3ec"

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

user_settings = {}

# 💬 Русские теги → англ. ID
RU_TO_TAG = {
    "анус": "anal", "вагина": "vagina", "вся в сперме": "cum", "футанари": "futanari",
    "большая грудь": "big_breasts", "чулки": "stockings", "шибари": "shibari",
    "ахегао": "ahegao", "золотая помада": "gold_lipstick", "вертикальный шпагат": "ver_split",
    "горизонтальный шпагат": "hor_split", "подвешена": "suspended", "приседание": "squat",
    "каблуки": "heels", "сперма": "cum", "маска": "mask", "возраст 21": "age_21",
    "азиатка": "ethnicity_asian", "европейка": "ethnicity_european",
    "на боку с поднятой ногой": "side_up_leg", "лицом к зрителю": "front_facing",
    "спиной к зрителю": "back_facing", "мост": "bridge", "лежит с коленями вверх": "lying_knees_up",
    "снизу": "view_under", "сверху": "view_above", "сбоку": "view_side",
    "дальше": "view_far", "ближе": "view_close", "лоли": "age_loli", "милфа": "age_milf",
    "белая кожа": "skin_white", "черная кожа": "skin_black",
    "фури кролик": "furry_bunny", "фури кошка": "furry_cat", "фури лисица": "furry_fox",
    "фури волчица": "furry_wolf", "фури сильвеон": "furry_sylveon", "фури дракон": "furry_dragon",
    "акено химедзима": "akeno", "риас гремори": "rias", "кафка": "kafka",
    "фу сюань": "fu_xuan", "еола": "eula", "аясе сейко": "ayase"
}

# 💡 Расширенные промпты
TAG_PROMPTS = {
    "futanari": "futanari, penis",
    "big_breasts": "very large breasts, visible, uncovered",
    "anal": "visible anus",
    "dildo": "dildo, inserted",
    "cum": "covered in cum",
    "gold_lipstick": "gold lipstick on lips only",
    "ahegao": "ahegao expression",
    "ver_split": "vertical split, standing leg up, gymnastics, full body pose",
    "hor_split": "horizontal split on the floor, full body pose",
    "view_under": "view from under the body, under the floor",
    "view_above": "top-down view",
    "view_side": "side angle",
    "view_far": "zoomed out, full body visible",
    "view_close": "close-up, partial body in frame",
    "rias": "red hair, blue eyes, pale skin, rias gremory, highschool dxd",
    "akeno": "black hair, purple eyes, akeno himejima, highschool dxd",
    "kafka": "purple hair, kafka, honkai star rail",
    "fu_xuan": "pink hair, fu xuan, honkai star rail",
    "eula": "light blue hair, eula, genshin impact",
    "ayase": "black hair, school uniform, ayase seiko"
}

def build_prompt(tags):
    base = "nsfw, masterpiece, best quality, anime style, full body, ultra detailed, fully nude, no hands on breasts"
    extra = [TAG_PROMPTS.get(tag, tag.replace("_", " ")) for tag in tags]
    return f"{base}, {', '.join(extra)}"

def replicate_generate(prompt, count=1):
    url = "https://api.replicate.com/v1/predictions"
    headers = {"Authorization": f"Token {REPLICATE_TOKEN}", "Content-Type": "application/json"}
    urls = []

    for _ in range(count):
        response = requests.post(url, headers=headers, json={
            "version": REPLICATE_MODEL,
            "input": {"prompt": prompt}
        })
        if response.status_code != 201:
            continue
        status_url = response.json()["urls"]["get"]

        for _ in range(60):
            time.sleep(2)
            status = requests.get(status_url, headers=headers)
            if status.status_code != 200:
                break
            data = status.json()
            if data["status"] == "succeeded":
                output = data["output"]
                urls.append(output[0] if isinstance(output, list) else output)
                break
            elif data["status"] == "failed":
                break
    return urls

# 🚀 Команды
@bot.message_handler(commands=["start"])
def start(msg):
    cid = msg.chat.id
    user_settings[cid] = {"tags": [], "last_prompt": []}
    bot.send_message(cid, "Привет! Введите теги через запятую или нажмите кнопку.", reply_markup=main_menu())

def main_menu():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🧩 Выбрать теги", callback_data="choose_tags"))
    kb.add(types.InlineKeyboardButton("🎨 Генерировать", callback_data="generate"))
    return kb

# ✏️ Ввод тегов вручную
@bot.message_handler(func=lambda m: True, content_types=["text"])
def handle_text(msg):
    cid = msg.chat.id
    text = msg.text.strip().lower()
    count = 1
    parts = [p.strip() for p in text.split(",")]
    if parts and parts[-1].isdigit():
        count = min(10, max(1, int(parts.pop())))
    tags = []
    unknown = []
    for word in parts:
        tag = RU_TO_TAG.get(word)
        if tag:
            tags.append(tag)
        else:
            unknown.append(word)
    if unknown:
        bot.send_message(cid, f"Неизвестные теги: {', '.join(unknown)}")
        return
    user_settings[cid] = {"tags": tags, "last_prompt": tags}
    bot.send_message(cid, f"⏳ Генерация {count} изображений...")
    prompt = build_prompt(tags)
    urls = replicate_generate(prompt, count)
    if urls:
        for url in urls:
            bot.send_photo(cid, url, reply_markup=result_menu())
    else:
        bot.send_message(cid, "❌ Не удалось сгенерировать изображение.")

def result_menu():
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("🔁 Начать заново", callback_data="start"),
        types.InlineKeyboardButton("🎨 Ещё раз", callback_data="generate")
    )
    return kb

# 📩 Обработка колбэков
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    cid = call.message.chat.id
    if call.data == "start":
        return start(call.message)
    elif call.data == "generate":
        tags = user_settings.get(cid, {}).get("last_prompt", [])
        if not tags:
            bot.send_message(cid, "Сначала выберите теги.")
            return
        prompt = build_prompt(tags)
        urls = replicate_generate(prompt)
        if urls:
            for url in urls:
                bot.send_photo(cid, url, reply_markup=result_menu())
        else:
            bot.send_message(cid, "❌ Ошибка генерации.")
    elif call.data == "choose_tags":
        bot.send_message(cid, "Введите теги через запятую. Например: риас гремори, футанари, анус, дилдо")

# 🌐 Вебхуки
@app.route("/", methods=["POST"])
def webhook():
    json_str = request.stream.read().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "ok", 200

@app.route("/", methods=["GET"])
def home():
    return "бот активен", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=PORT)