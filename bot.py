import os
import time
import re
import requests
import telebot
from telebot import types
from flask import Flask, request

API_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://retete.onrender.com")

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# Усилители промтов (в конце каждого генерации будем предлагать выбор)
def enhance_nsfw_female(p):
    return p + ", nude, erotic, sensual, solo, young female, seductive, large breasts, soft skin, masterpiece, ultra detailed, NSFW"

def enhance_futanari(p):
    return p + ", futanari, shemale, dickgirl, big breasts, penis, nude, erotic pose, solo, highly detailed, NSFW"

def enhance_femboy(p):
    return p + ", femboy, cute male, feminine face, soft skin, lingerie, erotic, slim waist, NSFW, solo"

def enhance_shibari(p):
    return p + ", shibari, rope bondage, tied up, detailed knots, erotic ropes, submissive pose, NSFW, cinematic"

enhancers_map = {
    "nsfw_female": enhance_nsfw_female,
    "futanari": enhance_futanari,
    "femboy": enhance_femboy,
    "shibari": enhance_shibari
}

# Расширение промта с синонимами и ключами
def expand_prompt_synonyms(text):
    text = text.lower()
    additions = []

    def contains(words):
        for w in words:
            # Ищем точное слово, игнорируем регистр
            pattern = r'\b' + re.escape(w) + r'\b'
            if re.search(pattern, text):
                return True
        return False

    # Анал и все синонимы
    if contains(["анальный секс", "анал", "анус", "анальный", "анальная фистинг", "анальная стимуляция", "задница"]):
        additions.append(
            "anal penetration, detailed anus, erotic anal play, butt, rimjob, erotic buttocks, backdoor play, rear entry, explicit anal, uncensored"
        )

    # Дилдо с синонимами
    if contains(["дилдо", "большой дилдо", "конский дилдо", "огромный дилдо", "гигантский дилдо", "фаллоимитатор", "фаллический"]):
        additions.append(
            "large realistic dildo, dildo penetration, rubber dildo, phallic object, detailed dildo, sex toy, dildo insertion, penetrating dildo, explicit toy, uncensored"
        )

    # Поза
    if contains(["раком", "вертикальный шпагат", "на корточках", "поза раком", "спиной", "стоя", "сидя", "лежа", "горизонтальный шпагат", "сидя на корточках"]):
        additions.append(
            "detailed pose, erotic posture, specific pose, sexy pose, dynamic pose, body position"
        )

    # Видно киску и синонимы
    if contains(["видно киску", "видна киска", "показана киска", "открытая киска", "влагалище видно", "вагина", "вагина видна"]):
        additions.append(
            "visible pussy, open vagina, detailed vulva, exposed pussy, pussy lips, erotic genitalia"
        )

    # Размер груди и варианты
    if contains(["большая грудь", "огромная грудь", "маленькая грудь", "маленькие сиськи", "средняя грудь", "крупные сиськи", "пышная грудь"]):
        additions.append(
            "breasts size variation, large breasts, small breasts, realistic breasts, detailed cleavage"
        )

    # Пирсинг
    if contains(["пирсинг", "пирсинг на пизде", "пирсинг на сосках", "пирсинг на вагине"]):
        additions.append(
            "body piercing, nipple piercing, genital piercing, erotic piercing, detailed piercings"
        )

    # Чулки и синонимы
    if contains(["чулки", "сетчатые чулки", "кружевные чулки", "чулки до бедра", "чулки на ногах"]):
        additions.append(
            "stockings, lace stockings, fishnet stockings, thigh high stockings, detailed stockings"
        )

    # Если не добавлено — всегда добавим NSFW чтобы усилить
    additions.append("nsfw, explicit, uncensored, highly detailed, masterpiece")

    return ", ".join(additions)

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

# Основная функция генерации с учётом расширения
def generate_custom_image(message, enhancer):
    base_prompt = message.text.strip()
    expansions = expand_prompt_synonyms(base_prompt)
    final_prompt = base_prompt
    if expansions:
        final_prompt += ", " + expansions
    final_prompt = enhancer(final_prompt)

    bot.send_message(message.chat.id, "🔞 Генерирую изображение, подожди...")

    status_url, error = generate_image(final_prompt)
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
            send_enhancement_buttons(message.chat.id)
            return
        elif status.get("status") == "failed":
            bot.send_message(message.chat.id, "❌ Генерация не удалась.")
            return
        time.sleep(2)
    bot.send_message(message.chat.id, "❌ Не удалось сгенерировать изображение за отведённое время.")

# Кнопки выбора усиления после генерации
def send_enhancement_buttons(chat_id):
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("🎀 NSFW для женщин", callback_data="nsfw_female"),
        types.InlineKeyboardButton("⚧️ Футанари", callback_data="futanari")
    )
    markup.row(
        types.InlineKeyboardButton("🧑‍🎤 Фембой", callback_data="femboy"),
        types.InlineKeyboardButton("🪢 Шибари", callback_data="shibari")
    )
    bot.send_message(chat_id, "Выбери режим усиления для следующей генерации:", reply_markup=markup)

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

    enhancer = enhancers_map.get(mode, lambda p: p)

    msg = bot.send_message(call.message.chat.id, prompt_msg)
    bot.register_next_step_handler(msg, lambda m: generate_custom_image(m, enhancer))

# Команда /start
@bot.message_handler(commands=['start'])
def start(message):
    send_enhancement_buttons(message.chat.id)

# Обработка обычного текста
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