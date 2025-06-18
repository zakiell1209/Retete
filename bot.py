# --- bot.py ---
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

REPLICATE_MODEL = "c1d5b02687df6081c7953c74bcc527858702e8c153c9382012ccc3906752d3ec"

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
user_settings = {}

CATEGORY_NAMES = {
    "holes": "Отверстия",
    "toys": "Игрушки",
    "poses": "Позы",
    "clothes": "Одежда",
    "body": "Тело",
    "ethnos": "Этнос",
    "furry": "Фури",
    "characters": "Персонажи",
    "head": "Голова"
}

# Теги и их отображение
TAGS = {
    "poses": {
        "hor_split": "Горизонтальный шпагат",
        "ver_split": "Вертикальный шпагат",
    },
    "characters": {
        "rias": "Риас Гремори",
        "akeno": "Акено Химедзима"
    }
}

# Внешность персонажей
CHARACTER_EXTRA = {
    "rias": "red long hair, blue eyes, pale skin, large breasts, rias gremory, highschool dxd",
    "akeno": "long black hair, purple eyes, large breasts, akeno himejima, highschool dxd"
}

# Промпты
TAG_PROMPTS = {
    **CHARACTER_EXTRA,
    "hor_split": (
        "1girl, doing full horizontal split, legs perfectly flat to each side, "
        "pelvis on floor, hands on floor, solo, centered, full body, high detail, realistic anatomy"
    ),
    "ver_split": (
        "1girl, vertical split, one leg raised straight up, hands holding leg, "
        "solo, full body, perfect balance, realistic pose, high detail"
    )
}

# Главное меню
def main_menu():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🧩 Выбрать теги", callback_data="choose_tags"))
    kb.add(types.InlineKeyboardButton("🎨 Генерировать", callback_data="generate"))
    return kb

# Меню категорий
def category_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    for key, name in CATEGORY_NAMES.items():
        kb.add(types.InlineKeyboardButton(name, callback_data=f"cat_{key}"))
    kb.add(types.InlineKeyboardButton("✅ Готово", callback_data="done_tags"))
    return kb

# Меню тегов
def tag_menu(category, selected_tags):
    kb = types.InlineKeyboardMarkup(row_width=2)
    for tag_key, tag_name in TAGS[category].items():
        label = f"✅ {tag_name}" if tag_key in selected_tags else tag_name
        kb.add(types.InlineKeyboardButton(label, callback_data=f"tag_{category}_{tag_key}"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="back_to_cat"))
    return kb

# Обработка старта
@bot.message_handler(commands=["start"])
def start(msg):
    cid = msg.chat.id
    user_settings[cid] = {"tags": [], "last_cat": None}
    bot.send_message(cid, "Привет! Что делаем?", reply_markup=main_menu())

# Обработка кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    cid = call.message.chat.id
    if cid not in user_settings:
        user_settings[cid] = {"tags": [], "last_cat": None}

    data = call.data

    if data == "choose_tags":
        bot.edit_message_text("Выбери категорию тегов:", cid, call.message.message_id, reply_markup=category_menu())

    elif data.startswith("cat_"):
        cat = data[4:]
        user_settings[cid]["last_cat"] = cat
        selected = user_settings[cid]["tags"]
        bot.edit_message_text(f"Категория: {CATEGORY_NAMES[cat]}", cid, call.message.message_id, reply_markup=tag_menu(cat, selected))

    elif data.startswith("tag_"):
        _, cat, tag = data.split("_", 2)
        tags = user_settings[cid]["tags"]
        if tag in tags:
            tags.remove(tag)
        else:
            tags.append(tag)
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=tag_menu(cat, tags))

    elif data == "done_tags":
        bot.edit_message_text("Теги сохранены.", cid, call.message.message_id, reply_markup=main_menu())

    elif data == "back_to_cat":
        bot.edit_message_text("Выбери категорию:", cid, call.message.message_id, reply_markup=category_menu())

    elif data == "generate":
        tags = user_settings[cid]["tags"]
        if not tags:
            bot.send_message(cid, "Сначала выбери теги!")
            return
        prompt = build_prompt(tags)
        user_settings[cid]["last_prompt"] = tags.copy()
        bot.send_message(cid, "⏳ Генерация изображения...")
        url = replicate_generate(prompt)
        if url:
            kb = types.InlineKeyboardMarkup()
            kb.add(
                types.InlineKeyboardButton("🔁 Начать заново", callback_data="start"),
                types.InlineKeyboardButton("🔧 Изменить теги", callback_data="edit_tags"),
                types.InlineKeyboardButton("➡ Продолжить с этими", callback_data="generate")
            )
            bot.send_photo(cid, url, caption="✅ Готово!", reply_markup=kb)
        else:
            bot.send_message(cid, "❌ Ошибка генерации.")

    elif data == "edit_tags":
        if "last_prompt" in user_settings[cid]:
            user_settings[cid]["tags"] = user_settings[cid]["last_prompt"]
            bot.send_message(cid, "Изменяем теги:", reply_markup=category_menu())
        else:
            bot.send_message(cid, "Нет сохранённых тегов. Сначала сделай генерацию.")

    elif data == "start":
        user_settings[cid] = {"tags": [], "last_cat": None}
        bot.send_message(cid, "Сброс настроек.", reply_markup=main_menu())

# Генерация prompt
def build_prompt(tags):
    base = (
        "nsfw, masterpiece, ultra detailed, anime style, best quality, fully nude, solo, full body, "
        "no clothing covering breasts or genitals, no hands or objects covering nipples or pussy, "
        "no hair covering chest or genitals, no arms covering chest, nipples must be visible, genitalia visible, "
        "realistic anatomy, no censorship, no watermarks"
    )

    prompts = []
    character_prompt = None
    pose_prompt = None

    for tag in tags:
        if tag in CHARACTER_EXTRA:
            character_prompt = CHARACTER_EXTRA[tag]
        elif tag in ["hor_split", "ver_split"]:
            pose_prompt = TAG_PROMPTS.get(tag, tag)
        else:
            prompts.append(TAG_PROMPTS.get(tag, tag))

    if character_prompt and pose_prompt:
        prompts.insert(0, f"{character_prompt}, {pose_prompt}")
    elif character_prompt:
        prompts.insert(0, character_prompt)
    elif pose_prompt:
        prompts.insert(0, pose_prompt)

    return base + ", " + ", ".join(prompts)

# Генерация через Replicate
def replicate_generate(prompt):
    url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {REPLICATE_TOKEN}",
        "Content-Type": "application/json"
    }
    json_data = {
        "version": REPLICATE_MODEL,
        "input": {"prompt": prompt}
    }
    r = requests.post(url, headers=headers, json=json_data)
    if r.status_code != 201:
        return None
    status_url = r.json()["urls"]["get"]

    for _ in range(60):
        time.sleep(2)
        r = requests.get(status_url, headers=headers)
        if r.status_code != 200:
            return None
        data = r.json()
        if data["status"] == "succeeded":
            return data["output"][0] if isinstance(data["output"], list) else data["output"]
        elif data["status"] == "failed":
            return None
    return None

# Webhook
@app.route("/", methods=["POST"])
def webhook():
    json_str = request.stream.read().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "ok", 200

@app.route("/", methods=["GET"])
def home():
    return "бот работает", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=PORT)