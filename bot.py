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

NEGATIVE_PROMPT = "male, man, penis, testicles, muscular male, hands on chest, hand covering nipple, hand covering breasts, censored, bra, panties, blurry, lowres, bad anatomy, watermark, text, logo"

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
user_settings = {}

def main_menu():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🧩 Выбрать теги", callback_data="choose_tags"))
    kb.add(types.InlineKeyboardButton("📸 Кол-во изображений", callback_data="choose_count"))
    kb.add(types.InlineKeyboardButton("🎨 Генерировать", callback_data="generate"))
    return kb

@bot.message_handler(commands=["start"])
def start(msg):
    cid = msg.chat.id
    user_settings[cid] = {"prompt": "", "count": 1}
    bot.send_message(cid, "Привет! Отправь описание (prompt) или выбери действие ниже:", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    cid = call.message.chat.id
    data = call.data

    if cid not in user_settings:
        user_settings[cid] = {"prompt": "", "count": 1}

    if data == "choose_tags":
        bot.send_message(cid, "Просто напиши описание вручную, например:

`девушка в чулках, на шпагате, фури кошка`")
    elif data == "choose_count":
        kb = types.InlineKeyboardMarkup(row_width=4)
        for i in range(1, 5):
            kb.add(types.InlineKeyboardButton(f"{i}", callback_data=f"count_{i}"))
        kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="back_main"))
        bot.edit_message_text("Выбери количество изображений:", cid, call.message.message_id, reply_markup=kb)
    elif data.startswith("count_"):
        count = int(data.split("_")[1])
        user_settings[cid]["count"] = count
        bot.send_message(cid, f"✅ Выбрано изображений: {count}", reply_markup=main_menu())
    elif data == "back_main":
        bot.edit_message_text("Возврат в главное меню", cid, call.message.message_id, reply_markup=main_menu())
    elif data == "generate":
        prompt = user_settings[cid].get("prompt", "")
        count = user_settings[cid].get("count", 1)
        if not prompt:
            bot.send_message(cid, "Сначала отправь описание.")
            return
        bot.send_message(cid, f"⏳ Генерация {count} изображений...")
        images = replicate_generate(prompt, count)
        if not images:
            bot.send_message(cid, "❌ Не удалось сгенерировать изображения.")
            return
        media = [types.InputMediaPhoto(url) for url in images]
        bot.send_media_group(cid, media)

@bot.message_handler(content_types=["text"])
def set_prompt(msg):
    cid = msg.chat.id
    user_settings[cid] = user_settings.get(cid, {})
    user_settings[cid]["prompt"] = msg.text.strip()
    bot.send_message(cid, f"✅ Промпт установлен:
`{msg.text.strip()}`
Теперь нажми «🎨 Генерировать»", reply_markup=main_menu())

def replicate_generate(prompt, num_outputs=1):
    url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {REPLICATE_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "version": REPLICATE_MODEL,
        "input": {
            "prompt": prompt,
            "negative_prompt": NEGATIVE_PROMPT,
            "num_outputs": min(max(1, num_outputs), 4)
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
        result = r.json()
        if result["status"] == "succeeded":
            return result["output"] if isinstance(result["output"], list) else [result["output"]]
        if result["status"] == "failed":
            return []
    return []

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
