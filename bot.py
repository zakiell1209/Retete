import os
import telebot
import requests
import time
from flask import Flask, request

API_TOKEN = os.getenv("TELEGRAM_TOKEN") or "ВСТАВЬ_ТВОЙ_ТГ_ТОКЕН"
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN") or "ВСТАВЬ_ТВОЙ_REPLICATE_ТОКЕН"
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://retete.onrender.com")

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# NSFW Flux модель
REPLICATE_MODEL_VERSION = "fb4f086702d6a301ca32c170d926239324a7b7b2f0afc3d232a9c4be382dc3fa"

def generate_image(prompt):
    url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {REPLICATE_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "version": REPLICATE_MODEL_VERSION,
        "input": {
            "prompt": prompt,
            "negative_prompt": "ugly, blurry, watermark",
            "num_inference_steps": 30,
            "guidance_scale": 7
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        prediction = response.json()
        return prediction["urls"]["get"]
    else:
        print(f"❌ Ошибка генерации: {response.status_code} {response.text}")
        return None

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "👋 Привет! Напиши описание изображения, которое хочешь сгенерировать.")

@bot.message_handler(func=lambda m: True)
def handle_prompt(message):
    prompt = message.text
    bot.send_message(message.chat.id, "🎨 Генерирую изображение, подожди...")
    status_url = generate_image(prompt)

    if not status_url:
        bot.send_message(message.chat.id, "❌ Не удалось сгенерировать изображение. Проверь логи.")
        return

    for _ in range(30):
        res = requests.get(status_url, headers={"Authorization": f"Token {REPLICATE_TOKEN}"})
        if res.status_code != 200:
            print(f"Ошибка получения статуса: {res.status_code} {res.text}")
            break
        status = res.json()
        if status.get("status") == "succeeded":
            output = status.get("output")
            if output and isinstance(output, list):
                bot.send_photo(message.chat.id, output[0])
            else:
                bot.send_message(message.chat.id, "⚠️ Модель не вернула изображение.")
            return
        elif status.get("status") == "failed":
            bot.send_message(message.chat.id, "❌ Ошибка генерации изображения.")
            return
        time.sleep(2)

    bot.send_message(message.chat.id, "⏱ Не удалось сгенерировать изображение за отведённое время.")

@app.route('/', methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return '', 200

@app.route('/', methods=['GET'])
def index():
    return '✅ Бот запущен.'

if __name__ == '__main__':
    print("🚀 Бот запущен. Ожидание сообщений...")
    bot.polling(none_stop=True)