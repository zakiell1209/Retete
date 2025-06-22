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

NEGATIVE_PROMPT = "male, man, muscular male, penis, testicles, hands on chest, hands covering breasts, bra, panties, censored, text, watermark, logo, lowres, bad anatomy"

# Категории и теги с emoji
CATEGORIES = {
    "holes": "🕳️ Отверстия", "toys": "🧸 Игрушки", "poses": "🤸 Позы",
    "clothes": "👗 Одежда", "body": "🧍 Тело", "ethnos": "🌍 Этнос",
    "furry": "🐾 Фури", "characters": "🎭 Персонажи", "head": "👤 Голова", "view": "📷 Обзор"
}

TAGS = {
    "holes": {
        "vagina": "Вагина", "anal": "Анус", "both": "Оба"
    },
    "toys": {
        "dildo": "Дилдо", "huge_dildo": "Огромное дилдо", "horse_dildo": "Конское дилдо",
        "anal_beads": "Анальные бусы", "anal_plug": "Анальная пробка", "anal_expander": "Расширитель",
        "gag": "Кляп", "piercing": "Пирсинг", "long_dildo_path": "Дилдо через тело"
    },
    "poses": {
        "doggy": "Догги", "standing": "Стоя", "splits": "Шпагат", "squat": "Присед",
        "lying": "Лёжа", "hor_split": "Гор. шпагат", "ver_split": "Верт. шпагат",
        "side_up_leg": "На боку с ногой вверх", "front_facing": "Лицом", "back_facing": "Спиной",
        "lying_knees_up": "Колени вверх", "bridge": "Мост", "suspended": "Подвешена"
    },
    "clothes": {
        "stockings": "Чулки", "bikini_tan_lines": "Загар от бикини",
        "mask": "Маска", "heels": "Каблуки", "shibari": "Шибари"
    },
    "body": {
        "big_breasts": "Большая грудь", "small_breasts": "Маленькая грудь",
        "skin_white": "Белая кожа", "skin_black": "Чёрная кожа",
        "body_fat": "Пышное", "body_thin": "Худое", "body_normal": "Обычное", "body_fit": "Подтянутое",
        "body_muscular": "Мускулистое", "age_loli": "Лоли", "age_milf": "Милфа",
        "age_21": "21 год", "cum": "Вся в сперме", "belly_bloat": "Вздутие",
        "succubus_tattoo": "Тату сукуба"
    },
    "ethnos": {
        "futanari": "Футанари", "femboy": "Фембой",
        "ethnicity_asian": "Азиатка", "ethnicity_european": "Европейка"
    },
    "furry": {
        "furry_cat": "Фури кошка", "furry_dog": "Фури собака",
        "furry_cow": "Фури корова", "furry_dragon": "Фури дракон",
        "furry_sylveon": "Фури сильвеон", "furry_bunny": "Фури кролик",
        "furry_fox": "Фури лисица", "furry_wolf": "Фури волчица"
    },
    "head": {
        "ahegao": "Ахегао", "pain_face": "Лицо в боли", "ecstasy_face": "Экстаз",
        "gold_lipstick": "Золотая помада", "hair_long": "Длинные волосы",
        "hair_short": "Короткие волосы", "hair_bob": "Боб", "hair_ponytail": "Конский хвост",
        "hair_red": "Красные волосы", "hair_white": "Белые волосы", "hair_black": "Чёрные волосы"
    },
    "characters": {
        "rias": "Риас", "akeno": "Акено", "kafka": "Кафка",
        "eula": "Еола", "fu_xuan": "Фу Сюань", "ayase": "Аясе"
    },
    "view": {
        "view_top": "Сверху", "view_bottom": "Снизу",
        "view_side": "Сбоку", "view_close": "Близко", "view_full": "Далеко"
    }
}

@bot.message_handler(commands=["start"])
def start(message):
    cid = message.chat.id
    user_settings[cid] = {"tags": [], "category": None, "count": 1}
    bot.send_message(cid, "Привет! Выбери действие:", reply_markup=main_menu())

def main_menu():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🧩 Выбрать теги", callback_data="choose_tags"))
    kb.add(types.InlineKeyboardButton("🎨 Генерировать", callback_data="generate"))
    return kb

def category_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    for key, name in CATEGORIES.items():
        kb.add(types.InlineKeyboardButton(name, callback_data=f"cat_{key}"))
    kb.add(types.InlineKeyboardButton("📸 Кол-во картинок", callback_data="count"))
    kb.add(types.InlineKeyboardButton("✅ Готово", callback_data="done_tags"))
    return kb

def tag_menu(cat, selected):
    kb = types.InlineKeyboardMarkup(row_width=2)
    for key, name in TAGS[cat].items():
        prefix = "✅ " if key in selected else ""
        kb.add(types.InlineKeyboardButton(f"{prefix}{name}", callback_data=f"tag_{cat}_{key}"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="back_to_cat"))
    return kb

def count_menu():
    kb = types.InlineKeyboardMarkup(row_width=5)
    for i in range(1, 5):
        kb.add(types.InlineKeyboardButton(str(i), callback_data=f"count_{i}"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="back_to_cat"))
    return kb

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    cid = call.message.chat.id
    data = call.data
    state = user_settings.setdefault(cid, {"tags": [], "category": None, "count": 1})

    if data == "choose_tags":
        bot.edit_message_text("Выбери категорию:", cid, call.message.message_id, reply_markup=category_menu())
    elif data.startswith("cat_"):
        cat = data[4:]
        state["category"] = cat
        bot.edit_message_text(f"{CATEGORIES[cat]}:", cid, call.message.message_id, reply_markup=tag_menu(cat, state["tags"]))
    elif data.startswith("tag_"):
        _, cat, tag = data.split("_", 2)
        if tag in state["tags"]:
            state["tags"].remove(tag)
        else:
            state["tags"].append(tag)
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=tag_menu(cat, state["tags"]))
    elif data == "done_tags":
        bot.edit_message_text("Теги сохранены.", cid, call.message.message_id, reply_markup=main_menu())
    elif data == "back_to_cat":
        bot.edit_message_text("Выбери категорию:", cid, call.message.message_id, reply_markup=category_menu())
    elif data == "count":
        bot.edit_message_text("Сколько изображений генерировать?", cid, call.message.message_id, reply_markup=count_menu())
    elif data.startswith("count_"):
        state["count"] = int(data.split("_")[1])
        bot.edit_message_text(f"Количество: {state['count']}", cid, call.message.message_id, reply_markup=category_menu())
    elif data == "generate":
        if not state["tags"]:
            bot.send_message(cid, "❗ Сначала выбери теги.")
            return
        prompt = build_prompt(state["tags"])
        bot.send_message(cid, "⏳ Генерация...")
        urls = replicate_generate(prompt, state["count"])
        if urls:
            media = [types.InputMediaPhoto(u) for u in urls]
            bot.send_media_group(cid, media)
        else:
            bot.send_message(cid, "❌ Не удалось сгенерировать.")

def build_prompt(tags):
    base = "nsfw, anime style, masterpiece, high detail, fully nude, no bra, no panties, no men, no male, no hands on chest"
    mapped = [tag.replace("_", " ") for tag in tags]
    return f"{base}, {', '.join(mapped)}"

def replicate_generate(prompt, num_outputs=1):
    url = "https://api.replicate.com/v1/predictions"
    headers = {"Authorization": f"Token {REPLICATE_TOKEN}", "Content-Type": "application/json"}
    json_data = {
        "version": REPLICATE_MODEL,
        "input": {
            "prompt": prompt,
            "negative_prompt": NEGATIVE_PROMPT,
            "num_outputs": num_outputs
        }
    }
    res = requests.post(url, headers=headers, json=json_data)
    if res.status_code != 201:
        return None
    status_url = res.json()["urls"]["get"]
    for _ in range(60):
        time.sleep(2)
        check = requests.get(status_url, headers=headers)
        if check.status_code == 200:
            data = check.json()
            if data["status"] == "succeeded":
                return data["output"] if isinstance(data["output"], list) else [data["output"]]
            elif data["status"] == "failed":
                return None
    return None

@app.route("/", methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "ok", 200

@app.route("/", methods=["GET"])
def index():
    return "бот работает", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=PORT)