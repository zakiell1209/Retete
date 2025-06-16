import os
import time
import requests
from flask import Flask, request
import telebot
from telebot import types

API_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Например: https://your-app.onrender.com
PORT = int(os.environ.get("PORT", 5000))

REPLICATE_MODELS = {
    "anime": "c1d5b02687df6081c7953c74bcc527858702e8c153c9382012ccc3906752d3ec",  # твоя модель аниме
    "realism": "stability-ai/stable-diffusion:ac732df8",
    "3d": "stability-ai/stable-diffusion-3-medium"
}

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# Храним настройки пользователей (чат_id -> dict)
user_settings = {}

# ===== Промты и синонимы для тегов =====
TAG_CATEGORIES = {
    "holes": {
        "vagina": ["vagina", "pussy", "vaginal penetration"],
        "anal": ["anal", "anus", "anal penetration", "asshole"],
        "both": ["vagina and anal", "both holes", "double penetration"]
    },
    "toys": {
        "dildo": ["dildo", "large dildo", "horse dildo", "inserted dildo"],
        "anal_beads": ["anal beads", "anals balls"],
        "anal_plug": ["anal plug", "butt plug"],
        "gag": ["gag", "mouth gag", "klyap"]
    },
    "poses": {
        "doggy": ["doggy style", "from behind", "on all fours", "раком"],
        "standing": ["standing", "vertical pose"],
        "splits": ["split", "vertical split", "шпагат"],
        "squat": ["squatting", "on squat", "на корточках"],
        "lying": ["lying", "laying down", "лежа"]
    },
    "clothes": {
        "stockings": [
            "stockings", "thigh highs", "чулки"
        ],
        "bikini": [
            "bikini", "swimwear", "бикини"
        ],
        "mask": [
            "mask", "face mask", "маска"
        ],
        "heels": [
            "high heels", "туфли с каблуком"
        ],
        "shibari": [
            "shibari", "japanese rope bondage", "шибари", "бондаж"
        ],
        "cow_costume": [
            "cow costume", "cow outfit", "рога", "чулки", "хвост коровы", "коровий костюм"
        ],
        "bikini_tan_lines": [
            "bikini tan lines", "sharp and distinct tan lines in the shape of a bikini", "загар в линиях бикини"
        ]
    }
}

# Упрощенный словарь тегов для кнопок (callback_data) с русскими названиями и эмодзи
TAGS = {
    "holes": ["vagina", "anal", "both"],
    "toys": ["dildo", "anal_beads", "anal_plug", "gag"],
    "poses": ["doggy", "standing", "splits", "squat", "lying"],
    "clothes": [
        "stockings", "bikini", "mask", "heels", "shibari", "cow_costume", "bikini_tan_lines"
    ],
    "extras": [
        "big_breasts", "small_breasts", "piercing", "femboy",
        "ethnicity_asian", "ethnicity_european", "ethnicity_furry",
        "skin_white", "skin_black"
    ]
}

# Кнопки категорий для выбора тегов с русскими названиями и эмодзи
CATEGORY_NAMES_EMOJI = {
    "holes": "Отверстия 🕳️",
    "toys": "Игрушки 🧸",
    "poses": "Позиции 🤸‍♀️",
    "clothes": "Одежда 👗",
    "extras": "Дополнительно ✨"
}

# Подписи к тегам одежды с эмодзи
CLOTHES_NAMES_EMOJI = {
    "stockings": "Чулки 🧦",
    "bikini": "Бикини 👙",
    "mask": "Маска 😷",
    "heels": "Туфли 👠",
    "shibari": "Шибари ⛓️",
    "cow_costume": "Костюм коровы 🐄",
    "bikini_tan_lines": "Загар линиями от бикини ☀️"
}

# Названия тегов других категорий (для подсказок)
TAG_NAMES_EMOJI = {
    "holes": {
        "vagina": "Вагина ♀️",
        "anal": "Анал 🍑",
        "both": "Оба 🔥"
    },
    "toys": {
        "dildo": "Дилдо 🍆",
        "anal_beads": "Анальные бусы 🔴",
        "anal_plug": "Анальная пробка 🔵",
        "gag": "Кляп 😶"
    },
    "poses": {
        "doggy": "Догги стиль 🐕",
        "standing": "Стоя 🧍",
        "splits": "Шпагат 🤸",
        "squat": "На корточках 🧎",
        "lying": "Лежа 🛌"
    },
    "extras": {
        "big_breasts": "Большая грудь 🍒",
        "small_breasts": "Маленькая грудь 🥥",
        "piercing": "Пирсинг 💎",
        "femboy": "Фембой ⚧",
        "ethnicity_asian": "Азиатка 🈶",
        "ethnicity_european": "Европейка 🇪🇺",
        "ethnicity_furry": "Фури 🐾",
        "skin_white": "Белая кожа ⚪",
        "skin_black": "Чёрная кожа ⚫"
    }
}

# ===== Клавиатуры =====
def category_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    for cat in ["holes", "toys", "poses", "clothes", "extras"]:
        markup.add(
            types.InlineKeyboardButton(
                CATEGORY_NAMES_EMOJI[cat], callback_data=f"cat_{cat}"
            )
        )
    markup.add(types.InlineKeyboardButton("✅ Готово", callback_data="tags_done"))
    return markup

def tags_keyboard(category):
    markup = types.InlineKeyboardMarkup(row_width=2)
    if category == "clothes":
        for tag in TAGS[category]:
            name = CLOTHES_NAMES_EMOJI.get(tag, tag.replace("_", " ").capitalize())
            markup.add(types.InlineKeyboardButton(name, callback_data=f"tag_{tag}"))
    else:
        # для остальных категорий русский с эмодзи
        for tag in TAGS.get(category, []):
            name = TAG_NAMES_EMOJI.get(category, {}).get(tag, tag.replace("_", " ").capitalize())
            markup.add(types.InlineKeyboardButton(name, callback_data=f"tag_{tag}"))
    markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="tags_back"))
    return markup

# ===== Строим промт =====
def build_prompt(base, features):
    additions = []

    # Отверстия
    if "vagina" in features: additions.append("vagina, pussy, vaginal penetration")
    if "anal" in features: additions.append("anal sex, anal penetration, anus focus")
    if "both" in features: additions.append("vagina and anal penetration, double penetration")

    # Игрушки
    if "dildo" in features: additions.append("dildo, large dildo, inserted dildo, detailed dildo")
    if "anal_beads" in features: additions.append("anal beads")
    if "anal_plug" in features: additions.append("anal plug, butt plug")
    if "gag" in features: additions.append("mouth gag, klyap")

    # Пози
    if "doggy" in features: additions.append("doggy style, from behind")
    if "standing" in features: additions.append("standing pose")
    if "splits" in features: additions.append("vertical split, flexibility, splits")
    if "squat" in features: additions.append("squatting, legs open, sitting on heels")
    if "lying" in features: additions.append("lying down, relaxed pose")

    # Одежда
    if "stockings" in features: additions.append("thigh high stockings, sexy lingerie")
    if "bikini" in features: additions.append("bikini swimsuit")
    if "mask" in features: additions.append("face mask")
    if "heels" in features: additions.append("high heels shoes")
    if "shibari" in features: additions.append("shibari, japanese rope bondage, intricate rope patterns, body bondage")
    if "cow_costume" in features: additions.append("cow costume, cow horns, cow tail, cow stockings, cute cow outfit")
    if "bikini_tan_lines" in features: additions.append("bikini tan lines, sharp and distinct tan lines in the shape of a bikini, sun-kissed skin with clear swimsuit outline")

    # Дополнительные
    if "big_breasts" in features: additions.append("large breasts, full chest")
    if "small_breasts" in features: additions.append("small breasts")
    if "piercing" in features: additions.append("nipple piercing, body piercing")
    if "femboy" in features: additions.append("femboy, feminine male, smooth skin, slim waist, erotic pose")
    if "ethnicity_asian" in features: additions.append("asian girl, asian features")
    if "ethnicity_european" in features: additions.append("european girl, european face")
    if "ethnicity_furry" in features: additions.append("furry, anthropomorphic animal, anthropomorphic features")
    if "skin_white" in features: additions.append("pale skin, light skin tone")
    if "skin_black" in features: additions.append("dark skin, black skin tone")

    additions.append("nsfw, masterpiece, ultra-detailed, high resolution")

    prompt = base
    if additions:
        prompt += ", " + ", ".join(additions)
    return prompt

# ===== Генерация изображения =====
def generate_image(prompt, model_version):
    url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {REPLICATE_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "version": model_version,
        "input": {"prompt": prompt}
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        return response.json()["urls"]["get"], None
    return None, f"❌ Ошибка генерации: {response.status_code} {response.text}"

def wait_for_image(status_url):
    for _ in range(40):  # Ждем до ~80 сек (40*2)
        time.sleep(2)
        res = requests.get(status_url, headers={"Authorization": f"Token {REPLICATE_TOKEN}"})
        if res.status_code != 200:
            return None
        data = res.json()
        if data.get("status") == "succeeded":
            output = data.get("output")
            if isinstance(output, list):
                return output[0]
            return output
        if data.get("status") == "failed":
            return None
    return None

# ===== Обработчики команд =====
@bot.message_handler(commands=["start"])
def start(message):
    cid = message.chat.id
    user_settings[cid] = {"features": [], "model": "anime", "waiting_for_prompt": False}
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🎨 Выбрать модель", callback_data="model"),
        types.InlineKeyboardButton("🧩 Выбрать теги", callback_data="tags"),
        types.InlineKeyboardButton("✅ Генерировать", callback_data="generate")
    )
    bot.send_message(cid, "Привет! Выбери действие:", reply_markup=markup)

# ===== Обработчик callback =====
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    cid = call.message.chat.id
    data = call.data

    if cid not in user_settings:
        user_settings[cid] = {"features": [], "model": "anime", "waiting_for_prompt": False}

    if data == "model":
        bot.edit_message_text("Выбери модель:", cid, call.message.message_id, reply_markup=model_keyboard())

    elif data.startswith("model_"):
        model = data.split("_")[1]
        user_settings[cid]["model"] = model
        bot.answer_callback_query(call.id, f"Модель установлена: {model}")
        bot.edit_message_text(f"Модель установлена: {model}", cid, call.message.message_id, reply_markup=main_keyboard())

    elif data == "tags":
        user_settings[cid]["waiting_for_prompt"] = False
        bot.edit_message_text("Выбери категорию тегов:", cid, call.message.message_id, reply_markup=category_keyboard())

    elif data.startswith("cat_"):
        category = data[4:]
        bot.edit_message_text(f"Выбери теги категории {CATEGORY_NAMES_EMOJI.get(category, category)}:", cid, call.message.message_id, reply_markup=tags_keyboard(category))

    elif data.startswith("tag_"):
        tag = data[4:]
        features = user_settings[cid].get("features", [])
        if tag in features:
            features.remove(tag)
        else:
            features.append(tag)
        user_settings[cid]["features"] = features
        status = "добавлен" if tag in features else "убран"
        display_name = (
            CLOTHES_NAMES_EMOJI.get(tag) or
            TAG_NAMES_EMOJI.get("holes", {}).get(tag) or
            TAG_NAMES_EMOJI.get("toys", {}).get(tag) or
            TAG_NAMES_EMOJI.get("poses", {}).get(tag) or
            TAG_NAMES_EMOJI.get("extras", {}).get(tag) or
            tag.replace("_", " ").capitalize()
        )
        bot.answer_callback_query(call.id, f"{display_name} {status}")

    elif data == "tags_done":
        tags = user_settings[cid].get("features", [])
        if tags:
            tags_str = []
            for t in tags:
                name = (
                    CLOTHES_NAMES_EMOJI.get(t) or
                    TAG_NAMES_EMOJI.get("holes", {}).get(t) or
                    TAG_NAMES_EMOJI.get("toys", {}).get(t) or
                    TAG_NAMES_EMOJI.get("poses", {}).get(t) or
                    TAG_NAMES_EMOJI.get("extras", {}).get(t) or
                    t.replace("_", " ").capitalize()
                )
                tags_str.append(name)
            bot.edit_message_text(f"Выбраны теги: {', '.join(tags_str)}", cid, call.message.message_id, reply_markup=main_keyboard())
        else:
            bot.edit_message_text("Выбраны теги: нет", cid, call.message.message_id, reply_markup=main_keyboard())

    elif data == "tags_back":
        bot.edit_message_text("Выбери категорию тегов:", cid, call.message.message_id, reply_markup=category_keyboard())

    elif data == "generate":
        user_settings[cid]["waiting_for_prompt"] = True
        bot.send_message(cid, "📝 Напиши описание картинки (например: 'обнажённая женщина, сексуальная поза'):")

    elif data == "main_menu":
        bot.edit_message_text("Привет! Выбери действие:", cid, call.message.message_id, reply_markup=main_keyboard())

# ===== Приём текста после генерации =====
@bot.message_handler(func=lambda m: user_settings.get(m.chat.id, {}).get("waiting_for_prompt", False))
def handle_prompt(message):
    cid = message.chat.id
    base_prompt = message.text
    user_settings[cid]["waiting_for_prompt"] = False
    features = user_settings[cid].get("features", [])
    model_id = user_settings[cid].get("model", "anime")
    model_version = REPLICATE_MODELS.get(model_id, REPLICATE_MODELS["anime"])

    prompt = build_prompt(base_prompt, features)
    bot.send_message(cid, f"🎨 Модель: {model_id}\n📸 Генерация изображения...")

    status_url, error = generate_image(prompt, model_version)
    if error:
        bot.send_message(cid, error)
        return

    image_url = wait_for_image(status_url)
    if image_url:
        bot.send_photo(cid, image_url)
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🧩 Выбрать теги", callback_data="tags"),
            types.InlineKeyboardButton("🎨 Выбрать модель", callback_data="model"),
            types.InlineKeyboardButton("✅ Новая генерация", callback_data="generate")
        )
        bot.send_message(cid, "Выбери дальнейшее действие:", reply_markup=markup)
    else:
        bot.send_message(cid, "❌ Ошибка генерации изображения.")

# ===== Вспомогательные клавиатуры =====
def model_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🖌 Аниме", callback_data="model_anime"),
        types.InlineKeyboardButton("📷 Реализм", callback_data="model_realism"),
        types.InlineKeyboardButton("🧱 3D", callback_data="model_3d"),
        types.InlineKeyboardButton("⬅ Назад", callback_data="main_menu")
    )
    return markup

def main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.In