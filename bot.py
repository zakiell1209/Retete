import os
import time
import requests
from flask import Flask, request
import telebot
from telebot import types

API_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")
REPLICATE_MODEL = "057e2276ac5dcd8d1575dc37b131f903df9c10c41aed53d47cd7d4f068c19fa5"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 5000))

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
user_settings = {}

NEGATIVE_PROMPT = (
    "male, man, muscular male, penis, testicles, hands on breast, hands covering chest, "
    "panties, bra, clothing, censored, watermark, text, blurry, lowres, bad anatomy"
)

TAGS = {
    "poses": {
        "doggy": "doggy style", "standing": "standing pose", "splits": "doing splits",
        "squat": "squatting", "lying": "lying pose", "hor_split": "horizontal splits",
        "ver_split": "vertical splits", "side_up_leg": "side pose with one leg up",
        "front_facing": "facing viewer", "back_facing": "back facing viewer",
        "lying_knees_up": "lying with knees up", "bridge": "bridge pose", "suspended": "suspended pose"
    },
    "toys": {
        "dildo": "dildo inserted", "huge_dildo": "huge dildo deep inside",
        "horse_dildo": "horse dildo inserted", "anal_beads": "anal beads inserted",
        "anal_plug": "anal plug", "anal_expander": "anal expander",
        "gag": "gag in mouth", "piercing": "visible body piercing",
        "long_dildo_path": "dildo from anus through mouth"
    },
    "clothes": {
        "stockings": "only stockings, no bra, no panties",
        "bikini_tan_lines": "bikini tan lines, no bikini", "mask": "mask on face",
        "heels": "high heels", "shibari": "shibari rope bondage"
    },
    "body": {
        "big_breasts": "large breasts", "small_breasts": "small breasts",
        "skin_white": "white skin", "skin_black": "dark skin",
        "body_fat": "plump body", "body_thin": "thin body", "body_normal": "normal body",
        "body_fit": "fit body", "body_muscular": "muscular female body",
        "age_loli": "loli girl", "age_milf": "milf", "age_21": "21 years old",
        "cum": "covered in cum", "belly_bloat": "inflated belly",
        "succubus_tattoo": "succubus tattoo on lower belly"
    },
    "ethnos": {
        "futanari": "futanari female body", "femboy": "femboy with feminine features",
        "ethnicity_asian": "asian anime girl", "ethnicity_european": "european anime girl"
    },
    "head": {
        "ahegao": "ahegao face", "pain_face": "pain expression",
        "ecstasy_face": "face in ecstasy", "gold_lipstick": "gold lipstick"
    },
    "view": {
        "view_bottom": "view from below", "view_top": "top down view",
        "view_side": "side view", "view_close": "close-up", "view_full": "full body"
    },
    "furry": {
        "furry_bunny": "anthro bunny girl", "furry_fox": "anthro fox girl", "furry_wolf": "anthro wolf girl"
    }
}

CATEGORY_NAMES = {
    "poses": "ÐÐ¾Ð·Ñ", "toys": "ÐÐ³ÑÑÑÐºÐ¸", "clothes": "ÐÐ´ÐµÐ¶Ð´Ð°",
    "body": "Ð¢ÐµÐ»Ð¾", "ethnos": "Ð­ÑÐ½Ð¾Ñ", "head": "ÐÐ¾Ð»Ð¾Ð²Ð°", "view": "ÐÐ±Ð·Ð¾Ñ", "furry": "Ð¤ÑÑÐ¸"
}

def main_menu():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("ð§© ÐÑÐ±ÑÐ°ÑÑ ÑÐµÐ³Ð¸", callback_data="choose_tags"))
    kb.add(types.InlineKeyboardButton("ð¨ ÐÐµÐ½ÐµÑÐ°ÑÐ¸Ñ", callback_data="generate"))
    return kb

def category_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    for key, name in CATEGORY_NAMES.items():
        kb.add(types.InlineKeyboardButton(name, callback_data=f"cat_{key}"))
    kb.add(types.InlineKeyboardButton("â ÐÐ¾ÑÐ¾Ð²Ð¾", callback_data="done_tags"))
    kb.add(types.InlineKeyboardButton("ð¸ ÐÐ¾Ð»-Ð²Ð¾ ÑÐ¾ÑÐ¾", callback_data="choose_count"))
    return kb

def count_menu():
    kb = types.InlineKeyboardMarkup(row_width=5)
    for i in range(1, 5):
        kb.add(types.InlineKeyboardButton(str(i), callback_data=f"count_{i}"))
    kb.add(types.InlineKeyboardButton("â¬ ÐÐ°Ð·Ð°Ð´", callback_data="back_to_cat"))
    return kb

def tag_menu(category, selected_tags):
    kb = types.InlineKeyboardMarkup(row_width=2)
    for tag, desc in TAGS[category].items():
        label = f"â {desc}" if tag in selected_tags else desc
        kb.add(types.InlineKeyboardButton(label, callback_data=f"tag_{category}_{tag}"))
    kb.add(types.InlineKeyboardButton("â¬ ÐÐ°Ð·Ð°Ð´", callback_data="back_to_cat"))
    return kb

@bot.message_handler(commands=["start"])
def start(msg):
    cid = msg.chat.id
    user_settings[cid] = {"tags": [], "last_cat": None, "count": 1}
    bot.send_message(cid, "ÐÑÐ¸Ð²ÐµÑ! Ð§ÑÐ¾ Ð´ÐµÐ»Ð°ÐµÐ¼?", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    cid = call.message.chat.id
    data = call.data
    if cid not in user_settings:
        user_settings[cid] = {"tags": [], "last_cat": None, "count": 1}
    if data == "choose_tags":
        bot.edit_message_text("ÐÑÐ±ÐµÑÐ¸ ÐºÐ°ÑÐµÐ³Ð¾ÑÐ¸Ñ:", cid, call.message.message_id, reply_markup=category_menu())
    elif data.startswith("cat_"):
        cat = data[4:]
        user_settings[cid]["last_cat"] = cat
        selected = user_settings[cid]["tags"]
        bot.edit_message_text(f"ÐÐ°ÑÐµÐ³Ð¾ÑÐ¸Ñ: {CATEGORY_NAMES[cat]}", cid, call.message.message_id, reply_markup=tag_menu(cat, selected))
    elif data.startswith("tag_"):
        _, cat, tag = data.split("_", 2)
        tags = user_settings[cid]["tags"]
        tags.remove(tag) if tag in tags else tags.append(tag)
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=tag_menu(cat, tags))
    elif data == "done_tags":
        bot.edit_message_text("Ð¢ÐµÐ³Ð¸ ÑÐ¾ÑÑÐ°Ð½ÐµÐ½Ñ.", cid, call.message.message_id, reply_markup=main_menu())
    elif data == "choose_count":
        bot.edit_message_text("ÐÑÐ±ÐµÑÐ¸ ÐºÐ¾Ð»Ð¸ÑÐµÑÑÐ²Ð¾ Ð¸Ð·Ð¾Ð±ÑÐ°Ð¶ÐµÐ½Ð¸Ð¹:", cid, call.message.message_id, reply_markup=count_menu())
    elif data.startswith("count_"):
        count = int(data.split("_")[1])
        user_settings[cid]["count"] = count
        bot.edit_message_text(f"â ÐÐ¾Ð»Ð¸ÑÐµÑÑÐ²Ð¾: {count}", cid, call.message.message_id, reply_markup=category_menu())
    elif data == "generate":
        tags = user_settings[cid]["tags"]
        count = user_settings[cid]["count"]
        if not tags:
            bot.send_message(cid, "ÐÑÐ±ÐµÑÐ¸ ÑÐµÐ³Ð¸.")
            return
        prompt = build_prompt(tags)
        bot.send_message(cid, "â³ ÐÐµÐ½ÐµÑÐ°ÑÐ¸Ñ...")
        urls = replicate_generate(prompt, count)
        if urls:
            media = [types.InputMediaPhoto(url) for url in urls]
            bot.send_media_group(cid, media)
        else:
            bot.send_message(cid, "â ÐÑÐ¸Ð±ÐºÐ° Ð³ÐµÐ½ÐµÑÐ°ÑÐ¸Ð¸.")

def build_prompt(tags):
    base = "nsfw, masterpiece, anime style, best quality, solo, female"
    details = [TAGS[cat][tag] for cat in TAGS for tag in tags if tag in TAGS[cat]]
    return base + ", " + ", ".join(details)

def replicate_generate(prompt, count):
    url = "https://api.replicate.com/v1/predictions"
    headers = {"Authorization": f"Token {REPLICATE_TOKEN}", "Content-Type": "application/json"}
    data = {
        "version": REPLICATE_MODEL,
        "input": {
            "prompt": prompt,
            "negative_prompt": NEGATIVE_PROMPT,
            "num_outputs": count
        }
    }
    r = requests.post(url, headers=headers, json=data)
    if r.status_code != 201:
        return None
    status_url = r.json()["urls"]["get"]
    for _ in range(50):
        time.sleep(2)
        res = requests.get(status_url, headers=headers)
        if res.status_code != 200:
            return None
        d = res.json()
        if d["status"] == "succeeded":
            return d["output"]
        elif d["status"] == "failed":
            return None
    return None

@app.route("/", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "ok", 200

@app.route("/", methods=["GET"])
def home():
    return "Ð±Ð¾Ñ ÑÐ°Ð±Ð¾ÑÐ°ÐµÑ", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=PORT)
