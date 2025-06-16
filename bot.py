import os
import time
import requests
from flask import Flask, request
import telebot
from telebot import types

API_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # например: https://your-app.onrender.com
PORT = int(os.environ.get("PORT", 5000))

REPLICATE_MODELS = {
    "anime": "cjwbw/eimis_anime_diffusion:a409b076",
    "realism": "stability-ai/stable-diffusion:ac732df8",
    "3d": "stability-ai/stable-diffusion-3-medium"
}

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# Переменные генерации
user_settings = {}

# ===== Усилители =====
def build_prompt(base, features):
    additions = []

    # Темы
    if 'anal' in features: additions.append("anal sex, anal penetration, anus focus")
    if 'dildo' in features: additions.append("dildo, large dildo, inserted dildo")
    if 'pose_doggy' in features: additions.append("doggy style, from behind")
    if 'pose_squat' in features: additions.append("squatting, legs open")
    if 'pose_vertical' in features: additions.append("vertical split, flexibility")
    if 'visible_pussy' in features: additions.append("pussy, open legs, visible vagina")
    if 'big_breasts' in features: additions.append("large breasts")
    if 'small_breasts' in features: additions.append("small breasts")
    if 'piercing' in features: additions.append("nipple piercing, navel piercing")
    if 'stockings' in features: additions.append("thigh high stockings, sexy lingerie")
    if 'femboy' in features:
        additions.append("femboy, cute feminine male, smooth skin, slim waist, erotic pose")
    if 'ethnicity_asian' in features: additions.append("asian girl")
    if 'ethnicity_european' in features: additions.append("european face")
    if 'skin_white' in features: additions.append("pale skin")
    if 'skin_black' in features: additions.append("dark skin")

    return base + ", " + ", ".join(additions) + ", nsfw, masterpiece, high detail"

# ===== Генерация =====
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
    return None, f"❌ Ошибка: {response.status_code} {response.text}"

def wait_for_image(url):
    for _ in range(35):
        time.sleep(2)
        res = requests.get(url, headers={"Authorization": f"Token {REPLICATE_TOKEN}"})
        if res.status_code != 200:
            return None
        data = res.json()
        if data["status"] == "succeeded":
            return data["output"][0]
        if data["status"] == "failed":
            return None
    return None

# ===== Команды =====
@bot.message_handler(commands=['start'])
def start(message):
    user_settings[message.chat.id] = {"features": [], "model": "realism"}
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("✅ Генерация", callback_data="generate"),
        types.InlineKeyboardButton("🎨 Выбрать модель", callback_data="model")
    )
    markup.add(types.InlineKeyboardButton("🧩 Выбрать теги", callback_data="tags"))
    bot.send_message(message.chat.id, "Привет! Выбери действия:", reply_markup=markup)

# ===== Выбор модели =====
def model_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🖌 Аниме", callback_data="model_anime"))
    markup.add(types.InlineKeyboardButton("📷 Реализм", callback_data="model_realism"))
    markup.add(types.InlineKeyboardButton("🧱 3D", callback_data="model_3d"))
    return markup

# ===== Выбор тегов =====
def tag_keyboard():
    tags = [
        ("🍑 Анал", "anal"), ("🍆 Дилдо", "dildo"),
        ("🤸‍♀️ Раком", "pose_doggy"), ("🧘‍♀️ Шпагат", "pose_vertical"),
        ("🧍‍♀️ На корточках", "pose_squat"), ("👀 Видно киску", "visible_pussy"),
        ("🔺 Большая грудь", "big_breasts"), ("🔻 Маленькая грудь", "small_breasts"),
        ("💎 Пирсинг", "piercing"), ("🧦 Чулки", "stockings"),
        ("👦‍ Фембой", "femboy"), ("🧑‍🦱 Азиатка", "ethnicity_asian"),
        ("👩‍🦰 Европейка", "ethnicity_european"), ("⚪ Белая кожа", "skin_white"),
        ("⚫ Чёрная кожа", "skin_black")
    ]
    markup = types.InlineKeyboardMarkup(row_width=2)
    for name, tag in tags:
        markup.add(types.InlineKeyboardButton(name, callback_data=f"tag_{tag}"))
    markup.add(types.InlineKeyboardButton("✅ Готово", callback_data="tags_done"))
    return markup

# ===== Callback =====
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    cid = call.message.chat.id
    data = call.data

    if cid not in user_settings:
        user_settings[cid] = {"features": [], "model": "realism"}

    if data == "generate":
        bot.send_message(cid, "📝 Напиши описание:")
        bot.register_next_step_handler_by_chat_id(cid, handle_prompt)

    elif data.startswith("model_"):
        model = data.split("_")[1]
        user_settings[cid]["model"] = model
        bot.send_message(cid, f"🎨 Модель установлена: {model.upper()}")

    elif data == "model":
        bot.send_message(cid, "Выбери модель:", reply_markup=model_keyboard())

    elif data == "tags":
        user_settings[cid]["features"] = []
        bot.send_message(cid, "Выбери теги:", reply_markup=tag_keyboard())

    elif data.startswith("tag_"):
        tag = data.split("_")[1]
        if tag in user_settings[cid]["features"]:
            user_settings[cid]["features"].remove(tag)
        else:
            user_settings[cid]["features"].append(tag)

    elif data == "tags_done":
        bot.send_message(cid, f"Выбрано: {', '.join(user_settings[cid]['features'])}")

# ===== Описание =====
def handle_prompt(message):
    cid = message.chat.id
    base_prompt = message.text
    features = user_settings[cid].get("features", [])
    model_id = user_settings[cid].get("model", "realism")
    model_version = REPLICATE_MODELS.get(model_id, REPLICATE_MODELS["realism"])

    prompt = build_prompt(base_prompt, features)
    bot.send_message(cid, f"🎨 Модель: {model_id}\n📸 Генерация...")

    status_url, error = generate_image(prompt, model_version)
    if error:
        bot.send_message(cid, error)
        return

    image_url = wait_for_image(status_url)
    if image_url:
        bot.send_photo(cid, image_url)
    else:
        bot.send_message(cid, "❌ Ошибка генерации изображения.")

# ===== Flask Webhook =====
@app.route('/', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.data.decode("utf-8"))
    bot.process_new_updates([update])
    return '', 200

@app.route('/', methods=['GET'])
def index():
    return "🤖 Бот работает."

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(WEBHOOK_URL)
    app.run(host="0.0.0.0", port=PORT)