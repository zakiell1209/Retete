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

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
user_settings = {}

REPLICATE_MODEL = "aitechtree/nsfw-novel-generation"

TAGS = {
    "holes": ["vagina", "anal", "both"],
    "toys": ["dildo", "huge_dildo", "horse_dildo", "anal_beads", "anal_plug", "anal_expander", "gag", "piercing"],
    "poses": ["doggy", "standing", "splits", "squat", "lying", "hor_split", "ver_split", "side_up_leg", "front_facing", "back_facing", "lying_knees_up", "bridge", "suspended"],
    "clothes": ["stockings", "bikini", "bikini_tan_lines", "mask", "heels", "shibari", "cow_costume"],
    "body": ["big_breasts", "small_breasts", "skin_white", "skin_black", "body_fat", "body_thin", "body_normal", "body_fit", "body_muscular", "height_tall", "height_short", "age_loli", "age_milf", "age_middle", "age_21", "cum", "belly_bloat", "long_dildo_path", "succubus_tattoo"],
    "ethnos": ["futanari", "femboy", "ethnicity_asian", "ethnicity_european"],
    "furry": ["furry_cow", "furry_cat", "furry_dog", "furry_dragon", "furry_sylveon", "furry_rabbit", "furry_fox", "furry_wolf"],
    "head": ["hair_long", "hair_short", "hair_bob", "hair_ponytail", "hair_red", "hair_white", "hair_black", "gold_lipstick", "ahegao", "pain_face", "ecstasy_face"]
}

CATEGORY_NAMES = {
    "holes": "Отверстия", "toys": "Игрушки", "poses": "Позы", "clothes": "Одежда", "body": "Тело",
    "ethnos": "Этнос", "furry": "Фури", "head": "Голова"
}

TAG_PROMPTS = {
    "femboy": "feminine male, smooth body, flat chest, soft features",
    "futanari": "futanari, penis, shemale, dickgirl, breasts",
    "succubus_tattoo": "heart-shaped womb tattoo on belly",
    "cow_costume": "girl in cow-patterned thigh-high stockings, horns, cow tail, no underwear",
    "bikini_tan_lines": "tan skin with white bikini tan lines",
    "furry_sylveon": "sexy anthropomorphic sylveon, pink and white fur, ribbons, large eyes, feminine body"
}

def build_prompt(tags):
    prompt = "1girl, solo, nsfw, detailed, high quality"
    for tag in tags:
        prompt += ", " + TAG_PROMPTS.get(tag, tag.replace("_", " "))
    return prompt

def get_user_tags(user_id):
    return user_settings.setdefault(user_id, {"tags": [], "category": None})

@bot.message_handler(commands=["start"])
def start_handler(message):
    markup = types.InlineKeyboardMarkup()
    for cat in TAGS.keys():
        markup.add(types.InlineKeyboardButton(CATEGORY_NAMES[cat], callback_data=f"cat:{cat}"))
    markup.add(types.InlineKeyboardButton("✅ Готово", callback_data="generate"))
    bot.send_message(message.chat.id, "Выбери категории тегов:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat:"))
def category_handler(call):
    cat = call.data.split(":")[1]
    user_settings[call.from_user.id]["category"] = cat
    markup = types.InlineKeyboardMarkup(row_width=2)
    for tag in TAGS[cat]:
        tag_text = "✅ " + tag if tag in get_user_tags(call.from_user.id)["tags"] else tag
        markup.add(types.InlineKeyboardButton(tag_text, callback_data=f"tag:{tag}"))
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back"))
    bot.edit_message_text(f"Выбери теги для категории {CATEGORY_NAMES[cat]}:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("tag:"))
def tag_handler(call):
    tag = call.data.split(":")[1]
    tags = get_user_tags(call.from_user.id)["tags"]
    if tag in tags:
        tags.remove(tag)
    else:
        tags.append(tag)
    category_handler(call)

@bot.callback_query_handler(func=lambda call: call.data == "back")
def back_handler(call):
    start_handler(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "generate")
def generate_handler(call):
    tags = get_user_tags(call.from_user.id)["tags"]
    if not tags:
        bot.answer_callback_query(call.id, "Сначала выбери теги!")
        return
    prompt = build_prompt(tags)
    msg = bot.send_message(call.message.chat.id, "🧠 Генерация изображения...")
    image_url = replicate_generate(prompt)
    if image_url:
        bot.send_photo(call.message.chat.id, image_url, caption="🎨 Сгенерировано!")
    else:
        bot.send_message(call.message.chat.id, "❌ Ошибка генерации.")

def replicate_generate(prompt):
    url = f"https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {REPLICATE_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "version": "c1d5b02687df6081c7953c74bcc527858702e8c153c9382012ccc3906752d3ec",
        "input": {"prompt": prompt}
    }
    try:
        r = requests.post(url, json=data, headers=headers)
        prediction = r.json()
        prediction_id = prediction["id"]

        for _ in range(60):
            time.sleep(2)
            res = requests.get(f"{url}/{prediction_id}", headers=headers).json()
            if res["status"] == "succeeded":
                return res["output"][-1]
            if res["status"] == "failed":
                return None
    except:
        return None

@app.route(f"/{API_TOKEN}", methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "ok", 200

@app.route("/", methods=["GET"])
def index():
    return "бот работает"

if __name__ == "__main__":
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=f"{WEBHOOK_URL}/{API_TOKEN}")
    app.run(host="0.0.0.0", port=PORT)