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

# Версия модели Flux NSFW (актуальную лучше проверить на replicate.com)
MODEL_VERSION = "a2c7a12413262db9d4f827b0c7b9f7a545f4073a9bc541d50333e15c3c6f7df9"

def generate_image(prompt):
    url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {REPLICATE_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "version": MODEL_VERSION,
        "input": {"prompt": prompt}
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        prediction = response.json()
        return prediction["urls"]["get"]
    else:
        return f"Ошибка генерации: {response.status_code} {response.text}"

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Напиши описание изображения для генерации (NSFW).")

@bot.message_handler(func=lambda m: True)
def handle_prompt(message):
    prompt = message.text
    bot.send_message(message.chat.id, "Генерирую изображение, подожди...")
    status_url = generate_image(prompt)
    
    # Если вернулась ошибка как строка, отправим её пользователю
    if isinstance(status_url, str) and status_url.startswith("Ошибка генерации"):
        bot.send_message(message.chat.id, status_url)
        return

    for _ in range(20):
        res = requests.get(status_url, headers={"Authorization": f"Token {REPLICATE_TOKEN}"})
        if res.status_code != 200:
            bot.send_message(message.chat.id, f"Ошибка получения статуса: {res.status_code}")
            return
        status = res.json()
        if status.get("status") == "succeeded":
            image_url = status["output"][0]
            bot.send_photo(message.chat.id, image_url)
            return
        elif status.get("status") == "failed":
            bot.send_message(message.chat.id, "Генерация не удалась.")
            return
        time.sleep(2)

    bot.send_message(message.chat.id, "Не удалось сгенерировать изображение за отведённое время.")

@app.route('/', methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return '', 200

@app.route('/', methods=['GET'])
def index():
    return 'Bot is running'

if __name__ == '__main__':
    # Автоматическая установка вебхука
    bot.remove_webhook()
    bot.set_webhook(WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))