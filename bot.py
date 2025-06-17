import os
import json
import logging
import requests
from flask import Flask, request
from telebot import TeleBot, types

# 🔐 Токены
BOT_TOKEN = os.getenv("BOT_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_TOKEN")
REPLICATE_MODEL = "aitechtree/nsfw-novel-generation"

bot = TeleBot(BOT_TOKEN)
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# 📁 Состояние и категории
user_states = {}
categories = {
    "позы": ["вертикальный шпагат", "горизонтальный шпагат", "мост", "подвешенная"],
    "игрушки": ["дилдо", "анальные бусы", "раскрытие ануса"],
    "тело": ["лоли", "милфа", "худое", "пышное", "нормальное"],
    "этнос": ["азиатка", "европейка", "фембой", "футанари"],
    "кожа": ["чёрная кожа", "белая кожа", "загар от бикини"],
    "фури": ["фури-кошка", "фури-собака", "фури-сильвеон"],
    "особое": ["тату сукуба", "костюм коровы"]
}
tag_prompts = {
    "дилдо": "dildo in anus, visible through mouth",
    "тату сукуба": "heart tattoo on womb area, no wings, no horns, no tail",
    "загар от бикини": "dark tan lines on skin without bikini",
    "костюм коровы": "girl in cow-patterned stockings with horns and tail, no bull, no actual cow",
    "фури-сильвеон": "anthro sylveon style girl, pastel colors, detailed"
}

# 🧠 Сбор пользовательских тегов
def get_user_tags(user_id):
    return user_states.setdefault(user_id, {"tags": [], "category": None})["tags"]

# ✅ Обработка /start
@bot.message_handler(commands=["start"])
def start_handler(message):
    user_states[message.chat.id] = {"tags": [], "category": None}
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🧩 Выбрать теги", "🎨 Сгенерировать")
    bot.send_message(message.chat.id, "Добро пожаловать! Выберите действие:", reply_markup=markup)

# 🧩 Обработка кнопки выбора тегов
@bot.message_handler(func=lambda msg: msg.text == "🧩 Выбрать теги")
def choose_category_handler(message):
    markup = types.InlineKeyboardMarkup()
    for category in categories.keys():
        markup.add(types.InlineKeyboardButton(category, callback_data=f"cat:{category}"))
    bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=markup)

# 🎨 Генерация
@bot.message_handler(func=lambda msg: msg.text == "🎨 Сгенерировать")
def generate_handler(message):
    user_id = message.chat.id
    tags = get_user_tags(user_id)
    prompt_parts = []
    for tag in tags:
        prompt_parts.append(tag_prompts.get(tag, tag))
    prompt = ", ".join(prompt_parts) + ", 1girl, nsfw, anime style"
    bot.send_message(user_id, f"🎨 Генерирую изображение по тегам:\n\n{', '.join(tags)}")

    response = requests.post(
        "https://api.replicate.com/v1/predictions",
        headers={"Authorization": f"Token {REPLICATE_TOKEN}", "Content-Type": "application/json"},
        json={"version": "8f606c0d...", "input": {"prompt": prompt}}
    )
    output_url = response.json().get("urls", {}).get("get")
    if output_url:
        for _ in range(30):
            r = requests.get(output_url, headers={"Authorization": f"Token {REPLICATE_TOKEN}"})
            out = r.json()
            if out.get("status") == "succeeded":
                img_url = out["output"][0]
                bot.send_photo(user_id, img_url, caption="✅ Готово!")
                break
    else:
        bot.send_message(user_id, "Ошибка генерации.")

# 🔘 Обработка inline кнопок
@bot.callback_query_handler(func=lambda call: call.data.startswith("cat:"))
def category_selected(call):
    category = call.data.split(":")[1]
    user_states[call.message.chat.id]["category"] = category
    markup = types.InlineKeyboardMarkup(row_width=2)
    for tag in categories[category]:
        user_tags = get_user_tags(call.message.chat.id)
        is_selected = tag in user_tags
        btn_text = f"✅ {tag}" if is_selected else tag
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"tag:{tag}"))
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back"))
    bot.edit_message_text(f"Выберите теги из категории {category}:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("tag:"))
def tag_selected(call):
    tag = call.data.split(":")[1]
    user_id = call.message.chat.id
    tags = get_user_tags(user_id)
    if tag in tags:
        tags.remove(tag)
    else:
        tags.append(tag)
    category = user_states[user_id]["category"]
    markup = types.InlineKeyboardMarkup(row_width=2)
    for tag_item in categories[category]:
        is_selected = tag_item in tags
        btn_text = f"✅ {tag_item}" if is_selected else tag_item
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"tag:{tag_item}"))
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back"))
    bot.edit_message_text(f"Выберите теги из категории {category}:", user_id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back")
def back_to_categories(call):
    choose_category_handler(call.message)

# 🌐 Webhook endpoint
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.stream.read().decode("utf-8")
    bot.process_new_updates([types.Update.de_json(update)])
    return "ok", 200

@app.route("/", methods=["GET"])
def index():
    return "Bot is running", 200

# 🚀 Запуск
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"https://retete.onrender.com/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))