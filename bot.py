import os
import replicate
import telebot
import requests
from flask import Flask, request

TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")
REPLICATE_MODEL = "aitechtree/nsfw-novel-generation:9a2d249fbf4e8e22faaf9a7b430fd8ba69a6875e470066a3ecdbb39dd0221b38"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # пример: https://название-проекта.onrender.com

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
replicate_client = replicate.Client(api_token=REPLICATE_TOKEN)

# Категории тегов и русские названия (сокращённые)
TAGS = {
    "поза": ["Шпагат ✅", "Мостик", "На боку", "Сбоку"],
    "отверстия": ["Анал ✅", "Рот", "Влагалище"],
    "игрушки": ["Дилдо", "Анальные бусы"],
    "тело": ["Белая кожа", "Чёрная кожа", "Маленькая грудь", "Пышная"],
    "этнос": ["Европейка", "Азиатка", "Фембой"],
    "фури": ["Фури-кошка", "Фури-сильвеон", "Фури-дракон"]
}

# Временное хранилище
user_data = {}

# Главная команда
@bot.message_handler(commands=["start"])
def handle_start(message):
    user_data[message.chat.id] = {"tags": [], "page": 0}
    bot.send_message(message.chat.id, "Привет! Выбери категории тегов для генерации.", reply_markup=category_keyboard())

# Клавиатура категорий
def category_keyboard():
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for cat in TAGS:
        keyboard.add(cat.capitalize())
    keyboard.add("Готово", "Редактировать теги")
    return keyboard

# Клавиатура тегов с пагинацией
def tag_keyboard(category, selected, page=0, per_page=6):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    tags = TAGS[category]
    total_pages = (len(tags) - 1) // per_page + 1
    start = page * per_page
    end = start + per_page
    for tag in tags[start:end]:
        label = f"✅ {tag}" if tag in selected else tag
        markup.add(label)
    buttons = []
    if page > 0:
        buttons.append("⬅️ Назад")
    if end < len(tags):
        buttons.append("➡️ Далее")
    markup.add(*buttons)
    markup.add("🔙 В меню")
    return markup

# Обработка сообщений
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    chat_id = message.chat.id
    text = message.text

    if chat_id not in user_data:
        user_data[chat_id] = {"tags": [], "page": 0}

    data = user_data[chat_id]
    if text == "Готово":
        generate_image(chat_id)
    elif text == "Редактировать теги":
        bot.send_message(chat_id, "Выбранные теги:\n" + ", ".join(data["tags"]))
    elif text in TAGS:
        data["category"] = text
        data["page"] = 0
        bot.send_message(chat_id, f"Выбери теги: {text}", reply_markup=tag_keyboard(text, data["tags"], 0))
    elif text == "➡️ Далее":
        data["page"] += 1
        bot.send_message(chat_id, "Далее:", reply_markup=tag_keyboard(data["category"], data["tags"], data["page"]))
    elif text == "⬅️ Назад":
        data["page"] -= 1
        bot.send_message(chat_id, "Назад:", reply_markup=tag_keyboard(data["category"], data["tags"], data["page"]))
    elif text == "🔙 В меню":
        bot.send_message(chat_id, "Выбери категорию:", reply_markup=category_keyboard())
    else:
        category = data.get("category")
        if category and text.replace("✅ ", "") in TAGS[category]:
            tag = text.replace("✅ ", "")
            if tag in data["tags"]:
                data["tags"].remove(tag)
            else:
                data["tags"].append(tag)
            bot.send_message(chat_id, f"Тег обновлён: {tag}", reply_markup=tag_keyboard(category, data["tags"], data["page"]))

# Генерация изображения
def generate_image(chat_id):
    tags = user_data[chat_id]["tags"]
    prompt = ", ".join(tags) + ", nsfw, detailed, anime style"
    msg = bot.send_message(chat_id, "Генерирую изображение, подожди...")

    try:
        output = replicate_client.run(
            REPLICATE_MODEL,
            input={"prompt": prompt, "width": 512, "height": 768, "guidance_scale": 7.5, "num_inference_steps": 30}
        )
        bot.send_photo(chat_id, output[0], caption="Сгенерировано!")
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка при генерации: {e}")
    finally:
        bot.send_message(chat_id, "Выбери следующий шаг:", reply_markup=category_keyboard())

# Flask endpoints
@app.route("/")
def index():
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
    return "Webhook установлен!", 200

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "", 200

# Запуск
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))