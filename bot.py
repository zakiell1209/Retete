# --- bot.py ---
import os
import time
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
user_settings = {}

# ⚙️ Категории и теги — не меняем
# (загружаются как есть — пропущено в этом коде ради краткости)

# 🎯 Построение промпта
def build_prompt(tags):
    character_prompts = []
    pose_prompts = []
    rest_prompts = []

    for tag in tags:
        prompt = TAG_PROMPTS.get(tag, tag)
        if tag in CHARACTER_EXTRA:
            character_prompts.append(prompt)
        elif tag in TAGS["poses"]:
            pose_prompts.append(prompt)
        else:
            rest_prompts.append(prompt)

    base = "nsfw, masterpiece, ultra detailed, anime style, best quality, solo, full body, fully nude, spread legs"
    full_prompt = ", ".join([base] + character_prompts + pose_prompts + rest_prompts)

    return full_prompt

# ❌ Отрицательный промпт
NEGATIVE_PROMPT = (
    "censored, mosaic, blurry, pixelated, low quality, watermark, text, duplicate, multiple girls, "
    "clothes, hands covering breasts, hair covering genitals, objects covering chest, arms over breasts, "
    "covered nipples, pubic hair, background clutter"
)

# 📤 Генерация
def replicate_generate(prompt):
    url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {REPLICATE_TOKEN}",
        "Content-Type": "application/json"
    }
    json_data = {
        "version": REPLICATE_MODEL,
        "input": {
            "prompt": prompt,
            "negative_prompt": NEGATIVE_PROMPT
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
            return data["output"][0] if isinstance(data["output"], list) else data["output"]
        elif data["status"] == "failed":
            return None
    return None

# 💬 Команды и интерфейс (start, выбор тегов, генерация, редактирование) — не меняем

# 📡 Webhook
@app.route("/", methods=["POST"])
def webhook():
    json_str = request.stream.read().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "ok", 200

@app.route("/", methods=["GET"])
def home():
    return "бот работает", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=PORT)