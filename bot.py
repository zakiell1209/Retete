# bot.py
import os
import time
import requests
from flask import Flask, request
import telebot
from telebot import types

API_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")
REPLICATE_MODEL = "c1d5b02687df6081c7953c74bcc527858702e8c153c9382012ccc3906752d3ec"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 5000))

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
user_settings = {}

CATEGORY_NAMES = {
    "count": "Количество фото",
    "holes": "Отверстия", "toys": "Игрушки", "poses": "Позы", "clothes": "Одежда",
    "body": "Тело", "ethnos": "Этнос", "furry": "Фури", "characters": "Персонажи",
    "head": "Голова", "view": "Обзор"
}

TAGS = {
    "count": {
        "1": "1", "2": "2", "3": "3", "4": "4", "5": "5",
        "6": "6", "7": "7", "8": "8", "9": "9", "10": "10"
    },
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
        "front_facing": "Лицом к зрителю", "back_facing": "Спиной к зрителю",
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

CHARACTER_EXTRA = {
    "rias": "red hair, blue eyes, large breasts, pale skin, rias gremory, highschool dxd",
    "akeno": "black hair, purple eyes, large breasts, akeno himejima, highschool dxd",
    "kafka": "purple wavy hair, kafka, honkai star rail",
    "eula": "light blue hair, fair skin, eula, genshin impact",
    "fu_xuan": "pink hair, fu xuan, honkai star rail",
    "ayase": "black hair, school uniform, ayase seiko"
}

TAG_PROMPTS = {
    **CHARACTER_EXTRA,
    "vagina": "spread pussy", "anal": "spread anus", "both": "spread pussy and anus",
    "dildo": "dildo inserted in anus", "huge_dildo": "huge dildo",
    "horse_dildo": "horse dildo", "anal_beads": "anal beads inserted",
    "anal_plug": "anal plug", "anal_expander": "anal expander stretching anus",
    "gag": "ball gag", "piercing": "nipple and genital piercings",
    "long_dildo_path": "seamless dildo passing from anus to mouth",
    "doggy": "doggy style", "standing": "standing pose", "splits": "doing a split",
    "hor_split": "horizontal split, legs flat, pelvis touching floor",
    "ver_split": "vertical split, leg up, hips aligned",
    "side_up_leg": "on side with leg raised", "front_facing": "facing viewer",
    "back_facing": "back to viewer", "lying_knees_up": "lying knees up",
    "bridge": "arched back bridge pose", "suspended": "suspended by ropes",
    "stockings": "black stockings", "mask": "blindfold", "heels": "high heels",
    "shibari": "shibari bondage", "big_breasts": "very large breasts",
    "small_breasts": "small breasts", "skin_white": "white skin",
    "skin_black": "black skin", "body_fat": "chubby body", "body_thin": "thin body",
    "body_normal": "average body", "body_fit": "fit body", "body_muscular": "muscular body",
    "age_loli": "young girl", "age_milf": "mature woman", "age_21": "21 years old",
    "cum": "covered in cum", "belly_bloat": "belly bulge",
    "succubus_tattoo": "tattoo on lower belly", "futanari": "futanari",
    "femboy": "feminine femboy", "ethnicity_asian": "asian girl",
    "ethnicity_european": "european girl", "furry_cow": "furry cow girl",
    "furry_cat": "furry cat girl", "furry_dog": "furry dog girl",
    "furry_dragon": "furry dragon girl", "furry_sylveon": "furry sylveon style",
    "furry_fox": "furry fox girl", "furry_bunny": "furry bunny girl",
    "furry_wolf": "furry wolf girl", "ahegao": "ahegao face",
    "pain_face": "face in pain", "ecstasy_face": "face in ecstasy",
    "gold_lipstick": "gold lipstick on lips",
    "view_bottom": "low angle", "view_top": "top-down view",
    "view_side": "side view", "view_close": "close-up", "view_full": "full body"
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
    for tag_key, tag_name in TAGS[category].items():
        label = f"✅ {tag_name}" if tag_key in selected_tags else tag_name
        kb.add(types.InlineKeyboardButton(label, callback_data=f"tag_{category}_{tag_key}"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="back_to_cat"))
    return kb

@bot.message_handler(commands=["start"])
def start(msg):
    cid = msg.chat.id
    user_settings[cid] = {"tags": [], "last_cat": None, "count": 1}
    bot.send_message(cid, "Привет! Что делаем?", reply_markup=main_menu())

@bot.message_handler(content_types=["text"])
def handle_text(msg):
    cid = msg.chat.id
    text = msg.text.lower()
    if cid not in user_settings:
        user_settings[cid] = {"tags": [], "last_cat": None, "count": 1}

    found_tags = []
    for cat, tagset in TAGS.items():
        for tag_key, tag_label in tagset.items():
            if tag_label.lower() in text:
                found_tags.append(tag_key)

    if found_tags:
        user_settings[cid]["tags"] = list(set(user_settings[cid]["tags"] + found_tags))
        bot.send_message(cid, "Теги обновлены.", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    cid = call.message.chat.id
    if cid not in user_settings:
        user_settings[cid] = {"tags": [], "last_cat": None, "count": 1}
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
        if cat == "count":
            user_settings[cid]["count"] = int(tag)
            bot.answer_callback_query(call.id, f"Установлено: {tag} изображений")
        else:
            tags = user_settings[cid]["tags"]
            if tag in tags:
                tags.remove(tag)
            else:
                tags.append(tag)
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=tag_menu(cat, user_settings[cid]["tags"]))

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
        user_settings[cid]["last_prompt"] = tags.copy()
        bot.send_message(cid, f"⏳ Генерация {user_settings[cid]['count']} изображений...")
        for _ in range(user_settings[cid]["count"]):
            url = replicate_generate(prompt)
            if url:
                bot.send_photo(cid, url)
            else:
                bot.send_message(cid, "❌ Ошибка генерации.")

def build_prompt(tags):
    base = "nsfw, masterpiece, best quality, fully nude, no hands on chest, no clothing"
    prompts = [TAG_PROMPTS.get(tag, tag) for tag in tags]
    return base + ", " + ", ".join(prompts)

def replicate_generate(prompt):
    url = "https://api.replicate.com/v1/predictions"
    headers = {"Authorization": f"Token {REPLICATE_TOKEN}", "Content-Type": "application/json"}
    json_data = {"version": REPLICATE_MODEL, "input": {"prompt": prompt}}
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