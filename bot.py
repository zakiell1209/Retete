import os
import telebot
import requests
import time
from flask import Flask, request

API_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Например, "https://retete.onrender.com/"

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

def generate_image(prompt):
    url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {REPLICATE_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "version": "fbdfeac868992494485981db247b476148f2619a9ca1a72f4d87e3a58c4d0039",  # nsfw-novel-generation
        "input": {
            "prompt": prompt,
            "negative_prompt": "blurry, cartoon, low quality"
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        prediction = response.json()
        return prediction["urls"]["get"]
    else:
        print(f"Ошибка генерации: {response.status_code} {response.text}")
        return None

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Напиши описание NSFW-изображения для генерации.")

@bot.message_handler(func=lambda m: True)
def handle_prompt(message):
    prompt = message.text
    bot.send_message(message.chat.id, "Генерирую изображение, подожди...")

    status_url = generate_image(prompt)
    if not status_url:
        bot.send_message(message.chat.id, "Ошибка при генерации. Проверь логи.")
        return

    for _ in range(25):  # максимум 50 секунд ожидания (25 * 2 сек)
        res = requests.get(status_url, headers={"Authorization": f"Token {REPLICATE_TOKEN}"})
        if res.status_code != 200:
            print(f"Ошибка получения статуса: {res.status_code} {res.text}")
            break
        status = res.json()
        if status.get("status") == "succeeded":
            image_url = status["output"][0]
            bot.send_photo(message.chat.id, image_url)
            return
        elif status.get("status") == "failed":
            break
        time.sleep(2)

    bot.send_message(message.chat.id, "Не удалось сгенерировать изображение.")

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
    bot.remove_webhook()
    if WEBHOOK_URL:
        bot.set_webhook(WEBHOOK_URL)
        print(f"Webhook установлен: {WEBHOOK_URL}")
    else:
        print("WEBHOOK_URL не задан, вебхук не установлен.")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))