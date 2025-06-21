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

NEGATIVE_PROMPT = (
    "male, man, muscular male, penis, testicles, clothes, censored, lowres, bad anatomy, "
    "text, watermark, blurry, multiple people, hand on breast, hands covering chest, "
    "hands on nipples, covering nipples, extra limbs, painting, sketch, cartoon"
)

# Дальше добавим категории, теги, меню, обработчики и генерацию

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

# Остальная логика (обработчики, генерация и интерфейс) дописывается...


from telebot import types

# --- Меню ---
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
    for i in range(1, 5):
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
        selected = user_settings[cid]["tags"]
        bot.edit_message_text(f"Категория: {CATEGORY_NAMES[cat]}", cid, call.message.message_id, reply_markup=tag_menu(cat, selected))
    elif data.startswith("tag_"):
        _, cat, tag = data.split("_", 2)
        tags = user_settings[cid]["tags"]
        if tag in tags:
            tags.remove(tag)
        else:
            tags.append(tag)
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=tag_menu(cat, tags))
    elif data == "done_tags":
        bot.edit_message_text("Теги сохранены.", cid, call.message.message_id, reply_markup=main_menu())
    elif data == "back_to_cat":
        bot.edit_message_text("Выбери категорию:", cid, call.message.message_id, reply_markup=category_menu())
    elif data == "choose_count":
        bot.edit_message_text("Выбери количество изображений:", cid, call.message.message_id, reply_markup=count_menu())
    elif data.startswith("count_"):
        count = int(data.split("_")[1])
        user_settings[cid]["count"] = count
        bot.edit_message_text(f"✅ Количество изображений: {count}", cid, call.message.message_id, reply_markup=category_menu())
    elif data == "generate":
        tags = user_settings[cid]["tags"]
        count = user_settings[cid].get("count", 1)
        if not tags:
            bot.send_message(cid, "Сначала выбери теги!")
            return
        prompt = build_prompt(tags)
        user_settings[cid]["last_prompt"] = tags.copy()
        bot.send_message(cid, f"⏳ Генерация {count} изображений...")

        images = replicate_generate(prompt, count)
        if images:
            media = [types.InputMediaPhoto(url) for url in images]
            bot.send_media_group(cid, media)
            kb = types.InlineKeyboardMarkup()
            kb.add(
                types.InlineKeyboardButton("🔁 Начать заново", callback_data="start"),
                types.InlineKeyboardButton("🔧 Изменить теги", callback_data="choose_tags")
            )
            bot.send_message(cid, "✅ Готово!", reply_markup=kb)
        else:
            bot.send_message(cid, "❌ Ошибка генерации.")

def build_prompt(tags):
    base = "nsfw, masterpiece, best quality, fully nude, no men, no male, no hands on chest, no hands covering nipples, hands away from breasts"
    prompts = [tag.replace("_", " ") for tag in tags]
    return base + ", " + ", ".join(prompts)

def replicate_generate(prompt, num_outputs):
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