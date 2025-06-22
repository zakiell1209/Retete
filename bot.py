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

REPLICATE_MODEL = "057e2276ac5dcd8d1575dc37b131f903df9c10c41aed53d47cd7d4f068c19fa5"

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
user_settings = {}

NEGATIVE_PROMPT = (
    "male, man, penis, testicles, muscular male, hands on chest, hands covering nipples, "
    "hand on breast, censored, bra, panties, blurry, lowres, bad anatomy, watermark, text"
)

CATEGORY_NAMES = {
    "poses": "Позы", "clothes": "Одежда", "body": "Тело", "head": "Голова",
    "ethnos": "Этнос", "furry": "Фури", "view": "Обзор", "toys": "Игрушки", "holes": "Отверстия"
}

TAGS = {
    "poses": {
        "doggy": "doggy style, back arched, butt up",
        "squat": "squatting, legs apart",
        "lying": "lying down, legs spread",
        "ver_split": "vertical splits, spread legs",
        "hor_split": "horizontal splits, flexible pose",
        "bridge": "backbend pose, arched spine",
        "suspended": "suspended in air, ropes",
        "side_up_leg": "lying on side, one leg up"
    },
    "clothes": {
        "stockings": "stockings only, no panties, no bra, sheer",
        "shibari": "shibari bondage, ropes only, no clothes",
        "heels": "high heels only, no other clothes",
        "bikini_tan_lines": "bikini tan lines on bare skin, no bikini"
    },
    "body": {
        "big_breasts": "large breasts, visible nipples",
        "small_breasts": "small breasts",
        "body_thin": "thin body",
        "body_fat": "curvy body",
        "skin_white": "white skin",
        "skin_black": "black skin",
        "cum": "cum on body and face",
        "belly_bloat": "bloated belly from anal inflation",
        "succubus_tattoo": "succubus tattoo on lower belly"
    },
    "head": {
        "ahegao": "ahegao expression",
        "pain_face": "face showing pain",
        "ecstasy_face": "face in ecstasy",
        "gold_lipstick": "gold lipstick on lips only"
    },
    "ethnos": {
        "futanari": "futanari with female body, no penis visible",
        "femboy": "femboy with feminine body, soft face",
        "ethnicity_asian": "asian female character",
        "ethnicity_european": "european female character"
    },
    "furry": {
        "furry_cow": "anthro cow girl, big breasts, sexy",
        "furry_fox": "anthro fox girl, long tail, seductive",
        "furry_wolf": "anthro wolf girl, muscular, dominant"
    },
    "view": {
        "view_top": "viewed from above",
        "view_bottom": "viewed from below",
        "view_side": "side view",
        "view_close": "close-up shot",
        "view_full": "full body shot"
    },
    "toys": {
        "dildo": "dildo insertion in vagina",
        "huge_dildo": "huge dildo stretching vagina",
        "horse_dildo": "horse dildo, extreme size, in anus",
        "anal_beads": "anal beads inside, visible bulge",
        "anal_plug": "anal plug in anus, visible",
        "gag": "gag in mouth",
        "piercing": "body piercings on nipples and navel",
        "long_dildo_path": "dildo from anus through mouth, body bulge"
    },
    "holes": {
        "vagina": "open vagina, wet",
        "anal": "open anus, spread",
        "both": "spread anus and vagina"
    }
}

@bot.message_handler(commands=["start"])
def start(msg):
    cid = msg.chat.id
    user_settings[cid] = {"tags": [], "count": 1}
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🧩 Теги", callback_data="tags"))
    markup.add(types.InlineKeyboardButton("🎨 Генерация", callback_data="generate"))
    bot.send_message(cid, "Привет! Выбери действие:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    cid = call.message.chat.id
    data = call.data
    user = user_settings.setdefault(cid, {"tags": [], "count": 1})

    if data == "tags":
        show_categories(cid, call.message.message_id)
    elif data.startswith("cat_"):
        cat = data[4:]
        show_tags(cid, call.message.message_id, cat)
    elif data.startswith("tag_"):
        _, cat, tag = data.split("_", 2)
        tags = user["tags"]
        if tag in tags:
            tags.remove(tag)
        else:
            tags.append(tag)
        show_tags(cid, call.message.message_id, cat)
    elif data == "done":
        main_menu(cid, "✅ Теги сохранены.", call.message.message_id)
    elif data == "generate":
        generate_images(cid, user)
    elif data == "start_over":
        start(call.message)
    elif data == "edit_tags":
        show_categories(cid, call.message.message_id)

def show_categories(cid, mid):
    kb = types.InlineKeyboardMarkup(row_width=2)
    for k, v in CATEGORY_NAMES.items():
        kb.add(types.InlineKeyboardButton(v, callback_data=f"cat_{k}"))
    kb.add(types.InlineKeyboardButton("✅ Готово", callback_data="done"))
    bot.edit_message_text("Выбери категорию:", cid, mid, reply_markup=kb)

def show_tags(cid, mid, cat):
    selected = user_settings[cid]["tags"]
    kb = types.InlineKeyboardMarkup(row_width=2)
    for tag, label in TAGS[cat].items():
        prefix = "✅ " if tag in selected else ""
        kb.add(types.InlineKeyboardButton(f"{prefix}{label}", callback_data=f"tag_{cat}_{tag}"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="tags"))
    bot.edit_message_text(f"Категория: {CATEGORY_NAMES[cat]}", cid, mid, reply_markup=kb)

def main_menu(cid, text, mid=None):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🧩 Теги", callback_data="tags"))
    kb.add(types.InlineKeyboardButton("🎨 Генерация", callback_data="generate"))
    if mid:
        bot.edit_message_text(text, cid, mid, reply_markup=kb)
    else:
        bot.send_message(cid, text, reply_markup=kb)

def build_prompt(tags):
    prompt = "nsfw, masterpiece, best quality, anime style, fully nude, solo female"
    for tag in tags:
        for group in TAGS.values():
            if tag in group:
                prompt += ", " + group[tag]
    return prompt

def generate_images(cid, user):
    prompt = build_prompt(user["tags"])
    count = user.get("count", 1)
    bot.send_message(cid, f"⏳ Генерация изображений ({count})...")
    urls = replicate_generate(prompt, count)
    if not urls:
        bot.send_message(cid, "❌ Ошибка генерации.")
        return
    media = [types.InputMediaPhoto(u) for u in urls]
    bot.send_media_group(cid, media)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔁 Начать заново", callback_data="start_over"))
    kb.add(types.InlineKeyboardButton("🎨 Снова", callback_data="generate"))
    kb.add(types.InlineKeyboardButton("🧩 Изменить теги", callback_data="edit_tags"))
    bot.send_message(cid, "✅ Готово!", reply_markup=kb)

def replicate_generate(prompt, n=1):
    url = "https://api.replicate.com/v1/predictions"
    headers = {"Authorization": f"Token {REPLICATE_TOKEN}", "Content-Type": "application/json"}
    json_data = {
        "version": REPLICATE_MODEL,
        "input": {
            "prompt": prompt,
            "negative_prompt": NEGATIVE_PROMPT,
            "num_outputs": n
        }
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
            output = data["output"]
            return output if isinstance(output, list) else [output]
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
