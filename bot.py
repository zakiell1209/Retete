import os
import time
import requests
import telebot
from telebot import types
from flask import Flask, request

API_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

user_settings = {}

REPLICATE_MODELS = {
    "anime": "fb4f086702d6a301ca32c170d926239324a7b7b2f0afc3d232a9c4be382dc3fa",
    "realism": "f219c7eb13e17887e1acb1be8b12e841be3db640c82fb956c0f5d52c4cc9b6ec",
    "3d": "b8b4012675e6e84bd38bb3770e5faaf6cb943030a14e435f1ec61d116d30b370"
}

PRESETS = {
    "anal": "anal sex, anus penetration, ass visible",
    "dildo": "huge dildo, inserted, sex toy",
    "pose_doggy": "doggy style pose, from behind",
    "pose_squat": "squatting pose, open legs",
    "pose_splits": "vertical splits pose, flexible",
    "pussy_visible": "pussy visible, spread legs",
    "small_boobs": "small breasts",
    "big_boobs": "large breasts",
    "piercing": "body piercing, nipple piercing",
    "stockings": "wearing stockings",
    "sex_scene": "realistic sex scene, penetration, cum",
    "femboy": "femboy, feminine male, slim waist, soft skin, long hair, flat chest, NSFW",
    "black_skin": "black skin",
    "white_skin": "pale white skin",
    "asian": "asian female",
    "european": "european face"
}

def generate_prompt(user_id, user_input):
    tags = user_settings.get(user_id, {}).get("tags", set())
    model = user_settings.get(user_id, {}).get("model", "realism")
    prompt = user_input + ", " + ", ".join(PRESETS[t] for t in tags if t in PRESETS)
    return prompt.strip(), REPLICATE_MODELS[model]

def generate_image(prompt, model_version):
    url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {REPLICATE_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "version": model_version,
        "input": {"prompt": prompt}
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        return response.json()["urls"]["get"], None
    return None, f"❌ Ошибка генерации: {response.status_code} {response.text}"

def poll_image(message, status_url):
    for _ in range(40):
        res = requests.get(status_url, headers={"Authorization": f"Token {REPLICATE_TOKEN}"})
        if res.status_code != 200:
            bot.send_message(message.chat.id, f"❌ Статус ошибка: {res.status_code}")
            return
        status = res.json()
        if status.get("status") == "succeeded":
            bot.send_photo(message.chat.id, status["output"][0])
            return
        elif status.get("status") == "failed":
            bot.send_message(message.chat.id, "❌ Генерация провалилась.")
            return
        time.sleep(2)
    bot.send_message(message.chat.id, "❌ Время ожидания истекло.")

@bot.message_handler(commands=['start'])
def start(message):
    user_settings[message.chat.id] = {"tags": set(), "model": "realism"}
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("Анал", callback_data="anal"),
        types.InlineKeyboardButton("Дилдо", callback_data="dildo"),
        types.InlineKeyboardButton("Фембой", callback_data="femboy")
    )
    markup.add(
        types.InlineKeyboardButton("Раком", callback_data="pose_doggy"),
        types.InlineKeyboardButton("Шпагат", callback_data="pose_splits"),
        types.InlineKeyboardButton("На корточках", callback_data="pose_squat")
    )
    markup.add(
        types.InlineKeyboardButton("Большая грудь", callback_data="big_boobs"),
        types.InlineKeyboardButton("Маленькая грудь", callback_data="small_boobs"),
        types.InlineKeyboardButton("Киска видна", callback_data="pussy_visible")
    )
    markup.add(
        types.InlineKeyboardButton("Пирсинг", callback_data="piercing"),
        types.InlineKeyboardButton("Чулки", callback_data="stockings"),
        types.InlineKeyboardButton("Сцена секса", callback_data="sex_scene")
    )
    markup.add(
        types.InlineKeyboardButton("Чёрная кожа", callback_data="black_skin"),
        types.InlineKeyboardButton("Белая кожа", callback_data="white_skin")
    )
    markup.add(
        types.InlineKeyboardButton("Азиатка", callback_data="asian"),
        types.InlineKeyboardButton("Европейка", callback_data="european")
    )
    markup.add(
        types.InlineKeyboardButton("Модель: Аниме", callback_data="model_anime"),
        types.InlineKeyboardButton("Модель: Реализм", callback_data="model_realism"),
        types.InlineKeyboardButton("Модель: 3D", callback_data="model_3d")
    )
    bot.send_message(message.chat.id, "Выберите параметры генерации:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    uid = call.message.chat.id
    data = call.data

    if data.startswith("model_"):
        model = data.split("_")[1]
        user_settings.setdefault(uid, {}).update({"model": model})
        bot.answer_callback_query(call.id, f"✅ Модель установлена: {model}")
        return

    tags = user_settings.setdefault(uid, {}).setdefault("tags", set())
    if data in tags:
        tags.remove(data)
        bot.answer_callback_query(call.id, f"❌ Убрано: {data}")
    else:
        tags.add(data)
        bot.answer_callback_query(call.id, f"✅ Добавлено: {data}")

@bot.message_handler(func=lambda m: True)
def handle_prompt(message):
    prompt, version = generate_prompt(message.chat.id, message.text)
    bot.send_message(message.chat.id, "🎨 Генерация...")

    status_url, error = generate_image(prompt, version)
    if error:
        bot.send_message(message.chat.id, error)
        return
    poll_image(message, status_url)

@app.route('/', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.data.decode("utf-8"))
    bot.process_new_updates([update])
    return '', 200

@app.route('/', methods=['GET'])
def root():
    return "🤖 Бот активен."

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))