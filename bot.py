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

CATEGORY_NAMES = {
    "holes": "Отверстия", "toys": "Игрушки", "poses": "Позы", "clothes": "Одежда",
    "body": "Тело", "ethnos": "Этнос", "furry": "Фури", "characters": "Персонажи",
    "head": "Голова", "view": "Обзор"
}

TAGS = {
    "holes": {"vagina": "Вагина", "anal": "Анус", "both": "Вагина и анус"},
    "toys": {
        "dildo": "dildo", "huge_dildo": "huge dildo", "horse_dildo": "horse dildo",
        "anal_beads": "anal beads", "anal_plug": "anal plug",
        "anal_expander": "anal expander", "gag": "gag",
        "piercing": "piercing", "long_dildo_path": "dildo enters anus exits mouth"
    },
    "poses": {
        "doggy": "doggy style", "standing": "standing pose", "splits": "doing splits",
        "squat": "squatting", "lying": "lying", "hor_split": "horizontal splits",
        "ver_split": "vertical splits", "side_up_leg": "side view leg up",
        "front_facing": "facing viewer", "back_facing": "back facing viewer",
        "lying_knees_up": "lying with knees up", "bridge": "doing bridge", "suspended": "suspended"
    },
    "clothes": {
        "stockings": "stockings", "bikini_tan_lines": "bikini tan lines", "mask": "mask",
        "heels": "high heels", "shibari": "shibari rope"
    },
    "body": {
        "big_breasts": "large breasts", "small_breasts": "small breasts",
        "skin_white": "pale skin", "skin_black": "dark skin",
        "body_fat": "chubby", "body_thin": "thin body", "body_normal": "normal build",
        "body_fit": "fit body", "body_muscular": "muscular",
        "age_loli": "loli", "age_milf": "milf", "age_21": "21 years old",
        "cum": "covered in cum", "belly_bloat": "belly inflation",
        "succubus_tattoo": "succubus tattoo on lower belly"
    },
    "ethnos": {
        "futanari": "futanari", "femboy": "femboy",
        "ethnicity_asian": "asian", "ethnicity_european": "european"
    },
    "furry": {
        "furry_cow": "cow furry", "furry_cat": "cat furry", "furry_dog": "dog furry",
        "furry_dragon": "dragon furry", "furry_sylveon": "sylveon furry",
        "furry_fox": "fox furry", "furry_bunny": "bunny furry", "furry_wolf": "wolf furry"
    },
    "characters": {
        "rias": "Rias Gremory", "akeno": "Akeno Himejima", "kafka": "Kafka from Honkai",
        "eula": "Eula from Genshin", "fu_xuan": "Fu Xuan", "ayase": "Seiko Ayase"
    },
    "head": {
        "ahegao": "ahegao face", "pain_face": "pain expression", "ecstasy_face": "ecstasy face",
        "gold_lipstick": "gold lipstick"
    },
    "view": {
        "view_bottom": "view from below", "view_top": "view from above",
        "view_side": "side view", "view_close": "close up", "view_full": "full body"
    }
}

RU_TO_TAG = {}
for cat_tags in TAGS.values():
    for key, ru_name in cat_tags.items():
        RU_TO_TAG[ru_name.lower()] = key

TAG_PROMPTS = {
    "gold_lipstick": "gold lipstick",
}

NEGATIVE_PROMPT = "bad anatomy, extra limbs, nsfw censor, watermark, signature, logo, jpeg artifacts, blurry, male, hands on chest, covering nipples"

def build_prompt(tags):
    base = "nsfw, anime, masterpiece, best quality, fully nude, solo female, no censorship"
    prompts = [TAGS[cat][tag] for cat in TAGS for tag in tags if tag in TAGS[cat]]
    return base + ", " + ", ".join(prompts), NEGATIVE_PROMPT

def replicate_generate(prompt, negative_prompt):
    url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {REPLICATE_TOKEN}",
        "Content-Type": "application/json"
    }
    json_data = {
        "version": REPLICATE_MODEL,
        "input": {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "num_outputs": 1
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

app = Flask(__name__)

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
