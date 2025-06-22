# --- bot.py ---
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
    "both": "double penetration",
    "cum": "covered in cum",
    "lying": "lying pose",
    "squat": "squatting pose",
    "femboy": "feminine body, femboy, no male genitals",
    "futanari": "futanari, feminine, penis, no testicles",
    "skin_black": "dark skin",
    "skin_white": "pale white skin",
    "age_loli": "petite loli body",
    "age_milf": "milf body, mature woman",
    "gold_lipstick": "gold lipstick on lips only",
    "no_hands_on_chest": "no hands on chest, hands away from breasts",
    "view_top": "top-down view",
    "view_side": "side view",
    "view_bottom": "from below",
    "view_full": "full body visible",
    "view_close": "close-up view"
}

def build_prompt(tags):
    base = "nsfw, masterpiece, best quality, fully nude, solo female"
    prompts = [TAG_PROMPTS.get(tag, tag) for tag in tags]
    return base + ", " + ", ".join(prompts)

def replicate_generate(prompt, count):
    url = "https://api.replicate.com/v1/predictions"
    headers = {"Authorization": f"Token {REPLICATE_TOKEN}", "Content-Type": "application/json"}
    json_data = {
        "version": REPLICATE_MODEL,
        "input": {
            "prompt": prompt,
            "negative_prompt": NEGATIVE_PROMPT,
            "num_outputs": min(count, 4)
        }
    }
    r = requests.post(url, headers=headers, json=json_data)
    if r.status_code != 201:
        return []
    status_url = r.json()["urls"]["get"]
    for _ in range(60):
        time.sleep(2)
        r = requests.get(status_url, headers=headers)
        if r.status_code != 200:
            break
        data = r.json()
        if data["status"] == "succeeded":
            return data["output"] if isinstance(data["output"], list) else [data["output"]]
        elif data["status"] == "failed":
            break
    return []

@app.route("/", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "ok", 200

@app.route("/", methods=["GET"])
def home():
    return "Ð±Ð¾Ñ ÑÐ°Ð±Ð¾ÑÐ°ÐµÑ", 200

@bot.message_handler(commands=["start"])
def start(msg):
    cid = msg.chat.id
    user_settings[cid] = {"tags": [], "count": 1}
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("ð§© ÐÑÐ±ÑÐ°ÑÑ ÑÐµÐ³Ð¸", "ð¸ ÐÐ¾Ð»-Ð²Ð¾ ÑÐ¾ÑÐ¾", "ð¨ ÐÐµÐ½ÐµÑÐ¸ÑÐ¾Ð²Ð°ÑÑ")
    bot.send_message(cid, "ÐÑÐ¸Ð²ÐµÑ! Ð§ÑÐ¾ Ð´ÐµÐ»Ð°ÐµÐ¼?", reply_markup=kb)

@bot.message_handler(func=lambda msg: True)
def handle_all(msg):
    cid = msg.chat.id
    txt = msg.text.strip().lower()

    if cid not in user_settings:
        user_settings[cid] = {"tags": [], "count": 1}

    if txt == "ð§© Ð²ÑÐ±ÑÐ°ÑÑ ÑÐµÐ³Ð¸":
        bot.send_message(cid, "ÐÐ²ÐµÐ´Ð¸ ÑÐµÐ³Ð¸ ÑÐµÑÐµÐ· Ð·Ð°Ð¿ÑÑÑÑ:")
    elif txt == "ð¸ ÐºÐ¾Ð»-Ð²Ð¾ ÑÐ¾ÑÐ¾":
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(*[str(i) for i in range(1, 5)])
        bot.send_message(cid, "ÐÑÐ±ÐµÑÐ¸ ÐºÐ¾Ð»Ð¸ÑÐµÑÑÐ²Ð¾ Ð¸Ð·Ð¾Ð±ÑÐ°Ð¶ÐµÐ½Ð¸Ð¹ (Ð´Ð¾ 4):", reply_markup=kb)
    elif txt == "ð¨ Ð³ÐµÐ½ÐµÑÐ¸ÑÐ¾Ð²Ð°ÑÑ":
        tags = user_settings[cid].get("tags", [])
        count = user_settings[cid].get("count", 1)
        if not tags:
            bot.send_message(cid, "Ð¡Ð½Ð°ÑÐ°Ð»Ð° Ð²ÑÐ±ÐµÑÐ¸ ÑÐµÐ³Ð¸.")
            return
        prompt = build_prompt(tags)
        bot.send_message(cid, f"ÐÐµÐ½ÐµÑÐ¸ÑÑÑ {count} Ð¸Ð·Ð¾Ð±ÑÐ°Ð¶ÐµÐ½Ð¸Ð¹...")
        urls = replicate_generate(prompt, count)
        if urls:
            media = [types.InputMediaPhoto(url) for url in urls]
            bot.send_media_group(cid, media)
        else:
            bot.send_message(cid, "ÐÐµ ÑÐ´Ð°Ð»Ð¾ÑÑ ÑÐ³ÐµÐ½ÐµÑÐ¸ÑÐ¾Ð²Ð°ÑÑ.")
    elif txt.isdigit() and 1 <= int(txt) <= 10:
        user_settings[cid]["count"] = int(txt)
        bot.send_message(cid, f"ÐÑÐ´ÐµÑ ÑÐ³ÐµÐ½ÐµÑÐ¸ÑÐ¾Ð²Ð°Ð½Ð¾: {txt} Ð¸Ð·Ð¾Ð±ÑÐ°Ð¶ÐµÐ½Ð¸Ð¹.")
    else:
        tags = [t.strip().lower() for t in txt.split(",") if t.strip()]
        user_settings[cid]["tags"] = tags
        bot.send_message(cid, f"Ð¢ÐµÐ³Ð¸ ÑÐ¾ÑÑÐ°Ð½ÐµÐ½Ñ: {', '.join(tags)}")

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=PORT)
