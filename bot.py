import os
import time
import requests
import telebot
from telebot import types
from flask import Flask, request

API_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://retete.onrender.com")

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# Усилители промтов
def enhance_nsfw_female(p): return p + ", nude, erotic, sensual, solo, young female, seductive, large breasts, soft skin, masterpiece, ultra detailed, NSFW"
def enhance_futanari(p): return p + ", futanari, shemale, dickgirl, big breasts, penis, nude, erotic pose, solo, highly detailed, NSFW"
def enhance_femboy(p): return p + ", femboy, cute male, feminine face, soft skin, lingerie, erotic, slim waist, NSFW, solo"
def enhance_shibari(p): return p + ", shibari, rope bondage, tied up, detailed knots, erotic ropes, submissive pose, NSFW, cinematic"

# Генерация картинки через Replicate
def generate_image(prompt):
    url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {REPLICATE_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "version": "fb4f086702d6a301ca32c170d926239324a7b7b2f0afc3d232a9c4be382dc3fa",
        "input": {"prompt": prompt}
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        prediction = response.json()
        return prediction["urls"]["get"], None
    return None, f"❌ Ошибка генерации: {response.status_code} {response.text}"

# Отправка запроса на генерацию
def generate_custom_image(message, enhancer):
    prompt = enhancer(message.text)
    bot.send_message(message.chat.id, "🔞 Генерирую изображение, подожди...")

    status_url, error = generate_image(prompt)
    if error:
        bot.send_message(message.chat.id, error)
        return

    for _ in range(25):
        res = requests.get(status_url, headers={"Authorization": f"Token {REPLICATE_TOKEN}"})
        if res.status_code != 200:
            bot.send_message(message.chat.id, f"❌ Ошибка статуса: {res.status_code} {res.text}")
            return
        status = res.json()
        if status.get("status") == "succeeded":
            img = status["output"][0]
            bot.send_photo(message.chat.id, img)
            return
        elif status.get("status") == "failed":
            bot.send_message(message.chat.id, "❌ Генерация не удалась.")
            return
        time.sleep(2)
    bot.send_message(message.chat.id, "❌ Не удалось сгенерировать изображение за отведённое время.")

# Обработка кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    mode = call.data
    prompt_msg = {
        "nsfw_female": "📝 Опиши девушку:",
        "futanari": "📝 Опиши футанари-сцену:",
        "femboy": "📝 Опиши фембоя:",
        "shibari": "📝 Опиши сцену с шибари:"
    }.get(mode, "📝 Введите описание:")

    enhancers = {
        "nsfw_female": enhance_nsfw_female,
        "futanari": enhance_futanari,
        "femboy": enhance_femboy,
        "shibari": enhance_shibari
    }

    msg = bot.send_message(call.message.chat.id, prompt_msg)
    bot.register_next_step_handler(msg, lambda m: generate_custom_image(m, enhancers[mode]))

# Команда /start
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("🎀 NSFW для женщин", callback_data="nsfw_female"),
        types.InlineKeyboardButton("⚧️ Футанари", callback_data="futanari")
    )
    markup.row(
        types.InlineKeyboardButton("🧑‍🎤 Фембой", callback_data="femboy"),
        types.InlineKeyboardButton("🪢 Шибари", callback_data="shibari")
    )
    bot.send_message(message.chat.id, "Выбери режим генерации:", reply_markup=markup)

# Также можно писать обычный текст
@bot.message_handler(func=lambda m: True)
def handle_prompt(message):
    bot.send_message(message.chat.id, "🔁 Генерирую обычное изображение без усиления...")
    generate_custom_image(message, lambda p: p)

# Flask Webhook
@app.route('/', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.data.decode("utf-8"))
    bot.process_new_updates([update])
    return '', 200

@app.route('/', methods=['GET'])
def index():
    return '🤖 Бот работает'

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))