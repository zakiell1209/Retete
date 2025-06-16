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

# Функция для расширения промта с синонимами и ключевыми словами
def expand_prompt_synonyms(text):
    text = text.lower()
    additions = []

    # Анал
    anal_synonyms = ["анал", "анус", "анальный"]
    if any(word in text for word in anal_synonyms):
        additions.append("anal, anal sex, detailed anus, erotic")

    # Дилдо
    dildo_synonyms = ["дилдо", "большой дилдо", "конский дилдо", "огромный дилдо", "гигантский дилдо"]
    if any(word in text for word in dildo_synonyms):
        additions.append("large dildo, realistic dildo, dildo penetration, detailed dildo")

    # Поза
    pose_synonyms = {
        "раком": "doggy style, rear view",
        "вертикальный шпагат": "vertical splits, flexible pose",
        "на корточках": "crouching pose, bent knees",
        "миссионерская": "missionary position",
        "69": "69 position"
    }
    for key, phrase in pose_synonyms.items():
        if key in text:
            additions.append(phrase)

    # Видно киску
    pussy_synonyms = ["видно киску", "киска видна", "обнажённая киска", "видна вагина"]
    if any(word in text for word in pussy_synonyms):
        additions.append("exposed pussy, pussy visible, detailed vulva")

    # Изменения размера груди
    breast_synonyms = {
        "большая грудь": "large breasts, big boobs, voluptuous",
        "маленькая грудь": "small breasts, petite boobs",
        "огромная грудь": "huge breasts, massive boobs",
        "средняя грудь": "medium breasts"
    }
    for key, phrase in breast_synonyms.items():
        if key in text:
            additions.append(phrase)

    # Пирсинг
    piercing_synonyms = ["пирсинг", "пирсинг на груди", "пирсинг на сосках", "пирсинг на пупке"]
    if any(word in text for word in piercing_synonyms):
        additions.append("piercing, nipple piercing, belly button piercing")

    # Чулки
    stockings_synonyms = ["чулки", "с чулками", "сетчатые чулки", "кружевные чулки"]
    if any(word in text for word in stockings_synonyms):
        additions.append("stockings, lace stockings, fishnet stockings")

    return ", ".join(additions)

# Усилители промтов
def enhance_prompt(base_prompt, mode):
    base_prompt = base_prompt.strip()
    base_prompt = base_prompt.capitalize()

    enhancers = {
        "nsfw_female": "nude, erotic, sensual, solo, young female, seductive, large breasts, soft skin, masterpiece, ultra detailed, NSFW",
        "futanari": "futanari, shemale, dickgirl, big breasts, penis, nude, erotic pose, solo, highly detailed, NSFW",
        "femboy": "femboy, cute male, feminine face, soft skin, lingerie, erotic, slim waist, NSFW, solo",
        "shibari": "shibari, rope bondage, tied up, detailed knots, erotic ropes, submissive pose, NSFW, cinematic",
        "default": ""
    }

    enhancer = enhancers.get(mode, enhancers["default"])
    extra = expand_prompt_synonyms(base_prompt)
    prompt = f"{base_prompt}"
    if enhancer:
        prompt += f", {enhancer}"
    if extra:
        prompt += f", {extra}"
    prompt += ", masterpiece, high quality, 4k, detailed, realistic"
    return prompt

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
def generate_custom_image(message, mode):
    prompt = enhance_prompt(message.text, mode)
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

    msg = bot.send_message(call.message.chat.id, prompt_msg)
    bot.register_next_step_handler(msg, lambda m: generate_custom_image(m, mode))

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

# Если пишут просто текст без выбора режима, сгенерируем без усиления (default)
@bot.message_handler(func=lambda m: True)
def handle_prompt(message):
    bot.send_message(message.chat.id, "🔁 Генерирую обычное изображение без усиления...")
    generate_custom_image(message, "default")

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