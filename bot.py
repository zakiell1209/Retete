import os
import time
import logging
import requests
from flask import Flask, request
from telebot import TeleBot, types

# 🔐 Конфигурация
API_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 5000))

REPLICATE_MODEL = "c1d5b02687df6081c7953c74bcc527858702e8c153c9382012ccc3906752d3ec"

# 🧠 Telegram Bot
bot = TeleBot(API_TOKEN, threaded=False)
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# 📁 Состояния
user_tags = {}
user_stage = {}

# 🏷 Категории и теги
CATEGORIES = {
    "тело": ["большая грудь", "маленькая грудь", "чёрная кожа", "белая кожа", "подросток", "взрослая"],
    "игрушки": ["анальная пробка", "вибратор", "дилдо", "дилдо из ануса выходит изо рта"],
    "этнос": ["азиатка", "европейка", "фембой", "футанари"],
    "фури": ["фури-королева", "фури-кошка", "фури-собака", "фури-дракон", "фури-сильвеон", "лисица", "волчица", "кролик"],
    "персонажи": ["Риас Гремори", "Акено Химэдзима", "Кафка", "Еола", "Фу Сюань", "Аясе Сейко"],
    "голова": ["ахегао", "лицо в боли", "лицо в экстазе", "золотая помада"],
    "позы": ["горизонтальный шпагат", "вертикальный шпагат", "на боку с одной ногой вверх", "лицом к зрителю", "спиной к зрителю", "мост", "лёжа на спине с раздвинутыми ногами", "подвешенная на верёвках"],
    "сцена": ["вид сверху", "вид снизу", "вид сбоку", "ближе", "дальше"]
}

# ✅ Преобразование тега в promt-форму
def format_tags(tags):
    if not tags:
        return "nude female"
    formatted = ", ".join(tags)
    # Фильтр блокирующей одежды
    banned = ["трусы", "лифчик", "нижнее белье", "одежда, закрывающая вагину", "одежда, скрывающая анус", "одежда на груди"]
    return f"{formatted}, nude, no panties, no bra, no covering clothes, {' '.join(['- ' + b for b in banned])}"

# 📸 Генерация изображения
def generate_image(tags):
    prompt = format_tags(tags)
    payload = {
        "version": REPLICATE_MODEL,
        "input": {
            "prompt": prompt,
            "width": 512,
            "height": 768
        }
    }
    headers = {
        "Authorization": f"Token {REPLICATE_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.post("https://api.replicate.com/v1/predictions", json=payload, headers=headers)
    if response.status_code != 201:
        return None

    prediction = response.json()
    status_url = prediction["urls"]["get"]

    for _ in range(60):
        result = requests.get(status_url, headers=headers).json()
        if result["status"] == "succeeded":
            return result["output"][-1]
        elif result["status"] == "failed":
            return None
        time.sleep(2)
    return None

# 📲 Обработка команд
@bot.message_handler(commands=['start'])
def start(message):
    user_tags[message.chat.id] = set()
    bot.send_message(message.chat.id, "Привет! Выбери категорию:", reply_markup=build_category_keyboard())

# 🧩 Клавиатура категорий
def build_category_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for category in CATEGORIES:
        keyboard.add(types.KeyboardButton(category))
    return keyboard

# 🧩 Клавиатура тегов
def build_tags_keyboard(category, user_id):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for tag in CATEGORIES.get(category, []):
        label = f"✅ {tag}" if tag in user_tags.get(user_id, set()) else tag
        keyboard.add(types.KeyboardButton(label))
    keyboard.add(types.KeyboardButton("🔙 Назад"), types.KeyboardButton("✅ Сгенерировать"))
    return keyboard

# 📝 Обработка выбора
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    user_id = message.chat.id
    text = message.text.strip()

    if text == "🔙 Назад":
        bot.send_message(user_id, "Выбери категорию:", reply_markup=build_category_keyboard())
        return

    if text == "✅ Сгенерировать":
        tags = list(user_tags.get(user_id, set()))
        bot.send_message(user_id, "Генерация изображения, подожди...")
        image_url = generate_image(tags)
        if image_url:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("🔁 Начать заново", "🛠 Изменить теги", "▶ Продолжить с этими тегами")
            bot.send_photo(user_id, image_url, reply_markup=markup)
        else:
            bot.send_message(user_id, "Ошибка генерации. Попробуй ещё раз.")
        return

    if text == "🔁 Начать заново":
        user_tags[user_id] = set()
        bot.send_message(user_id, "Выбери категорию:", reply_markup=build_category_keyboard())
        return

    if text == "🛠 Изменить теги":
        bot.send_message(user_id, "Выбери категорию:", reply_markup=build_category_keyboard())
        return

    if text == "▶ Продолжить с этими тегами":
        tags = list(user_tags.get(user_id, set()))
        bot.send_message(user_id, "Повторная генерация...")
        image_url = generate_image(tags)
        if image_url:
            bot.send_photo(user_id, image_url)
        else:
            bot.send_message(user_id, "Ошибка генерации.")
        return

    if text in CATEGORIES:
        user_stage[user_id] = text
        bot.send_message(user_id, f"Выбери теги из категории «{text}»", reply_markup=build_tags_keyboard(text, user_id))
        return

    if user_id in user_stage:
        category = user_stage[user_id]
        clean_text = text.replace("✅ ", "")
        if clean_text in CATEGORIES.get(category, []):
            if clean_text in user_tags.get(user_id, set()):
                user_tags[user_id].remove(clean_text)
            else:
                user_tags[user_id].add(clean_text)
            bot.send_message(user_id, f"Категория: {category}", reply_markup=build_tags_keyboard(category, user_id))
            return

# 🌐 Вебхук
@app.route(f"/{API_TOKEN}", methods=["POST"])
def webhook():
    json_string = request.get_data().decode("utf-8")
    update = types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

# 🚀 Запуск
if __name__ == "__main__":
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=f"{WEBHOOK_URL}/{API_TOKEN}")
    app.run(host="0.0.0.0", port=PORT)