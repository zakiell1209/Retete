# --- bot.py ---
import os
import time
import requests
import random
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

CATEGORY_NAMES = {
    "holes": "Отверстия", "toys": "Игрушки", "poses": "Позы", "clothes": "Одежда",
    "body": "Тело", "ethnos": "Этнос", "furry": "Фури", "characters": "Персонажи",
    "head": "Голова", "view": "Обзор"
}

TAGS = {
    "characters": {
        "rias": "Риас Гремори", "akeno": "Акено Химэдзима", "kafka": "Кафка (Хонкай)",
        "eula": "Еула (Геншин)", "fu_xuan": "Фу Сюань", "ayase": "Аясе Сейко"
    },
    "head": {
        "ahegao": "Ахегао", "pain_face": "Лицо в боли", "ecstasy_face": "Лицо в экстазе",
        "gold_lipstick": "Золотая помада"
    }
    # Остальные категории можно вставить как раньше — для краткости не дублируем
}

TAG_PROMPTS = {
    # Головные
    "ahegao": "ahegao expression, tongue out, eyes rolled up",
    "pain_face": "face contorted in pain, tears",
    "ecstasy_face": "face in pleasure, open mouth, flushed",
    "gold_lipstick": "gold lipstick, visible lips",

    # Персонажи
    "rias": "rias gremory from high school dxd",
    "akeno": "akeno himejima from high school dxd",
    "kafka": "kafka from honkai star rail",
    "eula": "eula from genshin impact",
    "fu_xuan": "fu xuan from honkai star rail",
    "ayase": "ayase seiko from original work",

    # Анти-руки (добавлены глобально)
}

NEGATIVE_PROMPT = (
    "male, man, penis, testicles, muscular male, censored, watermark, text, extra limbs, "
    "clothes, panties, bra, blurry, lowres, jpeg artifacts, hands on chest, hands covering nipples, "
    "covering genitals, badly drawn, multiple people, duplicate, watermark, signature"
)

def build_prompt(tags):
    base = (
        "nsfw, masterpiece, best quality, solo female, anime style, "
        "fully nude, visible nipples, detailed body, arms down, hands away from chest, no censorship"
    )
    prompts = [TAG_PROMPTS.get(tag, tag) for tag in tags]
    return base + ", " + ", ".join(prompts)

@bot.message_handler(commands=["start"])
def start(msg):
    cid = msg.chat.id
    user_settings[cid] = {"tags": [], "count": 1}
    bot.send_message(cid, "Привет! Выбирай действие.", reply_markup=main_menu())

def main_menu():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🎯 Теги", callback_data="choose_tags"))
    kb.add(types.InlineKeyboardButton("🎨 Генерация", callback_data="generate"))
    return kb

@bot.callback_query_handler(func=lambda c: True)
def callback(call):
    cid = call.message.chat.id
    data = call.data
    if cid not in user_settings:
        user_settings[cid] = {"tags": [], "count": 1}

    if data == "choose_tags":
        bot.edit_message_text("Выбери категорию:", cid, call.message.message_id, reply_markup=category_menu())
    elif data.startswith("cat_"):
        cat = data[4:]
        user_settings[cid]["last_cat"] = cat
        selected = user_settings[cid]["tags"]
        bot.edit_message_text(f"Категория: {CATEGORY_NAMES[cat]}", cid, call.message.message_id, reply_markup=tag_menu(cat, selected))
    elif data.startswith("tag_"):
        _, cat, tag = data.split("_", 2)
        tags = user_settings[cid]["tags"]
        if tag in tags:
            tags.remove(tag)
        else:
            tags.append(tag)
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=tag_menu(cat, tags))
    elif data == "generate":
        tags = user_settings[cid]["tags"]
        count = user_settings[cid].get("count", 1)
        if not tags:
            bot.send_message(cid, "Сначала выбери теги.")
            return
        prompt = build_prompt(tags)
        bot.send_message(cid, f"⏳ Генерация ({count} шт)...")
        images = generate_images(prompt, count)
        if not images:
            bot.send_message(cid, "❌ Не удалось сгенерировать.")
        else:
            media = [types.InputMediaPhoto(url) for url in images]
            bot.send_media_group(cid, media)

def generate_images(prompt, count):
    url = "https://api.replicate.com/v1/predictions"
    headers = {"Authorization": f"Token {REPLICATE_TOKEN}", "Content-Type": "application/json"}
    data = {
        "version": REPLICATE_MODEL,
        "input": {
            "prompt": prompt,
            "negative_prompt": NEGATIVE_PROMPT,
            "num_outputs": min(count, 4)
        }
    }
    r = requests.post(url, headers=headers, json=data)
    if r.status_code != 201:
        return []
    status_url = r.json()["urls"]["get"]
    for _ in range(60):
        time.sleep(2)
        r = requests.get(status_url, headers=headers)
        if r.status_code != 200:
            return []
        res = r.json()
        if res["status"] == "succeeded":
            return res["output"] if isinstance(res["output"], list) else [res["output"]]
        if res["status"] == "failed":
            return []
    return []

def category_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    for key, name in CATEGORY_NAMES.items():
        kb.add(types.InlineKeyboardButton(name, callback_data=f"cat_{key}"))
    kb.add(types.InlineKeyboardButton("✅ Готово", callback_data="generate"))
    return kb

def tag_menu(category, selected_tags):
    kb = types.InlineKeyboardMarkup(row_width=2)
    for tag_key, tag_name in TAGS[category].items():
        label = f"✅ {tag_name}" if tag_key in selected_tags else tag_name
        kb.add(types.InlineKeyboardButton(label, callback_data=f"tag_{category}_{tag_key}"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="choose_tags"))
    return kb

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