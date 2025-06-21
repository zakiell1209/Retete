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
        "dildo": "Дилдо", "huge_dildo": "Большое дилдо", "horse_dildo": "Лошадиное дилдо",
        "anal_beads": "Анальные бусы", "anal_plug": "Анальная пробка",
        "anal_expander": "Анальный расширитель", "gag": "Кляп",
        "piercing": "Пирсинг", "long_dildo_path": "Дилдо из ануса выходит изо рта"
    },
    "poses": {
        "doggy": "Наездница", "standing": "Стоя", "splits": "Шпагат",
        "squat": "Приседание", "lying": "Лежа", "hor_split": "Горизонтальный шпагат",
        "ver_split": "Вертикальный шпагат", "side_up_leg": "На боку с ногой вверх",
        "lying_knees_up": "Лежа с коленями вверх", "bridge": "Мост", "suspended": "Подвешена"
    },
    "clothes": {
        "stockings": "Чулки", "bikini_tan_lines": "Загар от бикини", "mask": "Маска",
        "heels": "Каблуки", "shibari": "Шибари"
    },
    "body": {
        "big_breasts": "Большая грудь", "small_breasts": "Маленькая грудь",
        "skin_white": "Белая кожа", "skin_black": "Чёрная кожа",
        "body_fat": "Пышное тело", "body_thin": "Худое тело", "body_normal": "Нормальное тело",
        "body_fit": "Подтянутое тело", "body_muscular": "Мускулистое тело",
        "age_loli": "Лоли", "age_milf": "Милфа", "age_21": "Возраст 21",
        "cum": "Вся в сперме", "belly_bloat": "Вздутие живота",
        "succubus_tattoo": "Тату внизу живота"
    },
    "ethnos": {
        "futanari": "Футанари", "femboy": "Фембой",
        "ethnicity_asian": "Азиатка", "ethnicity_european": "Европейка"
    },
    "furry": {
        "furry_cow": "Фури корова", "furry_cat": "Фури кошка", "furry_dog": "Фури собака",
        "furry_dragon": "Фури дракон", "furry_sylveon": "Фури сильвеон",
        "furry_fox": "Фури лисица", "furry_bunny": "Фури кролик", "furry_wolf": "Фури волчица"
    },
    "characters": {
        "rias": "Риас Гремори", "akeno": "Акено Химедзима", "kafka": "Кафка (Хонкай)",
        "eula": "Еола (Геншин)", "fu_xuan": "Фу Сюань", "ayase": "Аясе Сейко"
    },
    "head": {
        "ahegao": "Ахегао", "pain_face": "Лицо в боли", "ecstasy_face": "Лицо в экстазе",
        "gold_lipstick": "Золотая помада"
    },
    "view": {
        "view_bottom": "Снизу", "view_top": "Сверху",
        "view_side": "Сбоку", "view_close": "Ближе", "view_full": "Дальше"
    }
}

# Обратный словарь для распознавания русского ввода
RU_TO_TAG = {v.lower(): k for cat in TAGS.values() for k, v in cat.items()}

TAG_PROMPTS = {
    "vagina": "spread pussy", "anal": "spread anus", "both": "spread pussy and anus",
    "dildo": "dildo inserted", "huge_dildo": "huge dildo", "horse_dildo": "horse dildo",
    "anal_beads": "anal beads inserted", "anal_plug": "anal plug",
    "anal_expander": "anal expander stretching anus", "gag": "ball gag",
    "piercing": "nipple and genital piercings",
    "long_dildo_path": "dildo inserted into anus, bulging through stomach, exiting mouth, extreme toy stretch",
    "doggy": "doggy style", "standing": "standing pose", "splits": "doing full split",
    "hor_split": "horizontal split, legs wide apart, pelvis down", "ver_split": "vertical split",
    "side_up_leg": "on side, leg lifted", "lying_knees_up": "lying, knees up", "bridge": "bridge pose",
    "suspended": "suspended bondage", "stockings": "stockings only", "heels": "high heels",
    "shibari": "shibari bondage", "mask": "face mask", "bikini_tan_lines": "bikini tan lines",
    "big_breasts": "large breasts", "small_breasts": "small breasts", "skin_white": "white skin",
    "skin_black": "black skin", "body_fat": "curvy body", "body_thin": "slim body",
    "body_normal": "average body", "body_fit": "fit body", "body_muscular": "muscular body",
    "age_loli": "young loli girl", "age_milf": "mature milf", "age_21": "21 year old",
    "cum": "covered in cum", "belly_bloat": "bulging belly", "succubus_tattoo": "succubus tattoo",
    "futanari": "futanari girl", "femboy": "feminine boy", "ethnicity_asian": "asian girl",
    "ethnicity_european": "european girl", "furry_cow": "furry cow girl",
    "furry_cat": "furry cat girl", "furry_dog": "furry dog girl", "furry_dragon": "furry dragon girl",
    "furry_sylveon": "furry sylveon", "furry_fox": "furry fox girl", "furry_bunny": "furry bunny girl",
    "furry_wolf": "furry wolf girl", "ahegao": "ahegao face", "pain_face": "expression of pain",
    "ecstasy_face": "expression of ecstasy", "gold_lipstick": "gold lipstick on lips only",
    "view_bottom": "from below", "view_top": "from above", "view_side": "side view",
    "view_close": "close-up", "view_full": "full body view"
}

def build_prompt(tags):
    base = "masterpiece, high quality, realistic face, full body, female only, nsfw, no clothes"
    prompt = ", ".join(TAG_PROMPTS.get(tag, tag) for tag in tags)
    return f"{base}, {prompt}"

def build_negative_prompt():
    return (
        "bad anatomy, low quality, extra limbs, duplicate, watermark, text, "
        "male, man, men, boy, muscular male, hands on chest, hands covering breasts, "
        "hands covering pussy, covering nipples, covering genitals, mannequin, blur, glitch"
    )

def replicate_generate(prompt, negative_prompt, num_images=1):
    url = "https://api.replicate.com/v1/predictions"
    headers = {"Authorization": f"Token {REPLICATE_TOKEN}", "Content-Type": "application/json"}
    json_data = {
        "version": REPLICATE_MODEL,
        "input": {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "num_outputs": num_images
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
            return []
        data = r.json()
        if data["status"] == "succeeded":
            return data["output"] if isinstance(data["output"], list) else [data["output"]]
        if data["status"] == "failed":
            return []
    return []

@bot.message_handler(commands=["start"])
def start(msg):
    cid = msg.chat.id
    user_settings[cid] = {"tags": [], "count": 1}
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🎯 Выбрать теги", callback_data="choose"))
    bot.send_message(cid, "Привет! Нажми кнопку ниже:", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    cid = call.message.chat.id
    if cid not in user_settings:
        user_settings[cid] = {"tags": [], "count": 1}
    if call.data == "choose":
        show_categories(cid)
    elif call.data.startswith("cat_"):
        show_tags(cid, call.data[4:])
    elif call.data.startswith("tag_"):
        tag = call.data[4:]
        tags = user_settings[cid]["tags"]
        tags.remove(tag) if tag in tags else tags.append(tag)
        show_categories(cid)
    elif call.data == "generate":
        prompt = build_prompt(user_settings[cid]["tags"])
        neg = build_negative_prompt()
        count = user_settings[cid]["count"]
        bot.send_message(cid, "⏳ Генерация...")
        images = replicate_generate(prompt, neg, count)
        if images:
            media = [types.InputMediaPhoto(url) for url in images]
            bot.send_media_group(cid, media)
        else:
            bot.send_message(cid, "❌ Ошибка.")
        bot.send_message(cid, "🎯 Что дальше?", reply_markup=action_menu())

    elif call.data == "count":
        kb = types.InlineKeyboardMarkup()
        for i in range(1, 5):
            kb.add(types.InlineKeyboardButton(f"{i}", callback_data=f"c_{i}"))
        bot.send_message(cid, "Сколько изображений?", reply_markup=kb)
    elif call.data.startswith("c_"):
        user_settings[cid]["count"] = int(call.data[2:])
        bot.send_message(cid, f"✅ Будет сгенерировано: {call.data[2:]}")

def action_menu():
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("🔁 Заново", callback_data="choose"),
        types.InlineKeyboardButton("🔧 Кол-во", callback_data="count"),
        types.InlineKeyboardButton("🎨 Ещё раз", callback_data="generate")
    )
    return kb

def show_categories(cid):
    kb = types.InlineKeyboardMarkup()
    for cat in TAGS:
        kb.add(types.InlineKeyboardButton(CATEGORY_NAMES[cat], callback_data=f"cat_{cat}"))
    kb.add(types.InlineKeyboardButton("🎨 Генерация", callback_data="generate"))
    kb.add(types.InlineKeyboardButton("📸 Кол-во", callback_data="count"))
    bot.send_message(cid, "Выбери категорию:", reply_markup=kb)

def show_tags(cid, category):
    kb = types.InlineKeyboardMarkup()
    for tag, ru in TAGS[category].items():
        label = f"✅ {ru}" if tag in user_settings[cid]["tags"] else ru
        kb.add(types.InlineKeyboardButton(label, callback_data=f"tag_{tag}"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="choose"))
    bot.send_message(cid, f"Теги из {CATEGORY_NAMES[category]}:", reply_markup=kb)

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