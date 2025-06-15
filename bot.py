import os
import time
import requests
import telebot
from flask import Flask, request

API_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # должен быть задан заранее

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

MODEL = "wglint/2_sdv2-1"

def generate_image(prompt):
    resp = requests.post(
        "https://api.replicate.com/v1/predictions",
        headers={
            "Authorization": f"Token {REPLICATE_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL,
            "inputs": {"prompt": prompt}
        }
    )
    if resp.status_code != 201:
        return None, f"{resp.status_code} {resp.text}"
    data = resp.json()
    status_url = data["urls"]["get"]
    # Опрашиваем статус
    for _ in range(30):
        st = requests.get(status_url, headers={"Authorization": f"Token {REPLICATE_TOKEN}"})
        js = st.json()
        if js.get("status") == "succeeded":
            return js["output"][0], None
        if js.get("status") == "failed":
            return None, "generation failed"
        time.sleep(2)
    return None, "timeout"

@bot.message_handler(commands=["start"])
def cmd_start(m):
    bot.send_message(m.chat.id, "Привет! Пиши описание — я сгенерирую картинку.")

@bot.message_handler(func=lambda m: True)
def handle_all(m):
    bot.send_message(m.chat.id, "Генерирую…")
    url, err = generate_image(m.text)
    if err:
        bot.send_message(m.chat.id, f"Ошибка: {err}")
    else:
        bot.send_photo(m.chat.id, url)

@app.route("/", methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode())])
    return "", 200

@app.route("/", methods=["GET"])
def index():
    return "OK"

if __name__ == "__main__":
    # Установка вебхука
    telebot.apihelper.send(  # напрямую вызываем API setWebhook
        f"https://api.telegram.org/bot{API_TOKEN}/setWebhook?url={WEBHOOK_URL}"
    )
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))