# --- bot.py ---
import os
import time
import requests
import random
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

# 🔁 Сопоставление RU названий
RU_TO_TAG = {ru.lower(): key for cat in TAGS.values() for key, ru in cat.items()}

@bot.message_handler(func=lambda msg: True, content_types=["text"])
def handle_tag_input(msg):
    cid = msg.chat.id
    tags = []
    for name in msg.text.split(","):
        key = RU_TO_TAG.get(name.strip().lower())
        if key:
            tags.append(key)
    if not tags:
        bot.send_message(cid, "❌ Не удалось распознать ни одного тега.")
        return
    user_settings[cid] = {"tags": tags, "last_cat": None, "count": 1}
    bot.send_message(cid, "✅ Теги установлены.", reply_markup=main_menu())

TAG_PROMPTS = {
    "gold_lipstick": "gold lipstick on lips only",
    "vagina": "spread pussy", "anal": "spread anus", "both": "spread pussy and anus",
    "dildo": "dildo inserted", "huge_dildo": "huge dildo", "horse_dildo": "horse dildo",
    "anal_beads": "anal beads inserted", "anal_plug": "anal plug",
    "anal_expander": "anal expander stretching anus",
    "gag": "ball gag", "piercing": "nipple and genital piercings",
    "long_dildo_path": "dildo inserted into anus, bulging through stomach, exiting mouth",
    "doggy": "doggy style pose", "standing": "standing nude pose",
    "splits": "performing full split", "hor_split": "horizontal side split",
    "ver_split": "vertical front split", "side_up_leg": "on side with leg up",
    "lying_knees_up": "lying with knees bent", "bridge": "bridge pose",
    "suspended": "suspended pose, rope bondage",
    "stockings": "wearing stockings only", "bikini_tan_lines": "bikini tan lines visible",
    "mask": "mask on face", "heels": "black high heels", "shibari": "shibari rope",
    "big_breasts": "big breasts", "small_breasts": "small breasts",
    "skin_white": "white skin", "skin_black": "black skin",
    "body_fat": "curvy body", "body_thin": "thin body", "body_normal": "normal body",
    "body_fit": "fit athletic", "body_muscular": "muscular toned",
    "age_loli": "young girl loli", "age_milf": "mature milf", "age_21": "21 year old",
    "cum": "covered in cum", "belly_bloat": "belly bulge from toy",
    "succubus_tattoo": "succubus tattoo",
    "futanari": "futanari girl with realistic penis and breasts",
    "femboy": "feminine boy", "ethnicity_asian": "asian girl",
    "ethnicity_european": "european girl",
    "furry_cow": "furry cow girl", "furry_cat": "furry cat girl",
    "furry_dog": "furry dog girl", "furry_dragon": "furry dragon girl",
    "furry_sylveon": "furry sylveon", "furry_fox": "furry fox girl",
    "furry_bunny": "furry bunny girl", "furry_wolf": "furry wolf girl",
    "ahegao": "ahegao face", "pain_face": "expression of pain",
    "ecstasy_face": "expression of ecstasy",
    "view_bottom": "from below angle", "view_top": "from above angle",
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
    kb.add(types.InlineKeyboardButton("📸 Кол-во фото", callback_data="choose_count"))
    return kb

def count_menu():
    kb = types.InlineKeyboardMarkup(row_width=5)
    for i in range(1, 11):
        kb.add(types.InlineKeyboardButton(str(i), callback_data=f"count_{i}"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="back_to_cat"))
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

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    cid = call.message.chat.id
    data = call.data
    if cid not in user_settings:
        user_settings[cid] = {"tags": [], "last_cat": None, "count": 1}

    if data == "choose_tags":
        bot.edit_message_text("Выбери категорию тегов:", cid, call.message.message_id, reply_markup=category_menu())
    elif data.startswith("cat_"):
        cat = data[4:]
        user_settings[cid]["last_cat"] = cat
        bot.edit_message_text(f"Категория: {CATEGORY_NAMES[cat]}", cid, call.message.message_id, reply_markup=tag_menu(cat, user_settings[cid]["tags"]))
    elif data.startswith("tag_"):
        _, cat, tag = data.split("_", 2)
        tags = user_settings[cid]["tags"]
        tags.remove(tag) if tag in tags else tags.append(tag)
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=tag_menu(cat, tags))
    elif data == "done_tags":
        bot.edit_message_text("Теги сохранены.", cid, call.message.message_id, reply_markup=main_menu())
    elif data == "choose_count":
        bot.edit_message_text("Выбери количество изображений:", cid, call.message.message_id, reply_markup=count_menu())
    elif data.startswith("count_"):
        count = int(data.split("_")[1])
        user_settings[cid]["count"] = count
        bot.edit_message_text(f"✅ Кол-во изображений: {count}", cid, call.message.message_id, reply_markup=main_menu())
    elif data == "generate":
        tags = user_settings[cid]["tags"]
        count = user_settings[cid]["count"]
        if not tags:
            bot.send_message(cid, "Сначала выбери теги.")
            return
        prompt = build_prompt(tags)
        bot.send_message(cid, f"⏳ Генерация {count} изображений...")
        images = [replicate_generate(prompt) for _ in range(count)]
        images = list(filter(None, images))
        if images:
            media = [types.InputMediaPhoto(url) for url in images]
            bot.send_media_group(cid, media)
        else:
            bot.send_message(cid, "❌ Ошибка генерации.")

def build_prompt(tags):
    base = (
        "nsfw, masterpiece, best quality, fully nude, female only, "
        "no men, no male, no hands on chest, no covering nipples, no covering pussy, "
        "realistic body, realistic face, coherent body, full body"
    )
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
            output = data["output"]
            return output[0] if isinstance(output, list) else output
        if data["status"] == "failed":
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