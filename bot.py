import os
import telebot
import requests
import time
from flask import Flask, request

API_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://retete.onrender.com")

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

def generate_image(prompt):
    url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {REPLICATE_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "version": "fb4f086702d6a301ca32c170d926239324a7b7b2f0afc3d232a9c4be382dc3fa",
        "input": {
            "prompt": prompt,
            "negative_prompt": "blurry, ugly, distorted, low quality",
            "num_inference_steps": 30,
            "guidance_scale": 7.5,
            "width": 512,
            "height": 768
        }
    }

    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        prediction = response.json()
        return prediction["urls"]["get"], None
    else:
        error_text = f"❌ Ошибка генерации:\n{response.status_code}\n{response.text}"
        return None, error_text

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "👋 Привет! Напиши описание изображения, и я его сгенерирую.")

@bot.message_handler(func=lambda m: True)
def handle_prompt(message):
    prompt = message.text.strip()
    if not prompt:
        bot.send_message(message.chat.id, "⚠️ Пожалуйста, введите текстовое описание.")
        return

    bot.send_message(message.chat.id, "🧠 Генерирую изображение, подожди...")

    status_url, error = generate_image(prompt)
    if error:
        bot.send_message(message.chat.id, error)
        return

    for i in range(20):
        res = requests.get(status_url, headers={"Authorization": f"Token {REPLICATE_TOKEN}"})
        if res.status_code != 200:
            bot.send_message(message.chat.id, f"⚠️ Ошибка получения статуса:\n{res.status_code}\n{res.text}")
            break

        status = res.json()
        if status.get("status") == "succeeded":
            image_url = status["output"][0]
            bot.send_photo(message.chat.id, image_url)
            return
        elif status.get("status") == "failed":
            bot.send_message(message.chat.id, f"⚠️ Генерация не удалась.\n\n`{res.text}`", parse_mode="Markdown")
            return

        time.sleep(2)

    bot.send_message(message.chat.id, "❌ Не удалось сгенерировать изображение за отведённое время.")

@app.route('/', methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return '', 200

@app.route('/', methods=['GET'])
def index():
    return '✅ Bot is running!'

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))