import os
import json
import requests
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# 🔐 токены и ключи
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

user_settings = {}

# 👇 Категории и теги
TAGS = {
    "отверстия": ["vagina", "anal", "both"],
    "игрушки": ["dildo", "huge_dildo", "horse_dildo", "long_dildo_path", "anal_beads", "anal_plug", "anal_expander", "gag", "piercing"],
    "поза": ["doggy", "standing", "splits", "squat", "lying", "hor_split", "ver_split", "side_up_leg", "front_facing", "back_facing", "lying_knees_up"],
    "одежда": ["stockings", "bikini_tan_lines", "mask", "heels", "shibari", "cow_costume"],
    "тело": ["big_breasts", "small_breasts", "skin_white", "skin_black", "body_fat", "body_thin", "body_normal", "body_fit", "body_muscular", "height_tall", "height_short", "age_loli", "age_milf", "age_middle", "age_21"],
    "дополнительно": ["cum", "belly_bloat", "succubus_tattoo"],
    "этнос": ["futanari", "femboy", "ethnicity_asian", "ethnicity_european"],
    "фури": ["furry_cow", "furry_cat", "furry_dog", "furry_dragon", "furry_sylveon"]
}

def build_prompt(tags):
    base = "nsfw, masterpiece, ultra detailed, anime style, best quality"
    map_tag = {
        "vagina": "open vagina", "anal": "open anus", "both": "open anus and vagina",
        "dildo": "dildo", "huge_dildo": "huge dildo", "horse_dildo": "horse dildo",
        "anal_beads": "anal beads causing belly bloat", "anal_plug": "anal plug", "anal_expander": "anal expander",
        "gag": "gag", "piercing": "body piercing",
        "doggy": "doggy style", "standing": "standing pose", "splits": "splits", "squat": "squatting",
        "lying": "lying", "hor_split": "horizontal splits", "ver_split": "vertical splits",
        "side_up_leg": "lying on side, one leg up", "front_facing": "facing viewer",
        "back_facing": "back facing", "lying_knees_up": "lying, knees up and apart",
        "stockings": "stockings", "bikini_tan_lines": "dark skin with clear white tan lines from bikini, completely nude, no bikini, no clothes",
        "mask": "mask", "heels": "high heels", "shibari": "shibari",
        "cow_costume": "girl wearing cow pattern stockings, horns, tail, no underwear, no cow body, sexy",
        "big_breasts": "large breasts", "small_breasts": "small breasts", "skin_white": "white skin", "skin_black": "black skin",
        "body_fat": "curvy body", "body_thin": "thin body", "body_normal": "average body",
        "body_fit": "fit body", "body_muscular": "muscular body", "height_tall": "tall height", "height_short": "short height",
        "age_loli": "loli", "age_milf": "milf", "age_middle": "mature woman", "age_21": "21 years old",
        "cum": "cum", "belly_bloat": "bloated belly",
        "long_dildo_path": "one long dildo penetrating from anus through digestive tract and exiting mouth, visible bulge in belly and throat",
        "succubus_tattoo": "black heart tattoo above pubic area, no wings, no horns, no tail, not succubus",
        "futanari": "futanari", "femboy": "femboy", "ethnicity_asian": "asian girl", "ethnicity_european": "european girl",
        "furry_cow": "furry cow", "furry_cat": "furry cat", "furry_dog": "furry dog",
        "furry_dragon": "furry dragon", "furry_sylveon": "anthro sylveon, pink and white fur, ribbons, large breasts, sexy"
    }
    additions = [map_tag.get(tag, tag) for tag in tags]
    return base + ", " + ", ".join(additions)

def category_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    for cat in TAGS:
        kb.add(InlineKeyboardButton(cat, callback_data=f"cat_{cat}"))
    return kb

def tags_keyboard(category, cid):
    kb = InlineKeyboardMarkup(row_width=2)
    selected = user_settings[cid].get("tags", [])
    for tag in TAGS[category]:
        check = "✅" if tag in selected else ""
        kb.add(InlineKeyboardButton(f"{check} {tag}", callback_data=f"tag_{tag}"))
    kb.add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_cats"))
    return kb

@bot.message_handler(commands=["start"])
def start(message):
    cid = message.chat.id
    user_settings[cid] = {"tags": [], "last_category": None}
    bot.send_message(cid, "Выберите категории тегов:", reply_markup=category_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    cid = call.message.chat.id
    data = call.data

    if data.startswith("cat_"):
        cat = data[4:]
        user_settings[cid]["last_category"] = cat
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=tags_keyboard(cat, cid))

    elif data.startswith("tag_"):
        tag = data[4:]
        tags = user_settings[cid]["tags"]
        if tag in tags:
            tags.remove(tag)
        else:
            tags.append(tag)
        cat = user_settings[cid].get("last_category")
        user_settings[cid]["last_category"] = cat
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=tags_keyboard(cat, cid))

    elif data == "back_to_cats":
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=category_keyboard())

@bot.message_handler(func=lambda m: m.text.lower() == "сгенерировать")
def generate_image(message):
    cid = message.chat.id
    tags = user_settings.get(cid, {}).get("tags", [])
    prompt = build_prompt(tags)

    headers = {"Authorization": f"Token {REPLICATE_TOKEN}"}
    json_data = {
        "version": "aitechtree/nsfw-novel-generation:latest",
        "input": {"prompt": prompt}
    }
    r = requests.post("https://api.replicate.com/v1/predictions", headers=headers, json=json_data)
    prediction = r.json()
    image_url = prediction["urls"]["get"]

    import time
    for _ in range(20):
        time.sleep(3)
        res = requests.get(image_url, headers=headers).json()
        if res["status"] == "succeeded":
            bot.send_photo(cid, res["output"][0], caption="✅ Готово")
            break
        elif res["status"] == "failed":
            bot.send_message(cid, "❌ Ошибка генерации.")
            break

# 🌐 Webhook (Render)
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def telegram_webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@app.route("/")
def index():
    return "Бот работает."

# 🚀 Запуск Flask
if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))