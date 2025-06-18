import os
import time
import logging
import requests
from flask import Flask, request
from telebot import TeleBot, types

# 🔐 Токены и настройки
BOT_TOKEN = os.getenv("BOT_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
REPLICATE_MODEL = "aitechtree/nsfw-novel-generation"
PORT = int(os.environ.get("PORT", 5000))

bot = TeleBot(BOT_TOKEN)
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# 📁 Категории и продвинутые теги
TAG_CATEGORIES = {
    "тело": ["большая грудь", "маленькая грудь", "чёрная кожа", "белая кожа"],
    "игрушки": ["анальные шарики", "вибратор", "дилдо", "дилдо из ануса выходит изо рта"],
    "отверстия": ["анал", "вагина", "рот"],
    "поза": ["горизонтальный шпагат", "мост", "на спине", "на боку"],
    "персонажи": ["Риас Гремори", "Акено Химедзима", "Кафка", "Фу Сюань", "Еола", "Аясе Сейко"],
    "голова": ["ахегао", "лицо в боли", "лицо в экстазе", "золотая помада"],
    "фури": ["лисица", "волчица", "кролик"],
    "сцена": ["лицом к зрителю", "спиной к зрителю", "вид снизу", "вид сверху", "вид сбоку", "ближе", "дальше"],
}

# 🔥 Продвинутые промпты
ADVANCED_PROMPTS = {
    "горизонтальный шпагат": "performing a horizontal side split on the floor, legs fully extended to both sides, hips low to the floor, arms balancing body, viewed from the front",
    "дилдо из ануса выходит изо рта": "extremely long dildo, enters through anus, visibly bulging stomach, exits through mouth, single continuous dildo, realistic texture, anatomically plausible, no x-ray view",
    "лицом к зрителю": "viewed from the front, face visible",
    "спиной к зрителю": "viewed from behind, back and buttocks visible",
    "вид снизу": "viewed from below, perspective from beneath the floor, no floor visible",
    "вид сверху": "viewed from above, top-down perspective",
    "вид сбоку": "viewed from the side, profile view",
    "ближе": "close-up view, upper body possibly cropped, high detail",
    "дальше": "distant view, full body in frame regardless of pose",
}

# ❌ Исключение нежелательной одежды
BLOCK_CLOTHING = ["panties", "bra", "bikini", "underwear", "swimsuit", "clothes covering"]

# ✅ Состояние пользователя
user_states = {}

# 📥 Обработка старта
@bot.message_handler(commands=["start"])
def start_message(message):
    chat_id = message.chat.id
    user_states[chat_id] = {"tags": []}
    bot.send_message(chat_id, "Привет! Выбери теги для генерации.", reply_markup=build_tag_menu())

# 🧩 Клавиатура тегов
def build_tag_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for category in TAG_CATEGORIES:
        keyboard.add(category)
    keyboard.add("Генерировать", "Очистить")
    return keyboard

# 🏷 Кнопки тегов
def build_tags_keyboard(category, selected_tags):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for tag in TAG_CATEGORIES[category]:
        prefix = "✅ " if tag in selected_tags else ""
        keyboard.add(prefix + tag)
    keyboard.add("Назад")
    return keyboard

# 🔁 Логика взаимодействия
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id, {"tags": []})

    if message.text == "Генерировать":
        generate_image(chat_id, state["tags"])
    elif message.text == "Очистить":
        user_states[chat_id]["tags"] = []
        bot.send_message(chat_id, "Теги очищены.")
    elif message.text == "Назад":
        bot.send_message(chat_id, "Выбери категорию:", reply_markup=build_tag_menu())
    elif message.text in TAG_CATEGORIES:
        bot.send_message(chat_id, f"Выбери теги из категории '{message.text}':", reply_markup=build_tags_keyboard(message.text, state["tags"]))
    else:
        text = message.text.replace("✅ ", "")
        if text in sum(TAG_CATEGORIES.values(), []):
            tags = user_states[chat_id]["tags"]
            if text in tags:
                tags.remove(text)
            else:
                tags.append(text)
            user_states[chat_id]["tags"] = tags
            for cat, values in TAG_CATEGORIES.items():
                if text in values:
                    bot.send_message(chat_id, f"Обновлено:", reply_markup=build_tags_keyboard(cat, tags))
                    return

# 🖼 Генерация изображения
def generate_image(chat_id, tags):
    base_prompt = []
    for tag in tags:
        prompt = ADVANCED_PROMPTS.get(tag, tag)
        base_prompt.append(prompt)

    # Убираем скрывающую одежду
    negative_prompt = ", ".join(BLOCK_CLOTHING)

    # Добавим модификаторы для персонажей + теги
    if any("Риас" in t for t in tags):
        base_prompt.append("Rias Gremory, High School DxD, detailed face, red hair, matching appearance")
    if any("Акено" in t for t in tags):
        base_prompt.append("Akeno Himejima, High School DxD, long black hair, mature face, accurate costume")

    prompt = ", ".join(base_prompt)
    payload = {
        "version": "latest",
        "input": {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": 512,
            "height": 768,
            "num_outputs": 1
        }
    }

    headers = {
        "Authorization": f"Token {REPLICATE_TOKEN}",
        "Content-Type": "application/json"
    }

    bot.send_message(chat_id, "Генерация...")

    response = requests.post(f"https://api.replicate.com/v1/predictions", json=payload, headers=headers)
    prediction = response.json()
    image_url = prediction["output"][0] if "output" in prediction else None

    if image_url:
        bot.send_photo(chat_id, image_url, caption="Вот результат!")
    else:
        bot.send_message(chat_id, "Произошла ошибка при генерации.")

# 🌐 Вебхук Flask
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    bot.process_new_updates([types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "ok", 200

@app.route("/")
def index():
    return "Бот работает", 200

if __name__ == "__main__":
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=f"{WEBHOOK_URL}/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=PORT)