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
    "poses": "Позы", "clothes": "Одежда", "body": "Тело", "ethnos": "Этнос",
    "furry": "Фури", "characters": "Персонажи", "head": "Голова",
    "toys": "Игрушки", "holes": "Отверстия", "view": "Обзор"
}

TAGS = {
    "poses": {
        "doggy": "Собачка", "squat": "Приседание", "lying": "Лежа",
        "standing": "Стоя", "ver_split": "Вертикальный шпагат", "hor_split": "Горизонтальный шпагат",
        "bridge": "Мост", "suspended": "Подвешена", "side_up_leg": "На боку с ногой вверх"
    },
    "clothes": {
        "stockings": "Чулки", "heels": "Каблуки", "shibari": "Шибари",
        "mask": "Маска", "bikini_tan_lines": "Загар от бикини"
    },
    "body": {
        "big_breasts": "Большая грудь", "small_breasts": "Маленькая грудь",
        "skin_white": "Белая кожа", "skin_black": "Чёрная кожа",
        "body_thin": "Худое тело", "body_fat": "Пышное тело", "body_normal": "Нормальное тело",
        "age_loli": "Лоли", "age_milf": "Милфа"
    },
    "ethnos": {
        "ethnicity_asian": "Азиатка", "ethnicity_european": "Европейка",
        "futanari": "Футанари", "femboy": "Фембой"
    },
    "furry": {
        "furry_fox": "Фури лисица", "furry_bunny": "Фури кролик", "furry_wolf": "Фури волчица"
    },
    "characters": {
        "rias": "Риас Гремори", "akeno": "Акено", "kafka": "Кафка",
        "eula": "Еола", "fu_xuan": "Фу Сюань", "ayase": "Сейко Аясе"
    },
    "head": {
        "ahegao": "Ахегао", "ecstasy_face": "Экстаз", "pain_face": "Боль",
        "gold_lipstick": "Золотая помада"
    },
    "toys": {
        "dildo": "Дилдо", "huge_dildo": "Большое дилдо",
        "anal_plug": "Анальная пробка", "anal_beads": "Анальные бусы",
        "gag": "Кляп", "long_dildo_path": "Дилдо из ануса выходит изо рта"
    },
    "holes": {
        "vagina": "Вагина", "anal": "Анус", "both": "Вагина и анус"
    },
    "view": {
        "view_bottom": "Снизу", "view_top": "Сверху",
        "view_side": "Сбоку", "view_close": "Ближе", "view_full": "Дальше"
    }
}

RU_TO_TAG = {}
for cat in TAGS.values():
    for k, v in cat.items():
        RU_TO_TAG[v.lower()] = k

@bot.message_handler(commands=["start"])
def start(msg):
    cid = msg.chat.id
    user_settings[cid] = {"tags": [], "last_cat": None, "count": 1}
    bot.send_message(cid, "Привет! Что делаем?", reply_markup=main_menu())

def main_menu():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🧩 Выбрать теги", callback_data="choose_tags"))
    kb.add(types.InlineKeyboardButton("🎨 Генерировать", callback_data="generate"))
    return kb

def category_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    for k, v in CATEGORY_NAMES.items():
        kb.add(types.InlineKeyboardButton(v, callback_data=f"cat_{k}"))
    kb.add(types.InlineKeyboardButton("✅ Готово", callback_data="done_tags"))
    kb.add(types.InlineKeyboardButton("📸 Кол-во фото", callback_data="choose_count"))
    return kb

def count_menu():
    kb = types.InlineKeyboardMarkup(row_width=4)
    for i in range(1, 5):
        kb.add(types.InlineKeyboardButton(str(i), callback_data=f"count_{i}"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="back_to_cat"))
    return kb

def tag_menu(category, selected):
    kb = types.InlineKeyboardMarkup(row_width=2)
    for key, name in TAGS[category].items():
        text = f"✅ {name}" if key in selected else name
        kb.add(types.InlineKeyboardButton(text, callback_data=f"tag_{category}_{key}"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="back_to_cat"))
    return kb

@bot.message_handler(func=lambda msg: True)
def handle_tag_input(msg):
    cid = msg.chat.id
    tags = []
    for name in msg.text.split(","):
        tag = RU_TO_TAG.get(name.strip().lower())
        if tag:
            tags.append(tag)
    if not tags:
        bot.send_message(cid, "❌ Не удалось распознать ни одного тега.")
        return
    user_settings[cid] = {"tags": tags, "last_cat": None, "count": 1}
    bot.send_message(cid, f"✅ Теги: {', '.join(name for key in tags for name, val in RU_TO_TAG.items() if val == key)}", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    cid = call.message.chat.id
    data = call.data
    settings = user_settings.setdefault(cid, {"tags": [], "last_cat": None, "count": 1})
    if data == "choose_tags":
        bot.edit_message_text("Выбери категорию тегов:", cid, call.message.message_id, reply_markup=category_menu())
    elif data.startswith("cat_"):
        cat = data[4:]
        settings["last_cat"] = cat
        bot.edit_message_text(f"Категория: {CATEGORY_NAMES[cat]}", cid, call.message.message_id, reply_markup=tag_menu(cat, settings["tags"]))
    elif data.startswith("tag_"):
        _, cat, tag = data.split("_", 2)
        tags = settings["tags"]
        if tag in tags:
            tags.remove(tag)
        else:
            tags.append(tag)
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=tag_menu(cat, tags))
    elif data == "done_tags":
        bot.edit_message_text("✅ Теги сохранены.", cid, call.message.message_id, reply_markup=main_menu())
    elif data == "back_to_cat":
        bot.edit_message_text("Выбери категорию:", cid, call.message.message_id, reply_markup=category_menu())
    elif data == "choose_count":
        bot.edit_message_text("Сколько изображений сгенерировать?", cid, call.message.message_id, reply_markup=count_menu())
    elif data.startswith("count_"):
        settings["count"] = int(data.split("_")[1])
        bot.edit_message_text(f"✅ Кол-во изображений: {settings['count']}", cid, call.message.message_id, reply_markup=category_menu())
    elif data == "generate":
        if not settings["tags"]:
            bot.send_message(cid, "Сначала выбери теги.")
            return
        prompt = build_prompt(settings["tags"])
        neg = NEGATIVE_PROMPT
        count = settings.get("count", 1)
        bot.send_message(cid, f"⏳ Генерация {count} изображений...")
        urls = replicate_generate(prompt, neg, count)
        if urls:
            media = [types.InputMediaPhoto(u) for u in urls]
            bot.send_media_group(cid, media)
            kb = types.InlineKeyboardMarkup()
            kb.add(
                types.InlineKeyboardButton("🔁 Начать заново", callback_data="start"),
                types.InlineKeyboardButton("🔧 Изменить теги", callback_data="choose_tags"),
                types.InlineKeyboardButton("➡ Продолжить с этими", callback_data="generate")
            )
            bot.send_message(cid, "✅ Готово!", reply_markup=kb)
        else:
            bot.send_message(cid, "❌ Не удалось сгенерировать.")
    elif data == "start":
        user_settings[cid] = {"tags": [], "last_cat": None, "count": 1}
        bot.send_message(cid, "🔁 Начинаем заново.", reply_markup=main_menu())

def build_prompt(tags):
    base = "nsfw, anime, masterpiece, best quality, fully nude, no hands on chest, hands away from breasts"
    expanded = [tag for tag in tags]
    return base + ", " + ", ".join(expanded)

NEGATIVE_PROMPT = (
    "lowres, bad anatomy, wrong proportions, blurry, text, signature, watermark, "
    "bad hands, extra limbs, censored, mosaic, poorly drawn face, extra face, bad face, "
    "male, man, penis, testicles, clothed, covering"
)

def replicate_generate(prompt, negative_prompt, count):
    url = "https://api.replicate.com/v1/predictions"
    headers = {"Authorization": f"Token {REPLICATE_TOKEN}", "Content-Type": "application/json"}
    json_data = {
        "version": REPLICATE_MODEL,
        "input": {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "num_outputs": count
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
            return data["output"]
        elif data["status"] == "failed":
            return []
    return []

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