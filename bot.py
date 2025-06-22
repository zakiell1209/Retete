# --- bot.py (финальная версия) ---
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

# Отражение по категориям и тегам (укорочено для примера)
CATEGORY_NAMES = {
    "clothes": "Одежда", "head": "Голова"
}
TAGS = {
    "clothes": {
        "stockings": "Чулки", "bikini_tan_lines": "Загар от бикини"
    },
    "head": {
        "ahegao": "Ахегао", "ecstasy_face": "Лицо в экстазе"
    }
}
TAG_PROMPTS = {
    "stockings": "stockings only, no panties, no bra, no other clothes",
    "bikini_tan_lines": "dark tanned skin with clear white bikini tan lines, no bikini, no clothing, no underwear",
    "ahegao": "ahegao face, tongue out, eyes rolling",
    "ecstasy_face": "face in orgasmic ecstasy"
}

NEGATIVE_PROMPT = (
    "male, man, penis, testicles, muscular male, hands covering chest, hand on breast, censored, "
    "clothes, blurry, lowres, bad anatomy, text, watermark"
)

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
        count = user_settings[cid]["count"]
        prompt = build_prompt(tags)
        bot.send_message(cid, "⏳ Генерация изображений...")
        images = generate_images(prompt, count)
        if images:
            media = [types.InputMediaPhoto(img) for img in images]
            bot.send_media_group(cid, media)
        else:
            bot.send_message(cid, "❌ Ошибка генерации.")

def build_prompt(tags):
    base = "nsfw, masterpiece, ultra detailed, best quality"
    prompts = [TAG_PROMPTS.get(tag, tag) for tag in tags]
    return base + ", " + ", ".join(prompts)

def generate_images(prompt, num_outputs=1):
    url = "https://api.replicate.com/v1/predictions"
    headers = {"Authorization": f"Token {REPLICATE_TOKEN}", "Content-Type": "application/json"}
    json_data = {
        "version": REPLICATE_MODEL,
        "input": {
            "prompt": prompt,
            "negative_prompt": NEGATIVE_PROMPT,
            "num_outputs": min(num_outputs, 4)
        }
    }
    r = requests.post(url, headers=headers, json=json_data)
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
            return data["output"] if isinstance(data["output"], list) else [data["output"]]
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
