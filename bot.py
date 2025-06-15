import os
import time
import requests
import telebot
from flask import Flask, request

API_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://retete.onrender.com")

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# ID нужной модели Replicate (UnfilteredAI / NSFW Gen V2)
REPLICATE_MODEL_VERSION = "8625175575af3df665d665d2108a9e4e06cacf5c98295297502b52cc9c820b1c"

def generate_image(prompt):
    url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {REPLICATE_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "version": REPLICATE_MODEL_VERSION,
        "input": {"prompt": prompt}
    }
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 201:
        prediction = response.json()
        return prediction["urls"]["get"]
    else:
        print("Ошибка генерации:", response.status_code, response.text)
        return None

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "Привет! Напиши описание изображения, и я его сгенерирую.")

@bot.message_handler(func=lambda m: True)
def handle_prompt(message):
    prompt = message.text
    bot.send_message(message.chat.id, "Генерирую изображение, подожди...")

    status_url = generate_image(prompt)
    if not status_url:
        bot.send_message(message.chat.id, "❌ Ошибка при генерации. Проверь логи.")
        return

    for _ in range(20):
        res = requests.get(status_url, headers={"Authorization": f"Token {REPLICATE_TOKEN}"})
        if res.status_code != 200:
            print("Ошибка статуса:", res.status_code, res.text)
            break
        status = res.json()
        if status.get("status") == "succeeded":
            image_url = status["output"][0]
            bot.send_photo(message.chat.id, image_url)
            return
        elif status.get("status") == "failed":
            print("Ошибка модели:", status)
            break
        time.sleep(1.5)  # чуть быстрее, чем раньше

    bot.send_message(message.chat.id, "❌ Не удалось сгенерировать изображение.")

@app.route("/", methods=["POST"])
def webhook():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "", 200

@app.route("/", methods=["GET"])
def index():
    return "🤖 Бот работает!"

if __name__ == "__main__":
    # Устанавливаем вебхук вручную
    r = requests.get(
        f"https://api.telegram.org/bot{API_TOKEN}/setWebhook",
        params={"url": WEBHOOK_URL}
    )
    print("Webhook response:", r.text)

    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))