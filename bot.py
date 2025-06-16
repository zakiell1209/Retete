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

# Версия модели для аниме-стиля
REPLICATE_MODEL_VERSION = "c1d5b02687df6081c7953c74bcc527858702e8c153c9382012ccc3906752d3ec"

# Усилители промтов
def enhance_nsfw_female(p):
    return p + ", nude, erotic, sensual, solo, young female, seductive, large breasts, soft skin, masterpiece, ultra detailed, NSFW, anime style"

def enhance_futanari(p):
    return p + ", futanari, shemale, dickgirl, big breasts, penis, nude, erotic pose, solo, highly detailed, NSFW, anime style"

def enhance_femboy(p):
    return p + ", femboy, cute male, feminine face, soft skin, lingerie, erotic, slim waist, NSFW, solo, anime style"

def enhance_shibari(p):
    return p + ", shibari, rope bondage, tied up, detailed knots, erotic ropes, submissive pose, NSFW, cinematic, anime style"

# Добавление синонимов и распознавание ключевых слов (анал, дилдо, поза и т.д.)
def build_prompt(text):
    prompt = text.lower()
    additions = []

    # Анал и синонимы
    if any(x in prompt for x in ["анал", "анальный", "anal"]):
        additions.append("anal sex, detailed anal penetration")

    # Дилдо с вариациями
    if any(x in prompt for x in ["дилдо", "большой дилдо", "конский дилдо", "dildo", "big dildo", "horse dildo"]):
        additions.append("large dildo, realistic dildo, inserted dildo")

    # Позиции
    if any(x in prompt for x in ["раком", "на корточках", "спина", "поза", "позиция", "squatting", "doggy style", "on back"]):
        additions.append("specific pose")

    # Видно киску / влагалище
    if any(x in prompt for x in ["киска", "влагалище", "pussy", "vagina"]):
        additions.append("visible vagina, detailed vulva")

    # Размер груди
    if any(x in prompt for x in ["большая грудь", "огромная грудь", "large breasts", "big boobs"]):
        additions.append("large breasts, full chest")

    # Пирсинг
    if any(x in prompt for x in ["пирсинг", "piercing", "nipple piercing", "pierced nipples"]):
        additions.append("nipple piercing")

    # Чулки
    if any(x in prompt for x in ["чулки", "stockings", "hosiery"]):
        additions.append("lace stockings, thigh-high stockings")

    # Объединяем
    additions_text = ", ".join(additions)
    if additions_text:
        prompt += ", " + additions_text

    # Уточним стиль аниме
    prompt += ", anime style, detailed, high quality, NSFW"
    return prompt

# Генерация картинки через Replicate
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
        return prediction["urls"]["get"], None
    return None, f"❌ Ошибка генерации: {response.status_code} {response.text}"

# Отправка запроса на генерацию с повторной проверкой статуса
def generate_custom_image(message, enhancer):
    prompt = enhancer(message.text)
    bot.send_message(message.chat.id, "🔞 Генерирую изображение, подожди...")

    status_url, error = generate_image(prompt)
    if error:
        bot.send_message(message.chat.id, error)
        return

    for _ in range(30):  # Увеличено время ожидания
        res = requests.get(status_url, headers={"Authorization": f"Token {REPLICATE_TOKEN}"})
        if res.status_code != 200:
            bot.send_message(message.chat.id, f"❌ Ошибка статуса: {res.status_code} {res.text}")
            return
        status = res.json()
        if status.get("status") == "succeeded":
            img = status["output"][0]
            bot.send_photo(message.chat.id, img)
            # После генерации предлагаем усиление
            send_enhancement_options(message.chat.id)
            return
        elif status.get("status") == "failed":
            bot.send_message(message.chat.id, "❌ Генерация не удалась.")
            return
        time.sleep(2)
    bot.send_message(message.chat.id, "❌ Не удалось сгенерировать изображение за отведённое время.")

# Отправка выбора усиления
def send_enhancement_options(chat_id):
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("🎀 Усиление девушек", callback_data="nsfw_female"),
        types.InlineKeyboardButton("⚧️ Футанари", callback_data="futanari")
    )
    markup.row(
        types.InlineKeyboardButton("🧑‍🎤 Фембой", callback_data="femboy"),
        types.InlineKeyboardButton("🪢 Шибари", callback_data="shibari")
    )
    bot.send_message(chat_id, "Выбери усиление для следующей генерации:", reply_markup=markup)

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
    send_enhancement_options(message.chat.id)

# Обычный текст - без усиления
@bot.message_handler(func=lambda m: True)
def handle_prompt(message):
    prompt = build_prompt(message.text)
    bot.send_message(message.chat.id, "🔁 Генерирую изображение с учётом ключевых слов...")
    generate_custom_image(message, lambda _: prompt)

# Flask Webhook
app = Flask(__name__)

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