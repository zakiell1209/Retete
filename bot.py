# --- bot_perfect_final.py ---
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

# Простой словарь тегов → англ. описание (будет расширен)
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