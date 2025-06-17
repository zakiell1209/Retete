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

REPLICATE_MODEL = "aitechtree/nsfw-novel-generation"

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
user_settings = {}

TAGS = {
    "holes": ["vagina", "anal", "both"],
    "toys": ["dildo", "huge_dildo", "horse_dildo", "anal_beads", "anal_plug", "anal_expander", "gag", "piercing"],
    "poses": ["doggy", "standing", "splits", "squat", "lying", "hor_split", "ver_split", "side_up_leg", "front_facing", "back_facing", "lying_knees_up", "bridge", "suspended"],
    "clothes": ["stockings", "bikini_tan_lines", "mask", "heels", "shibari", "cow_costume"],
    "body": ["big_breasts", "small_breasts", "skin_white", "skin_black", "body_fat", "body_thin", "body_normal", "body_fit", "body_muscular", "age_loli", "age_milf", "age_21", "cum", "belly_bloat", "long_dildo_path", "succubus_tattoo"],
    "ethnos": ["futanari", "femboy", "ethnicity_asian", "ethnicity_european"],
    "furry": ["furry_cow", "furry_cat", "furry_dog", "furry_dragon", "furry_sylveon"],
}

CATEGORY_NAMES = {
    "holes": "Отверстия", "toys": "Игрушки", "poses": "Позы", "clothes": "Одежда", "body": "Тело", "ethnos": "Этнос", "furry": "Фури"
}

TAG_PROMPTS = {
    "vagina": "open vagina", "anal": "open anus", "both": "open anus and vagina",
    "dildo": "dildo inserted", "huge_dildo": "huge dildo", "horse_dildo": "horse dildo",
    "anal_beads": "anal beads inside", "anal_plug": "anal plug", "anal_expander": "anal expander spreading anus",
    "gag": "ball gag", "piercing": "nipple and genital piercing",
    "doggy": "doggy style", "standing": "standing pose", "splits": "doing splits", "squat": "squatting", "lying": "lying on back",
    "hor_split": "horizontal splits", "ver_split": "vertical splits", "side_up_leg": "side pose with one leg up",
    "front_facing": "facing viewer", "back_facing": "back turned to viewer", "lying_knees_up": "lying, knees up and spread",
    "bridge": "body arched like a bridge", "suspended": "body suspended with ropes",
    "stockings": "stockings only", "bikini_tan_lines": "dark skin with white bikini tan lines, no clothing", "mask": "face mask",
    "heels": "high heels", "shibari": "shibari ropes", "cow_costume": "girl in cow-print stockings, horns, tail, no underwear",
    "big_breasts": "large breasts", "small_breasts": "small breasts", "skin_white": "white skin", "skin_black": "black skin",
    "body_fat": "curvy body", "body_thin": "thin body", "body_normal": "average body", "body_fit": "fit body", "body_muscular": "muscular body",
    "age_loli": "loli", "age_milf": "milf", "age_21": "21 years old",
    "cum": "covered in cum", "belly_bloat": "belly inflation from toy", "long_dildo_path": "dildo through anus exiting mouth",
    "succubus_tattoo": "heart-shaped tattoo above womb",
    "futanari": "futanari girl with large breasts", "femboy": "femboy with feminine body",
    "ethnicity_asian": "asian girl", "ethnicity_european": "european girl",
    "furry_cow": "anthro cow girl", "furry_cat": "anthro cat girl", "furry_dog": "anthro dog girl",
    "furry_dragon": "anthro dragon girl", "furry_sylveon": "anthro sylveon, pink fur, ribbons, sexy"
}

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

def tag_menu(category, selected_tags):
    kb = types.InlineKeyboardMarkup(row_width=2)
    for tag in TAGS[category]:
        label = f"✅ {tag}" if tag in selected_tags else tag
        kb.add(types.InlineKeyboardButton(label, callback_data=f"tag_{category}_{tag}"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="back_to_cat"))
    return kb

@bot.message_handler(commands=["start"])
def start(msg):
    cid = msg.chat.id
    user_settings[cid] = {"tags": [], "last_cat": None}
    bot.send_message(cid, "Привет! Что делаем?", reply_markup=main_menu())

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
        bot.send_message(cid, "⏳ Генерация изображения...")
        url = replicate_generate(prompt)
        if url:
            kb = types.InlineKeyboardMarkup()
            kb.add(
                types.InlineKeyboardButton("🔁 Начать заново", callback_data="start"),
                types.InlineKeyboardButton("🔧 Изменить теги", callback_data="choose_tags")
            )
            bot.send_photo(cid, url, caption="✅ Готово!", reply_markup=kb)
        else:
            bot.send_message(cid, "❌ Ошибка генерации.")

    elif data == "start":
        user_settings[cid] = {"tags": [], "last_cat": None}
        bot.send_message(cid, "Сброс настроек.", reply_markup=main_menu())

def build_prompt(tags):
    base = "nsfw, masterpiece, ultra detailed, anime style, best quality"
    prompts = [TAG_PROMPTS.get(tag, tag) for tag in tags]
    return base + ", " + ", ".join(prompts)

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

@app.route("/", methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "ok", 200

@app.route("/", methods=["GET"])
def home():
    return "бот работает", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=PORT)