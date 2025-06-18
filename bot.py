import os
import time
import logging
import requests
from flask import Flask, request
import telebot
from telebot import types

# Токены и настройки
BOT_TOKEN = os.getenv("BOT_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
REPLICATE_MODEL = "aitechtree/nsfw-novel-generation"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

user_data = {}

categories = {
    "Персонажи": [
        "Риас Гремори", "Акено Химедзима", "Кафка", "Еола", "Фу Сюань", "Аясе Сейко"
    ],
    "Поза": [
        "горизонтальный шпагат", "вертикальный шпагат", "на боку с одной ногой вверх", "лёжа на спине с раздвинутыми ногами, согнутыми в коленях", "мост", "подвешенная на верёвках"
    ],
    "Игрушки": [
        "дилдо из ануса выходит изо рта"
    ],
    "Сцена": [
        "лицом к зрителю", "спиной к зрителю", "вид снизу", "вид сверху", "вид сбоку", "ближе", "дальше"
    ],
    "Голова": [
        "ахегао", "лицо в боли", "лицо в экстазе", "золотая помада"
    ],
    "Фури": [
        "лисица", "кролик", "волчица"
    ],
    "Отверстия": [
        "анал", "вагина", "оральный"
    ],
    "Скин": [
        "загар", "бледная кожа", "обычная кожа"
    ],
    "Этнос": [
        "азиатка", "европейка", "латиноамериканка"
    ],
    "Одежда": [
        "голая", "разорванная одежда"
    ]
}

def build_keyboard(user_id, category):
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    selected_tags = user_data.get(user_id, {}).get("selected_tags", [])

    for tag in categories[category]:
        check = "✅" if tag in selected_tags else ""
        buttons.append(types.InlineKeyboardButton(f"{check} {tag}", callback_data=f"tag|{tag}"))

    buttons.append(types.InlineKeyboardButton("🔙 Назад", callback_data="back"))
    markup.add(*buttons)
    return markup

@bot.message_handler(commands=["start"])
def start_handler(message):
    user_data[message.chat.id] = {"selected_tags": []}
    markup = types.InlineKeyboardMarkup()
    for category in categories:
        markup.add(types.InlineKeyboardButton(category, callback_data=f"cat|{category}"))
    bot.send_message(message.chat.id, "Выбери категорию:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.message.chat.id
    data = call.data

    if data.startswith("cat|"):
        category = data.split("|")[1]
        bot.edit_message_text("Выбери теги:", chat_id=user_id, message_id=call.message.message_id,
                              reply_markup=build_keyboard(user_id, category))

    elif data.startswith("tag|"):
        tag = data.split("|")[1]
        selected_tags = user_data[user_id]["selected_tags"]
        if tag in selected_tags:
            selected_tags.remove(tag)
        else:
            selected_tags.append(tag)
        user_data[user_id]["selected_tags"] = selected_tags
        for category, tags in categories.items():
            if tag in tags:
                bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=build_keyboard(user_id, category))
                break

    elif data == "back":
        markup = types.InlineKeyboardMarkup()
        for category in categories:
            markup.add(types.InlineKeyboardButton(category, callback_data=f"cat|{category}"))
        markup.add(types.InlineKeyboardButton("🎨 Генерировать", callback_data="generate"))
        bot.edit_message_text("Выбери категорию:", chat_id=user_id, message_id=call.message.message_id, reply_markup=markup)

    elif data == "generate":
        selected_tags = user_data[user_id]["selected_tags"]
        prompt = ", ".join(selected_tags)
        prompt += ", nsfw, nude, highly detailed, best quality, realistic skin, no hands covering, no clothes"

        response = requests.post(
            "https://api.replicate.com/v1/predictions",
            headers={
                "Authorization": f"Token {REPLICATE_TOKEN}",
                "Content-Type": "application/json",
            },
            json={
                "version": REPLICATE_MODEL,
                "input": {"prompt": prompt, "width": 512, "height": 768}
            },
        )

        if response.status_code == 200:
            prediction = response.json()
            image_url = prediction["urls"].get("get", "")
            bot.send_message(user_id, "Изображение генерируется...")

            for _ in range(30):
                time.sleep(2)
                r = requests.get(image_url, headers={"Authorization": f"Token {REPLICATE_TOKEN}"})
                output = r.json()
                if output["status"] == "succeeded":
                    bot.send_photo(user_id, output["output"][0],
                                   reply_markup=build_post_gen_keyboard(user_id))
                    break
        else:
            bot.send_message(user_id, "Ошибка генерации изображения.")

def build_post_gen_keyboard(user_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🔄 Начать заново", callback_data="start_over"),
        types.InlineKeyboardButton("🎯 Продолжить с этими тегами", callback_data="generate"),
        types.InlineKeyboardButton("✏️ Изменить теги", callback_data="back"),
    )
    return markup

@app.route("/", methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "ok", 200

if __name__ == "__main__":
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
