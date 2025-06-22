# --- bot.py ---
import os
import time
import requests
from flask import Flask, request
import telebot
from telebot import types

API_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")
REPLICATE_MODEL = "057e2276ac5dcd8d1575dc37b131f903df9c10c41aed53d47cd7d4f068c19fa5"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 5000))

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
user_settings = {}

NEGATIVE_PROMPT = (
    "male, penis, testicles, man, muscular male, censored, blurry, lowres, bad anatomy, watermark, "
    "clothes, bra, panties, hand on breast, hands on chest, fingers on nipples, covering chest, "
    "nude censored, realistic censor, mosaic, nsfw censor, arm crossing chest"
)

TAG_PROMPTS = {
    "rias": "rias gremory from highschool dxd, red hair, large breasts",
    "akeno": "akeno himejima from highschool dxd, long black hair, seductive expression",
    "eula": "eula from genshin impact, blue hair, elegant pose",
    "fu_xuan": "fu xuan from honkai star rail, purple twin-tails, confident look",
    "ayase": "ayase seiko, pink hair, school uniform, anime style",
    "kafka": "kafka from honkai star rail, purple long hair, glasses, bodysuit",

    "ahegao": "ahegao face, tongue out, rolling eyes",
    "pain_face": "face twisted in pain",
    "ecstasy_face": "face showing ecstasy",

    "gold_lipstick": "gold lipstick on lips only",

    "no_hands_on_chest": "hands away from chest, arms down, not touching body",
}

def main_menu():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🧩 Выбрать теги", callback_data="choose_tags"))
    kb.add(types.InlineKeyboardButton("🎨 Генерировать", callback_data="generate"))
    return kb

@bot.message_handler(commands=["start"])
def start(msg):
    cid = msg.chat.id
    user_settings[cid] = {"tags": [], "count": 1}
    bot.send_message(cid, "Привет! Что делаем?", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    cid = call.message.chat.id
    data = call.data

    if cid not in user_settings:
        user_settings[cid] = {"tags": [], "count": 1}

    if data == "generate":
        tags = user_settings[cid]["tags"]
        count = min(max(user_settings[cid].get("count", 1), 1), 4)
        if not tags:
            bot.send_message(cid, "❌ Сначала выбери теги!")
            return
        prompt = build_prompt(tags)
        bot.send_message(cid, f"🎨 Генерация {count} изображений...")
        images = []
        for _ in range(count):
            url = replicate_generate(prompt)
            if url:
                images.append(url)
        if images:
            media = [types.InputMediaPhoto(url) for url in images]
            bot.send_media_group(cid, media)
            post_kb = types.InlineKeyboardMarkup()
            post_kb.add(
                types.InlineKeyboardButton("🔁 Начать заново", callback_data="start_over"),
                types.InlineKeyboardButton("🛠 Редактировать теги", callback_data="edit_tags"),
                types.InlineKeyboardButton("🔂 Продолжить генерацию", callback_data="generate")
            )
            bot.send_message(cid, "✅ Готово!", reply_markup=post_kb)
        else:
            bot.send_message(cid, "❌ Не удалось сгенерировать изображения.")

    elif data == "start_over":
        user_settings[cid] = {"tags": [], "count": 1}
        bot.send_message(cid, "🔄 Начнём заново!", reply_markup=main_menu())

    elif data == "edit_tags":
        if "tags" in user_settings[cid]:
            bot.send_message(cid, "Редактируем теги (введи текстом или нажми /start):")
        else:
            bot.send_message(cid, "Нет тегов для редактирования. Используй /start")

@bot.message_handler(func=lambda msg: True, content_types=["text"])
def handle_tags(msg):
    cid = msg.chat.id
    raw = msg.text.lower().split(",")
    tags = []
    for r in raw:
        r = r.strip()
        if r in TAG_PROMPTS:
            tags.append(r)
    if not tags:
        bot.send_message(cid, "❌ Не удалось распознать теги. Используй /start")
        return
    user_settings[cid] = {"tags": tags, "count": 1}
    bot.send_message(cid, f"✅ Выбраны теги: {', '.join(tags)}", reply_markup=main_menu())

def build_prompt(tags):
    base = "nsfw, masterpiece, best quality, ultra detailed, anime style, solo female, fully nude, visible nipples, arms at sides, no clothing"
    mapped = [TAG_PROMPTS.get(t, t) for t in tags]
    return base + ", " + ", ".join(mapped)

def replicate_generate(prompt):
    url = "https://api.replicate.com/v1/predictions"
    headers = {"Authorization": f"Token {REPLICATE_TOKEN}", "Content-Type": "application/json"}
    data = {
        "version": REPLICATE_MODEL,
        "input": {
            "prompt": prompt,
            "negative_prompt": NEGATIVE_PROMPT,
            "num_outputs": 1
        }
    }
    r = requests.post(url, headers=headers, json=data)
    if r.status_code != 201:
        return None
    status_url = r.json()["urls"]["get"]
    for _ in range(60):
        time.sleep(2)
        r = requests.get(status_url, headers=headers)
        if r.status_code != 200:
            return None
        data = r.json()
        if data["status"] == "succeeded":
            output = data["output"]
            return output[0] if isinstance(output, list) else output
        elif data["status"] == "failed":
            return None
    return None

@app.route("/", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "ok", 200

@app.route("/", methods=["GET"])
def home():
    return "бот работает", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=PORT)