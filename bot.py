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
        "version": "8625175575af3df665d665d2108a9e4e06cacf5c98295297502b52cc9c820b1c",
        "input": {"prompt": prompt}
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        prediction = response.json()
        return prediction["urls"]["get"], None
    else:
        return None, f"Ошибка генерации: {response.status_code} {response.text}"

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Напиши описание изображения для генерации.")

@bot.message_handler(func=lambda m: True)
def handle_prompt(message):
    prompt = message.text
    bot.send_message(message.chat.id, "Генерирую изображение, подожди...")
    status_url, error = generate_image(prompt)
    if error:
        bot.send_message(message.chat.id, f"❌ Ошибка при запуске генерации:\n{error}")
        return

    for i in range(20):
        res = requests.get(status_url, headers={"Authorization": f"Token {REPLICATE_TOKEN}"})
        if res.status_code != 200:
            bot.send_message(message.chat.id, f"❌ Ошибка запроса статуса ({res.status_code}):\n{res.text}")
            return

        status_data = res.json()
        current_status = status_data.get("status", "неизвестно")
        bot.send_message(message.chat.id, f"🔄 Попытка {i+1}/20\nСтатус генерации: *{current_status}*", parse_mode="Markdown")

        if current_status == "succeeded":
            output = status_data.get("output")
            if output and isinstance(output, list):
                bot.send_photo(message.chat.id, output[0])
            else:
                bot.send_message(message.chat.id, "⚠️ Ошибка: генерация завершилась, но изображение не получено.")
            return

        elif current_status == "failed":
            bot.send_message(message.chat.id, "❌ Генерация не удалась.")
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
    return 'Bot is running'

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))