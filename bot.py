import os
import time
import requests
from flask import Flask, request
import telebot
from telebot import types

API_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")
REPLICATE_MODEL = "c1d5b02687df6081c7953c74bcc527858702e8c153c9382012ccc3906752d3ec"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 5000))

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
user_settings = {}

CATEGORY_NAMES = {
    "holes": "Отверстия", "toys": "Игрушки", "poses": "Позы", "clothes": "Одежда",
    "body": "Тело", "ethnos": "Этнос", "furry": "Фури", "characters": "Персонажи",
    "head": "Голова", "view": "Обзор"
}

# ... (сокращённый TAGS, TAG_PROMPTS, CHARACTER_EXTRA — будет восстановлен в полном файле)

def main_menu():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🧩 Выбрать теги", callback_data="choose_tags"))
    kb.add(types.InlineKeyboardButton("🎨 Генерировать", callback_data="generate"))
    return kb

def category_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    for key, name in CATEGORY_NAMES.items():
        kb.add(types.InlineKeyboardButton(name, callback_data=f"cat_{key}"))
    for i in range(2, 11):
        kb.add(types.InlineKeyboardButton(f"📷 {i} фото", callback_data=f"count_{i}"))
    kb.add(types.InlineKeyboardButton("✅ Готово", callback_data="done_tags"))
    return kb

def tag_menu(category, selected_tags):
    kb = types.InlineKeyboardMarkup(row_width=2)
    for tag_key, tag_name in TAGS[category].items():
        label = f"✅ {tag_name}" if tag_key in selected_tags else tag_name
        kb.add(types.InlineKeyboardButton(label, callback_data=f"tag_{category}_{tag_key}"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="back_to_cat"))
    return kb

@bot.message_handler(commands=["start"])
def start(msg):
    cid = msg.chat.id
    user_settings[cid] = {"tags": [], "last_cat": None, "count": 1}
    bot.send_message(cid, "Привет! Что делаем?", reply_markup=main_menu())

@bot.message_handler(content_types=["text"])
def manual_tags(msg):
    cid = msg.chat.id
    text = msg.text.lower()
    all_tags = {v.lower(): k for cat in TAGS.values() for k, v in cat.items()}
    selected = []
    for word in text.split(","):
        tag = all_tags.get(word.strip())
        if tag:
            selected.append(tag)
    if selected:
        user_settings[cid] = {"tags": selected, "last_cat": None, "count": 1}
        bot.send_message(cid, "Теги установлены. Жми «Генерировать».", reply_markup=main_menu())
    else:
        bot.send_message(cid, "Не удалось распознать теги. Попробуй ещё раз.")

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    cid = call.message.chat.id
    if cid not in user_settings:
        user_settings[cid] = {"tags": [], "last_cat": None, "count": 1}
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
    elif data.startswith("count_"):
        user_settings[cid]["count"] = int(data.split("_")[1])
        bot.answer_callback_query(call.id, f"Установлено: {user_settings[cid]['count']} фото")
    elif data == "back_to_cat":
        bot.edit_message_text("Выбери категорию:", cid, call.message.message_id, reply_markup=category_menu())
    elif data == "generate":
        tags = user_settings[cid]["tags"]
        count = user_settings[cid].get("count", 1)
        if not tags:
            bot.send_message(cid, "Сначала выбери теги!")
            return
        user_settings[cid]["last_prompt"] = tags.copy()
        bot.send_message(cid, f"⏳ Генерация {count} изображений...")
        urls = []
        prompt = build_prompt(tags)
        for _ in range(count):
            url = replicate_generate(prompt)
            if url:
                urls.append(url)
        if urls:
            kb = types.InlineKeyboardMarkup()
            kb.add(
                types.InlineKeyboardButton("🔁 Начать заново", callback_data="start"),
                types.InlineKeyboardButton("🔧 Изменить теги", callback_data="edit_tags"),
                types.InlineKeyboardButton("➡ Продолжить с этими", callback_data="generate")
            )
            for u in urls:
                bot.send_photo(cid, u)
            bot.send_message(cid, "✅ Готово!", reply_markup=kb)
        else:
            bot.send_message(cid, "❌ Ошибка генерации.")
    elif data == "edit_tags":
        if "last_prompt" in user_settings[cid]:
            user_settings[cid]["tags"] = user_settings[cid]["last_prompt"]
            bot.send_message(cid, "Изменяем теги:", reply_markup=category_menu())
        else:
            bot.send_message(cid, "Нет сохранённых тегов. Сначала сделай генерацию.")
    elif data == "start":
        user_settings[cid] = {"tags": [], "last_cat": None, "count": 1}
        bot.send_message(cid, "Сброс настроек.", reply_markup=main_menu())

def build_prompt(tags):
    base = "nsfw, masterpiece, best quality, fully nude, no clothing, no hands on chest, no hands covering nipples, hands away from breasts"
    prompts = [TAG_PROMPTS.get(tag, tag) for tag in tags]
    if "gold_lipstick" in tags:
        prompts = [p for p in prompts if "gold lipstick" not in p]
        prompts.append("gold lipstick on lips only")
    return base + ", " + ", ".join(prompts)

def replicate_generate(prompt):
    url = "https://api.replicate.com/v1/predictions"
    headers = {"Authorization": f"Token {REPLICATE_TOKEN}", "Content-Type": "application/json"}
    json_data = {"version": REPLICATE_MODEL, "input": {"prompt": prompt}}
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

@app.route("/", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "ok", 200

@app.route("/", methods=["GET"])
def home():
    return "бот работает", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=PORT)
