# --- bot.py ---
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
    "poses": "Позы", "clothes": "Одежда", "body": "Тело", "ethnos": "Этнос",
    "holes": "Отверстия", "toys": "Игрушки", "characters": "Персонажи"
}

TAGS = {
    "poses": {"doggy": "Наездница", "squat": "Присед", "bridge": "Мост", "suspended": "Подвешена"},
    "clothes": {"stockings": "Чулки", "heels": "Каблуки", "shibari": "Шибари"},
    "body": {
        "big_breasts": "Большая грудь", "small_breasts": "Маленькая грудь",
        "fem_body": "Женственное тело", "muscular": "Мускулистое",
        "cum": "Сперма", "belly_bulge": "Вздутие живота"
    },
    "ethnos": {
        "asian": "Азиатка", "european": "Европейка",
        "futanari": "Футанари", "femboy": "Фембой"
    },
    "holes": {"vagina": "Вагина", "anal": "Анус", "both": "Оба"},
    "toys": {
        "dildo": "Дилдо", "huge_dildo": "Большое дилдо", "horse_dildo": "Лошадиное дилдо",
        "anal_beads": "Анальные бусы", "anal_plug": "Анальная пробка",
        "anal_expander": "Анальный расширитель"
    },
    "characters": {
        "ayase": "Аясе Сейко", "rias": "Риас", "yor": "Йор", "2b": "2B"
    }
}

RU_TO_TAG = {v.lower(): k for cat in TAGS.values() for k, v in cat.items()}

TAG_PROMPTS = {
    "doggy": "doggystyle pose", "squat": "squatting open legs", "bridge": "bridge pose", "suspended": "suspended bondage",
    "stockings": "black thighhighs", "heels": "red heels", "shibari": "rope bondage shibari",
    "big_breasts": "large breasts", "small_breasts": "flat chest", "fem_body": "feminine body",
    "muscular": "muscular body", "cum": "cum on body and face", "belly_bulge": "belly bulge from insertion",
    "asian": "asian girl", "european": "european girl",
    "futanari": "futanari anatomy, penis, testicles", "femboy": "femboy, soft face, slim feminine body",
    "vagina": "vaginal insertion, visible vagina", "anal": "anal insertion, spread anus",
    "both": "vaginal and anal insertion, visible", "dildo": "dildo inserted in {hole}",
    "huge_dildo": "huge dildo inserted in {hole}", "horse_dildo": "horse dildo in {hole}",
    "anal_beads": "anal beads inserted in anus", "anal_plug": "anal plug in anus",
    "anal_expander": "anal expander stretching anus",
    "ayase": "black hair, ayase seiko from dandadan, school uniform", "rias": "red hair, rias gremory, blue eyes",
    "yor": "yor forger, black hair, red eyes", "2b": "white hair, blindfold, 2b, nier"
}

NEGATIVE_PROMPT = (
    "bad anatomy, blurry, text, watermark, lowres, clothing, male, hands covering breasts or genitals"
)

def main_menu():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🧩 Выбрать теги", callback_data="choose_tags"))
    kb.add(types.InlineKeyboardButton("🎨 Генерировать", callback_data="generate"))
    return kb

def category_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    for key, name in CATEGORY_NAMES.items():
        kb.add(types.InlineKeyboardButton(name, callback_data=f"cat_{key}"))
    kb.add(types.InlineKeyboardButton("✅ Готово", callback_data="done_tags"))
    return kb

def tag_menu(category, selected):
    kb = types.InlineKeyboardMarkup(row_width=2)
    for key, name in TAGS[category].items():
        label = f"✅ {name}" if key in selected else name
        kb.add(types.InlineKeyboardButton(label, callback_data=f"tag_{category}_{key}"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="back_to_cat"))
    return kb

@bot.message_handler(commands=["start"])
def cmd_start(msg):
    cid = msg.chat.id
    user_settings[cid] = {"tags": [], "count": 1, "last_cat": None}
    bot.send_message(cid, "Привет! Выбери теги.", reply_markup=main_menu())

@bot.message_handler(func=lambda m: True)
def handle_text(m):
    cid = m.chat.id
    tags = []
    for part in m.text.split(","):
        tag = RU_TO_TAG.get(part.strip().lower())
        if tag:
            tags.append(tag)
    if not tags:
        bot.send_message(cid, "❌ Не удалось распознать теги.")
        return
    user_settings[cid] = {"tags": tags, "count": 1, "last_cat": None}
    bot.send_message(cid, f"✅ Теги сохранены: {', '.join(part.strip() for part in m.text.split(','))}", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda c: True)
def callbacks(c):
    cid = c.message.chat.id
    data = c.data
    if cid not in user_settings:
        user_settings[cid] = {"tags": [], "count": 1, "last_cat": None}
    settings = user_settings[cid]

    if data == "choose_tags":
        bot.edit_message_text("Выбери категорию:", cid, c.message.message_id, reply_markup=category_menu())
    elif data.startswith("cat_"):
        cat = data[4:]
        settings["last_cat"] = cat
        bot.edit_message_text(f"Категория: {CATEGORY_NAMES[cat]}", cid, c.message.message_id, reply_markup=tag_menu(cat, settings["tags"]))
    elif data.startswith("tag_"):
        _, cat, tag = data.split("_")
        if tag in settings["tags"]:
            settings["tags"].remove(tag)
        else:
            settings["tags"].append(tag)
        bot.edit_message_reply_markup(cid, c.message.message_id, reply_markup=tag_menu(cat, settings["tags"]))
    elif data == "done_tags":
        bot.edit_message_text("Теги сохранены.", cid, c.message.message_id, reply_markup=main_menu())
    elif data == "back_to_cat":
        bot.edit_message_text("Выбери категорию:", cid, c.message.message_id, reply_markup=category_menu())
    elif data == "generate":
        if not settings["tags"]:
            bot.send_message(cid, "Сначала выбери теги.", reply_markup=main_menu())
            return
        bot.send_message(cid, "⏳ Генерация...")
        prompt = build_prompt(settings["tags"])
        images = replicate_generate(prompt, NEGATIVE_PROMPT, settings["count"])
        if images:
            media = [types.InputMediaPhoto(url) for url in images]
            bot.send_media_group(cid, media)
            kb = types.InlineKeyboardMarkup()
            kb.add(
                types.InlineKeyboardButton("🔁 Начать заново", callback_data="start"),
                types.InlineKeyboardButton("🔧 Изменить теги", callback_data="choose_tags"),
                types.InlineKeyboardButton("➡ Ещё раз", callback_data="generate")
            )
            bot.send_message(cid, "Готово!", reply_markup=kb)
        else:
            bot.send_message(cid, "❌ Ошибка генерации.", reply_markup=main_menu())
    elif data == "start":
        user_settings[cid] = {"tags": [], "count": 1, "last_cat": None}
        bot.send_message(cid, "🔄 Сброшено.", reply_markup=main_menu())

def build_prompt(tags):
    prompt_parts = []
    hole = "vagina"
    for tag in tags:
        base = TAG_PROMPTS.get(tag)
        if base:
            if "{hole}" in base:
                if "anal" in tags:
                    hole = "anus"
                elif "vagina" in tags:
                    hole = "vagina"
                base = base.replace("{hole}", hole)
            prompt_parts.append(base)
    return "nsfw, anime, best quality, fully nude, " + ", ".join(prompt_parts)

def replicate_generate(prompt, negative, count):
    url = "https://api.replicate.com/v1/predictions"
    headers = {"Authorization": f"Token {REPLICATE_TOKEN}", "Content-Type": "application/json"}
    payload = {"version": REPLICATE_MODEL, "input": {"prompt": prompt, "negative_prompt": negative, "num_outputs": count}}
    r = requests.post(url, headers=headers, json=payload)
    if r.status_code != 201:
        return []
    status = r.json()["urls"]["get"]
    for _ in range(60):
        time.sleep(2)
        r = requests.get(status, headers=headers)
        if r.status_code != 200:
            return []
        data = r.json()
        if data["status"] == "succeeded":
            out = data["output"]
            return out if isinstance(out, list) else [out]
        if data["status"] == "failed":
            return []
    return []

@app.route("/", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "ok", 200

@app.route("/", methods=["GET"])
def check():
    return "бот работает", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=PORT)