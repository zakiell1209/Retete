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
REPLICATE_MODEL = "057e2276ac5dcd8d1575dc37b131f903df9c10c41aed53d47cd7d4f068c19fa5"

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
user_settings = {}

NEGATIVE_PROMPT = (
    "male, man, muscular, penis, testicles, hands on breast, hand covering chest, "
    "lingerie, panties, bra, censored, watermark, bad anatomy, blurry, duplicate, clothed"
)

TAG_PROMPTS = {
    "stockings": "only stockings, no panties, no bra, no other clothing",
    "bikini_tan_lines": "tanned skin with clear bikini tan lines, no bikini",
    "heels": "high heels",
    "shibari": "shibari bondage, ropes on body",
    "doggy": "doggy style",
    "anal": "anal penetration",
    "vagina": "vaginal penetration",
    "both": "anal and vaginal penetration",
    "dildo": "dildo inserted",
    "huge_dildo": "huge dildo deeply inserted",
    "horse_dildo": "horse dildo inserted",
    "anal_beads": "anal beads fully inserted",
    "anal_plug": "anal plug inserted",
    "anal_expander": "anal expander stretching anus",
    "long_dildo_path": "dildo inserted in anus and coming out from mouth",
    "gag": "gag in mouth",
    "piercing": "body piercing visible",
    "big_breasts": "large breasts",
    "small_breasts": "small breasts",
    "skin_white": "pale white skin",
    "skin_black": "dark skin",
    "body_fat": "plump body",
    "body_thin": "thin body",
    "body_normal": "normal body",
    "body_fit": "fit and athletic body",
    "body_muscular": "defined muscular body",
    "age_loli": "young girl loli",
    "age_milf": "mature milf",
    "age_21": "21 years old",
    "cum": "covered in cum",
    "belly_bloat": "inflated belly",
    "succubus_tattoo": "succubus tattoo on lower belly",
    "futanari": "futanari girl with female body",
    "femboy": "femboy with soft face and flat chest",
    "ethnicity_asian": "asian anime girl",
    "ethnicity_european": "european anime girl",
    "ahegao": "ahegao face",
    "ecstasy_face": "face in ecstasy",
    "pain_face": "painful expression",
    "gold_lipstick": "gold lipstick",
    "view_top": "top down view",
    "view_bottom": "view from below",
    "view_side": "side view",
    "view_close": "close-up view",
    "view_full": "full body view",
    "furry_bunny": "anthro bunny girl, sexy",
    "furry_fox": "anthro fox girl, sexy",
    "furry_wolf": "anthro wolf girl, sexy"
}

def build_prompt(tags):
    base = "nsfw, masterpiece, best quality, fully nude, solo female, detailed, anime style"
    prompts = [TAG_PROMPTS.get(tag, tag.replace("_", " ")) for tag in tags]
    return base + ", " + ", ".join(prompts)

def replicate_generate(prompt, count):
    url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {REPLICATE_TOKEN}",
        "Content-Type": "application/json"
    }
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
    for _ in range(60):
        time.sleep(2)
        r = requests.get(status_url, headers=headers)
        if r.status_code != 200:
            return None
        result = r.json()
        if result["status"] == "succeeded":
            return result["output"]
        elif result["status"] == "failed":
            return None
    return None

def main_menu():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("ð§© ÐÐ²ÐµÑÑÐ¸ ÑÐµÐ³Ð¸", callback_data="custom_tags"))
    kb.add(types.InlineKeyboardButton("ð¨ ÐÐµÐ½ÐµÑÐ¸ÑÐ¾Ð²Ð°ÑÑ", callback_data="generate"))
    return kb

@bot.message_handler(commands=["start"])
def start(msg):
    cid = msg.chat.id
    user_settings[cid] = {"tags": [], "count": 1}
    bot.send_message(cid, "ÐÑÐ¸Ð²ÐµÑ! ÐÑÐ¿ÑÐ°Ð²Ñ ÑÐµÐ³Ð¸ Ð²ÑÑÑÐ½ÑÑ Ð¸Ð»Ð¸ Ð²ÑÐ±ÐµÑÐ¸ Ð¸Ð· Ð¼ÐµÐ½Ñ.", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    cid = call.message.chat.id
    data = call.data
    if data == "custom_tags":
        bot.send_message(cid, "ÐÐ²ÐµÐ´Ð¸ ÑÐµÐ³Ð¸ ÑÐµÑÐµÐ· Ð·Ð°Ð¿ÑÑÑÑ Ð½Ð° Ð°Ð½Ð³Ð»Ð¸Ð¹ÑÐºÐ¾Ð¼ (Ð½Ð°Ð¿ÑÐ¸Ð¼ÐµÑ: stockings, anal, cum):")
        user_settings[cid]["awaiting_tags"] = True
    elif data == "generate":
        tags = user_settings[cid].get("tags", [])
        count = user_settings[cid].get("count", 1)
        if not tags:
            bot.send_message(cid, "Ð¡Ð½Ð°ÑÐ°Ð»Ð° Ð²Ð²ÐµÐ´Ð¸ ÑÐµÐ³Ð¸.")
            return
        prompt = build_prompt(tags)
        bot.send_message(cid, f"â³ ÐÐµÐ½ÐµÑÐ°ÑÐ¸Ñ {count} Ð¸Ð·Ð¾Ð±ÑÐ°Ð¶ÐµÐ½Ð¸Ð¹...")
        images = replicate_generate(prompt, count)
        if not images:
            bot.send_message(cid, "â ÐÑÐ¸Ð±ÐºÐ° Ð³ÐµÐ½ÐµÑÐ°ÑÐ¸Ð¸.")
            return
        media = [types.InputMediaPhoto(url) for url in images]
        bot.send_media_group(cid, media)

@bot.message_handler(func=lambda m: True)
def on_text(msg):
    cid = msg.chat.id
    if user_settings.get(cid, {}).get("awaiting_tags"):
        text = msg.text
        tags = [tag.strip().lower().replace(" ", "_") for tag in text.split(",")]
        user_settings[cid]["tags"] = tags
        user_settings[cid]["awaiting_tags"] = False
        bot.send_message(cid, f"â Ð¢ÐµÐ³Ð¸ ÑÐ¾ÑÑÐ°Ð½ÐµÐ½Ñ: {', '.join(tags)}", reply_markup=main_menu())

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