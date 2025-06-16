# main.py
import os
import time
import requests
from flask import Flask, request
import telebot
from telebot import types

API_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 5000))

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
user_settings = {}

TAGS = {
    "poses": [
        "doggy", "standing", "splits", "squat", "lying",
        "vertical_splits", "horizontal_splits", "lying_legs_apart",
        "side_one_leg_up", "facing_viewer", "back_viewer", "bridge", "suspended_rope"
    ],
    "holes": ["vagina", "anal", "both"],
    "toys": ["dildo", "anal_beads", "anal_plug", "gag", "piercing"],
    "clothes": ["stockings", "bikini", "mask", "heels", "shibari", "cow_costume", "bikini_tan_lines"],
    "body": ["loli", "milf", "age_21", "thin", "muscular", "curvy", "normal", "big_breasts", "small_breasts", "skin_black", "skin_white"],
    "ethnicity": ["femboy", "ethnicity_asian", "ethnicity_european"],
    "furry": ["furry_cow", "furry_cat", "furry_dog", "furry_dragon", "furry_silveon"]
}

CATEGORY_NAMES = {
    "poses": "Позиции 🤸‍♀️",
    "holes": "Отверстия 🕳️",
    "toys": "Игрушки 🧸",
    "clothes": "Одежда 👗",
    "body": "Тело 💪",
    "ethnicity": "Этнос 🌍",
    "furry": "Фури 🐾"
}

# =====================================
def chunk_list(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]

def main_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🧩 Выбрать теги", callback_data="choose_category"))
    markup.add(types.InlineKeyboardButton("✏️ Ввести описание", callback_data="prompt_input"))
    return markup

def category_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    for key, name in CATEGORY_NAMES.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"cat_{key}"))
    markup.add(types.InlineKeyboardButton("✅ Готово", callback_data="tags_done"))
    return markup

def tag_page_keyboard(category, page, selected_tags):
    tags = TAGS[category]
    pages = list(chunk_list(tags, 6))
    total_pages = len(pages)
    current_tags = pages[page]

    markup = types.InlineKeyboardMarkup(row_width=2)
    for tag in current_tags:
        checked = "✅" if tag in selected_tags else ""
        markup.add(types.InlineKeyboardButton(f"{checked} {tag}", callback_data=f"tag_{tag}_{category}_{page}"))

    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("⬅", callback_data=f"page_{category}_{page-1}"))
    if page < total_pages - 1:
        nav.append(types.InlineKeyboardButton("➡", callback_data=f"page_{category}_{page+1}"))
    if nav:
        markup.add(*nav)

    markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="choose_category"))
    return markup

# =====================================
@bot.message_handler(commands=["start"])
def start(message):
    cid = message.chat.id
    user_settings[cid] = {"features": [], "last_features": [], "waiting": False}
    bot.send_message(cid, "Привет! Выбери действие:", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    cid = call.message.chat.id
    data = call.data
    if cid not in user_settings:
        user_settings[cid] = {"features": [], "last_features": [], "waiting": False}

    if data == "choose_category":
        bot.edit_message_text("Выбери категорию:", cid, call.message.message_id, reply_markup=category_keyboard())

    elif data.startswith("cat_"):
        cat = data.split("_")[1]
        bot.edit_message_text(f"Выбор тегов: {CATEGORY_NAMES[cat]}", cid, call.message.message_id,
                              reply_markup=tag_page_keyboard(cat, 0, user_settings[cid]["features"]))

    elif data.startswith("page_"):
        _, category, page = data.split("_")
        bot.edit_message_text(f"Выбор тегов: {CATEGORY_NAMES[category]}", cid, call.message.message_id,
                              reply_markup=tag_page_keyboard(category, int(page), user_settings[cid]["features"]))

    elif data.startswith("tag_"):
        _, tag, category, page = data.split("_")
        tags = user_settings[cid]["features"]
        if tag in tags:
            tags.remove(tag)
        else:
            tags.append(tag)
        bot.edit_message_reply_markup(cid, call.message.message_id,
                                      reply_markup=tag_page_keyboard(category, int(page), tags))

    elif data == "tags_done":
        bot.edit_message_text("Теги сохранены. Теперь введи описание.", cid, call.message.message_id,
                              reply_markup=main_menu())

    elif data == "prompt_input":
        bot.send_message(cid, "✍️ Введи описание картинки:")
        user_settings[cid]["waiting"] = True
        user_settings[cid]["last_features"] = user_settings[cid]["features"][:]

    elif data == "edit_tags":
        user_settings[cid]["features"] = user_settings[cid]["last_features"][:]
        bot.send_message(cid, "Редактируй последние теги:", reply_markup=category_keyboard())

@bot.message_handler(func=lambda m: user_settings.get(m.chat.id, {}).get("waiting"))
def prompt_handler(message):
    cid = message.chat.id
    prompt = message.text.strip()
    tags = user_settings[cid]["features"]
    user_settings[cid]["waiting"] = False
    full = prompt + ", " + ", ".join(tags)

    bot.send_message(cid, f"🧠 Генерирую по запросу:\n`{full}`", parse_mode="Markdown")
    bot.send_message(cid, "Готово! (заглушка)", reply_markup=types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("✏️ Продолжить", callback_data="prompt_input"),
        types.InlineKeyboardButton("🛠 Редактировать теги", callback_data="edit_tags")
    ))

# ==== Flask webhook ====
@app.route("/", methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "ok", 200

@app.route("/", methods=["GET"])
def index():
    return "Бот работает", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=PORT)