import os
import json
import requests
import replicate
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ======= Конфигурация =======
BOT_TOKEN = os.environ.get("BOT_TOKEN")
REPLICATE_TOKEN = os.environ.get("REPLICATE_API_TOKEN")
REPLICATE_MODEL = "aitechtree/nsfw-novel-generation"
REPLICATE_VERSION = "ccfc5f04e08e574d5ed07f91f46ff5f5368b8037d9b03cb0ff8ed0c684859d5e"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
headers = {"Authorization": f"Token {REPLICATE_TOKEN}"}

# ======= Теги =======
TAGS = {
    "тело": {
        "лоли": "loli",
        "милфа": "milf",
        "худое": "skinny body",
        "пышное": "plump body",
        "нормальное": "average body",
        "накачаное": "muscular body",
        "возраст 21": "21 years old"
    },
    "игрушки": {
        "анальные бусы": "anal beads",
        "дилдо": "dildo",
        "пирсинг": "nipple piercing"
    },
    "этнос": {
        "азиатка": "asian girl",
        "европейка": "european girl",
        "фембой": "femboy",
        "футанари": "futanari"
    },
    "фури": {
        "кошка": "furry cat girl",
        "дракон": "furry dragon girl",
        "сильвеон": "furry silveon girl, pink white, ribbons, sylveon",
        "собака": "furry dog girl"
    },
    "одежда": {
        "без белья": "no underwear",
        "костюм коровы": "cow print thighhighs, cow horns, cow tail, no panties",
        "загар от бикини": "dark tan skin with bikini tan lines"
    },
    "позиции": {
        "лежа": "lying pose",
        "мост": "bridge pose",
        "шпагат горизонт": "horizontal split",
        "шпагат вертикаль": "vertical split",
        "на боку": "on side, one leg up",
        "спереди": "facing viewer",
        "сзади": "from behind",
        "на спине": "on back, legs apart, knees up",
        "подвешена": "suspended with ropes"
    }
}

# Состояние пользователя
user_tags = {}

# ======= Кнопки =======
def build_tag_keyboard(user_id, category):
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = []
    selected = user_tags.get(user_id, {}).get(category, [])

    for label, prompt in TAGS[category].items():
        check = "✅" if prompt in selected else ""
        buttons.append(InlineKeyboardButton(f"{check} {label}", callback_data=f"tag|{category}|{prompt}"))

    buttons.append(InlineKeyboardButton("✅ Готово", callback_data=f"done|{category}"))
    keyboard.add(*buttons)
    return keyboard

# ======= Генерация =======
def generate_image(prompt):
    url = f"https://api.replicate.com/v1/predictions"
    data = {
        "version": REPLICATE_VERSION,
        "input": {
            "prompt": prompt,
            "width": 512,
            "height": 768,
            "guidance_scale": 7
        }
    }
    response = requests.post(url, headers=headers, json=data)
    prediction = response.json()
    return prediction["urls"]["get"]

# ======= Telegram =======
@bot.message_handler(commands=["start"])
def handle_start(message):
    user_tags[message.chat.id] = {}
    keyboard = InlineKeyboardMarkup(row_width=2)
    for category in TAGS:
        keyboard.add(InlineKeyboardButton(category.capitalize(), callback_data=f"cat|{category}"))
    bot.send_message(message.chat.id, "Выбери категорию тегов:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.message.chat.id
    data = call.data.split("|")

    if data[0] == "cat":
        category = data[1]
        bot.edit_message_text(f"Категория: {category}", chat_id=user_id, message_id=call.message.message_id,
                              reply_markup=build_tag_keyboard(user_id, category))

    elif data[0] == "tag":
        _, category, prompt = data
        selected = user_tags.setdefault(user_id, {}).setdefault(category, [])
        if prompt in selected:
            selected.remove(prompt)
        else:
            selected.append(prompt)
        bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.message_id,
                                      reply_markup=build_tag_keyboard(user_id, category))

    elif data[0] == "done":
        all_prompts = []
        for prompts in user_tags.get(user_id, {}).values():
            all_prompts.extend(prompts)
        if not all_prompts:
            bot.answer_callback_query(call.id, "Выберите хотя бы один тег.")
            return
        prompt = ", ".join(all_prompts)
        bot.send_message(user_id, "Генерирую изображение...")
        try:
            url = generate_image(prompt)
            bot.send_message(user_id, "Изображение будет доступно по ссылке (обновляется автоматически):\n" + url)
        except Exception as e:
            bot.send_message(user_id, f"Ошибка при генерации: {e}")

# ======= Flask webhook =======
@app.route('/', methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "ok", 200

@app.route('/', methods=["GET"])
def index():
    return "Бот работает!", 200

# ======= Запуск =======
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))