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

# --- Категории и теги ---
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
        "doggy": "Наездница", "standing": "Стоя", "splits": "Шпагат", "squat": "Приседание",
        "lying": "Лежа", "hor_split": "Горизонтальный шпагат", "ver_split": "Вертикальный шпагат",
        "side_up_leg": "На боку с ногой вверх", "front_facing": "Лицом к зрителю",
        "back_facing": "Спиной к зрителю", "lying_knees_up": "Лежа с коленями вверх",
        "bridge": "Мост", "suspended": "Подвешена"
    },
    "clothes": {
        "stockings": "Чулки", "bikini_tan_lines": "Загар от бикини", "mask": "Маска",
        "heels": "Каблуки", "shibari": "Шибари"
    },
    "body": {
        "big_breasts": "Большая грудь", "small_breasts": "Маленькая грудь",
        "skin_white": "Белая кожа", "skin_black": "Чёрная кожа", "body_fat": "Пышное тело",
        "body_thin": "Худое тело", "body_normal": "Нормальное тело", "body_fit": "Подтянутое тело",
        "body_muscular": "Мускулистое тело", "age_loli": "Лоли", "age_milf": "Милфа",
        "age_21": "Возраст 21", "cum": "Вся в сперме", "belly_bloat": "Вздутие живота",
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
        "view_bottom": "Снизу", "view_top": "Сверху", "view_side": "Сбоку",
        "view_close": "Ближе", "view_full": "Дальше"
    }
}

# --- Обратный словарь для русского ввода тегов ---
RUS_TO_KEY = {v: k for group in TAGS.values() for k, v in group.items()}

TAG_PROMPTS = {
    "gold_lipstick": "gold lipstick covering lips",
    "no_men": "no men", "no_hands": "no hands covering chest or nipples",
    "fully_nude": "fully nude", "nsfw": "nsfw", "masterpiece": "masterpiece", "best quality": "best quality"
}

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
    return kb

def tag_menu(category, selected_tags):
    kb = types.InlineKeyboardMarkup(row_width=2)
    for tag_key, tag_name in TAGS[category].items():
        label = f"✅ {tag_name}" if tag_key in selected_tags else tag_name
        kb.add(types.InlineKeyboardButton(label, callback_data=f"tag_{category}_{tag_key}"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="back_to_cat"))
    return kb

# --- Обработка /start ---
@bot.message_handler(commands=["start"])
def start(msg):
    cid = msg.chat.id
    user_settings[cid] = {"tags": [], "last_cat": None, "count": 1}
    bot.send_message(cid, "Привет! Что делаем?", reply_markup=main_menu())

# --- Обработка выбора количества картинок ---
@bot.message_handler(commands=["count"])
def set_count(msg):
    cid = msg.chat.id
    count = msg.text.split(" ")[1:]
    if count and count[0].isdigit() and 1 <= int(count[0]) <= 10:
        user_settings.setdefault(cid, {})["count"] = int(count[0])
        bot.send_message(cid, f"Количество изображений: {count[0]}")
    else:
        bot.send_message(cid, "Введите: /count 2 (от 1 до 10)")

# --- Обработка русского ввода тегов ---
@bot.message_handler(func=lambda m: True, content_types=["text"])
def handle_text(msg):
    cid = msg.chat.id
    if cid not in user_settings:
        user_settings[cid] = {"tags": [], "last_cat": None, "count": 1}
    parts = [p.strip() for p in msg.text.split(",")]
    keys = [RUS_TO_KEY[p] for p in parts if p in RUS_TO_KEY]
    if keys:
        user_settings[cid]["tags"] = keys
        bot.send_message(cid, "Теги приняты. Готово к генерации.", reply_markup=main_menu())

# --- Обработка кнопок ---
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    cid = call.message.chat.id
    user_settings.setdefault(cid, {"tags": [], "last_cat": None, "count": 1})
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
    elif data == "generate":
        tags = user_settings[cid]["tags"]
        if not tags:
            bot.send_message(cid, "Сначала выбери теги!")
            return
        count = user_settings[cid].get("count", 1)
        prompt = build_prompt(tags)
        user_settings[cid]["last_prompt"] = tags.copy()
        bot.send_message(cid, f"⏳ Генерация {count} изображения(й)...")
        for i in range(count):
            url = replicate_generate(prompt)
            if url:
                kb = types.InlineKeyboardMarkup()
                kb.add(
                    types.InlineKeyboardButton("🔁 Начать заново", callback_data="start"),
                    types.InlineKeyboardButton("🔧 Изменить теги", callback_data="edit_tags"),
                    types.InlineKeyboardButton("➡ Ещё раз", callback_data="generate")
                )
                bot.send_photo(cid, url, caption="✅ Готово!", reply_markup=kb)
            else:
                bot.send_message(cid, "❌ Ошибка генерации.")
    elif data == "edit_tags":
        if "last_prompt" in user_settings[cid]:
            user_settings[cid]["tags"] = user_settings[cid]["last_prompt"]
            bot.send_message(cid, "Изменяем теги:", reply_markup=category_menu())
        else:
            bot.send_message(cid, "Нет сохранённых тегов. Сначала сделай генерацию.")
    elif data == "start":
        user_settings[cid] = {"tags": [], "last_cat": None, "count": 1}
        bot.send_message(cid, "Сброс настроек.", reply_markup=main_menu())

# --- Построение prompt ---
def build_prompt(tags):
    base = "nsfw, masterpiece, best quality, fully nude, no men, no hands covering chest or nipples"
    prompts = [TAG_PROMPTS.get(tag, tag) for tag in tags]
    return base + ", " + ", ".join(prompts)

# --- Генерация через Replicate ---
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

# --- Webhook ---
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
    time.sleep(1)
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=PORT)