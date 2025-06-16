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

# Ключевые фразы для анализа текста
KEYWORDS = {
    "anal": ["анал", "анальный секс"],
    "dildo": ["дилдо", "большой дилдо", "огромный дилдо", "конский дилдо"],
    "positions": {
        "раком": "doggy style",
        "на корточках": "squatting",
        "вертикальный шпагат": "standing split"
    },
    "vagina": ["видно киску"],
    "breasts": {
        "большая грудь": "large breasts",
        "маленькая грудь": "small breasts"
    },
    "femboy": ["фембой"],
    "piercing": ["пирсинг"],
    "stockings": ["чулки"],
    "skin": {
        "белая кожа": "pale skin",
        "черная кожа": "dark skin"
    },
    "ethnicity": {
        "азиат": "asian",
        "европеец": "european"
    }
}

# Парсинг описания в промт
def build_prompt(user_input):
    prompt = user_input
    additions = []

    lower = user_input.lower()

    for key, values in KEYWORDS.items():
        if isinstance(values, dict):
            for k, v in values.items():
                if k in lower:
                    additions.append(v)
        else:
            for v in values:
                if v in lower:
                    additions.append(v)

    if "фембой" in lower:
        additions.append("femboy, soft feminine face, slim body, flat chest, lingerie")

    # NSFW усиления
    additions += ["NSFW", "masterpiece", "ultra detailed", "realistic lighting", "high quality", "solo"]

    full_prompt = f"{prompt}, " + ", ".join(additions)
    return full_prompt

# Генерация изображения через Replicate
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
    r = requests.post(url, headers=headers, json=data)
    if r.status_code == 201:
        return r.json()["urls"]["get"]
    return None

# Проверка статуса генерации
def wait_for_image(status_url):
    headers = {"Authorization": f"Token {REPLICATE_TOKEN}"}
    for _ in range(40):
        r = requests.get(status_url, headers=headers)
        if r.status_code != 200:
            return None
        data = r.json()
        if data["status"] == "succeeded":
            return data["output"][0]
        elif data["status"] == "failed":
            return None
        time.sleep(2)
    return None

# Генерация по сообщению
def handle_generation(message):
    prompt = build_prompt(message.text)
    bot.send_message(message.chat.id, "🔞 Генерирую изображение, подожди...")

    status_url = generate_image(prompt)
    if not status_url:
        bot.send_message(message.chat.id, "❌ Не удалось отправить запрос на генерацию.")
        return

    img_url = wait_for_image(status_url)
    if img_url:
        bot.send_photo(message.chat.id, img_url)
    else:
        bot.send_message(message.chat.id, "❌ Не удалось сгенерировать изображение.")

    show_options(message.chat.id)

# Кнопки выбора тем
def show_options(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🍑 Анал", callback_data="анал"),
        types.InlineKeyboardButton("🍆 Дилдо", callback_data="дилдо"),
        types.InlineKeyboardButton("🧑‍🎤 Фембой", callback_data="фембой"),
        types.InlineKeyboardButton("📸 Сцена секса", callback_data="секс"),
        types.InlineKeyboardButton("🧍 Позы", callback_data="позы"),
        types.InlineKeyboardButton("🧬 Цвет кожи", callback_data="цвет"),
        types.InlineKeyboardButton("🌏 Этнос", callback_data="этнос")
    )
    bot.send_message(chat_id, "📌 Выбери тематику или просто опиши, что хочешь сгенерировать:", reply_markup=markup)

@bot.message_handler(commands=["start"])
def handle_start(message):
    show_options(message.chat.id)

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    handle_generation(message)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    text = {
        "анал": "Голая девушка, анальный секс, крупный план, видно анус",
        "дилдо": "Голая девушка с дилдо в анусе, реалистично, крупный план",
        "фембой": "Фембой в чулках, видно пенис, женственная поза, эротично",
        "секс": "Девушка с дилдо в анусе, сексуальная сцена, NSFW",
        "позы": "Голая девушка вертикальный шпагат, эротичная поза",
        "цвет": "Черная кожа, голая девушка, анальная поза",
        "этнос": "Азиатка в чулках, большая грудь, анальный секс"
    }.get(call.data, "Голая девушка, NSFW")

    handle_generation(telebot.types.Message(
        message_id=call.message.message_id,
        chat=call.message.chat,
        date=call.message.date,
        content_type='text',
        message_type='text',
        json_string='',
        from_user=call.from_user,
        text=text
    ))

# Webhook endpoints
@app.route('/', methods=['GET'])
def root():
    return "🤖 Бот работает"

@app.route('/', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.data.decode("utf-8"))
    bot.process_new_updates([update])
    return '', 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))