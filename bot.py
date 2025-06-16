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

REPLICATE_MODELS = {
    "anime": "c1d5b02687df6081c7953c74bcc527858702e8c153c9382012ccc3906752d3ec",
    "realism": "stability-ai/stable-diffusion:ac732df8",
    "3d": "stability-ai/stable-diffusion-3-medium"
}

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
user_settings = {}

TAGS = {
    "holes": ["vagina", "anal", "both"],
    "toys": ["dildo", "anal_beads", "anal_plug", "gag", "piercing"],
    "poses": [
        "doggy", "standing", "splits", "squat", "lying",
        "split_horizontal", "split_vertical", "side_leg_up",
        "front_facing", "back_facing", "laying_spread_knees"
    ],
    "clothes": ["stockings", "bikini", "mask", "heels", "shibari", "cow_costume", "bikini_tan_lines"],
    "body": [
        "big_breasts", "small_breasts", "skin_white", "skin_black",
        "chubby", "slim", "fit", "muscular", "short", "tall",
        "loli", "milf", "middle_age"
    ],
    "ethnos": ["femboy", "futanari", "ethnicity_asian", "ethnicity_european"],
    "furry": ["furry_cow", "furry_cat", "furry_dog", "furry_dragon", "furry_sylveon"]
}

CATEGORY_NAMES_EMOJI = {
    "holes": "Отверстия 🕳️",
    "toys": "Игрушки 🧸",
    "poses": "Позиции 🤸‍♀️",
    "clothes": "Одежда 👗",
    "body": "Тело 🧍‍♀️",
    "ethnos": "Этнос 🌍",
    "furry": "Фури 🐾"
}

CLOTHES_NAMES_EMOJI = {
    "stockings": "Чулки 🧦", "bikini": "Бикини 👙", "mask": "Маска 😷", "heels": "Туфли 👠",
    "shibari": "Шибари ⛓️", "cow_costume": "Костюм коровы 🐄", "bikini_tan_lines": "Загар от бикини ☀️"
}

TAG_NAMES_EMOJI = {
    "holes": {"vagina": "Вагина ♀️", "anal": "Анал 🍑", "both": "Оба 🔥"},
    "toys": {"dildo": "Дилдо 🍆", "anal_beads": "Анальные бусы 🔴", "anal_plug": "Пробка 🔵", "gag": "Кляп 😶", "piercing": "Пирсинг 💎"},
    "poses": {
        "doggy": "Догги 🐕", "standing": "Стоя 🧍", "splits": "Шпагат 🤸", "squat": "Присед 🧎", "lying": "Лежа 🛌",
        "split_horizontal": "Горизонтальный шпагат ↔️", "split_vertical": "Вертикальный шпагат ↕️",
        "side_leg_up": "На боку с ногой вверх 🦵", "front_facing": "Лицом к зрителю 👁", "back_facing": "Спиной к зрителю 🔙",
        "laying_spread_knees": "На спине, ноги врозь ⛓️"
    },
    "body": {
        "big_breasts": "Большая грудь 🍒", "small_breasts": "Маленькая грудь 🥥",
        "skin_white": "Белая кожа ⚪", "skin_black": "Чёрная кожа ⚫",
        "chubby": "Пышное тело 🍑", "slim": "Худое тело 🧘", "fit": "Подтянутое тело 💃",
        "muscular": "Накачанное тело 💪", "short": "Низкий рост 📏", "tall": "Высокий рост 📐",
        "loli": "Лоли 👧", "milf": "Милфа 👩", "middle_age": "Средний возраст 👩‍🦳"
    },
    "ethnos": {
        "femboy": "Фембой ⚧", "futanari": "Футанари 🔞",
        "ethnicity_asian": "Азиатка 🈶", "ethnicity_european": "Европейка 🇪🇺"
    },
    "furry": {
        "furry_cow": "Фури-корова 🐄", "furry_cat": "Фури-кошка 🐱", "furry_dog": "Фури-собака 🐶",
        "furry_dragon": "Фури-дракон 🐉", "furry_sylveon": "Фури-сильвеон 🎀"
    }
}

def main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🎨 Выбрать модель", callback_data="model"),
        types.InlineKeyboardButton("🧩 Выбрать теги", callback_data="tags"),
        types.InlineKeyboardButton("✅ Генерировать", callback_data="generate")
    )
    return markup

def model_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🖌 Аниме", callback_data="model_anime"),
        types.InlineKeyboardButton("📷 Реализм", callback_data="model_realism"),
        types.InlineKeyboardButton("🧱 3D", callback_data="model_3d"),
        types.InlineKeyboardButton("⬅ Назад", callback_data="main_menu")
    )
    return markup

def category_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    for cat in CATEGORY_NAMES_EMOJI:
        markup.add(types.InlineKeyboardButton(CATEGORY_NAMES_EMOJI[cat], callback_data=f"cat_{cat}"))
    markup.add(types.InlineKeyboardButton("✅ Готово", callback_data="tags_done"))
    return markup

def tags_keyboard(category):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for tag in TAGS.get(category, []):
        name = CLOTHES_NAMES_EMOJI.get(tag, TAG_NAMES_EMOJI.get(category, {}).get(tag, tag))
        markup.add(types.InlineKeyboardButton(name, callback_data=f"tag_{tag}"))
    markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="tags_back"))
    return markup

@bot.message_handler(commands=["start"])
def start(message):
    cid = message.chat.id
    user_settings[cid] = {"features": [], "model": "anime", "waiting_for_prompt": False}
    bot.send_message(cid, "Привет! Выбери действие:", reply_markup=main_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    cid = call.message.chat.id
    data = call.data
    if cid not in user_settings:
        user_settings[cid] = {"features": [], "model": "anime", "waiting_for_prompt": False}

    if data == "model":
        bot.edit_message_text("Выбери модель:", cid, call.message.message_id, reply_markup=model_keyboard())
    elif data.startswith("model_"):
        model = data.split("_")[1]
        user_settings[cid]["model"] = model
        bot.edit_message_text(f"Модель установлена: {model}", cid, call.message.message_id, reply_markup=main_keyboard())
    elif data == "tags":
        bot.edit_message_text("Выбери категорию:", cid, call.message.message_id, reply_markup=category_keyboard())
    elif data.startswith("cat_"):
        cat = data.split("_")[1]
        bot.edit_message_text(f"Выбери теги категории {CATEGORY_NAMES_EMOJI[cat]}:", cid, call.message.message_id, reply_markup=tags_keyboard(cat))
    elif data.startswith("tag_"):
        tag = data.split("_")[1]
        tags = user_settings[cid]["features"]
        if tag in tags:
            tags.remove(tag)
        else:
            tags.append(tag)
        user_settings[cid]["features"] = tags
        bot.answer_callback_query(call.id, f"{tag} выбрано")
    elif data == "tags_done":
        bot.edit_message_text("Теги сохранены.", cid, call.message.message_id, reply_markup=main_keyboard())
    elif data == "tags_back":
        bot.edit_message_text("Выбери категорию:", cid, call.message.message_id, reply_markup=category_keyboard())
    elif data == "generate":
        user_settings[cid]["waiting_for_prompt"] = True
        bot.send_message(cid, "✏️ Введи описание картинки:")

@bot.message_handler(func=lambda m: user_settings.get(m.chat.id, {}).get("waiting_for_prompt"))
def handle_prompt(message):
    cid = message.chat.id
    user_settings[cid]["waiting_for_prompt"] = False
    base = message.text
    features = user_settings[cid]["features"]
    model_key = user_settings[cid]["model"]
    model_id = REPLICATE_MODELS.get(model_key, REPLICATE_MODELS["anime"])
    full_prompt = build_prompt(base, features)

    bot.send_message(cid, "⏳ Генерация изображения...")
    status_url, err = generate_image(full_prompt, model_id)
    if err:
        bot.send_message(cid, err)
        return

    image_url = wait_for_image(status_url)
    if image_url:
        bot.send_photo(cid, image_url, caption="Вот результат!", reply_markup=main_keyboard())
    else:
        bot.send_message(cid, "❌ Ошибка генерации изображения.")

def build_prompt(base, tags):
    map_tag = {
        "vagina": "vaginal penetration", "anal": "anal penetration", "both": "double penetration",
        "dildo": "dildo", "anal_beads": "anal beads", "anal_plug": "anal plug", "gag": "gag", "piercing": "body piercing",
        "doggy": "doggy style", "standing": "standing pose", "splits": "splits", "squat": "squatting", "lying": "laying",
        "split_horizontal": "horizontal split", "split_vertical": "vertical split", "side_leg_up": "laying on side with one leg up",
        "front_facing": "facing viewer", "back_facing": "back facing viewer", "laying_spread_knees": "laying on back, knees bent and spread",
        "stockings": "stockings", "bikini": "bikini", "mask": "mask", "heels": "high heels", "shibari": "shibari",
        "cow_costume": "cow costume", "bikini_tan_lines": "bikini tan lines",
        "big_breasts": "large breasts", "small_breasts": "small breasts", "skin_white": "white skin", "skin_black": "black skin",
        "femboy": "femboy", "futanari": "futanari", "ethnicity_asian": "asian girl", "ethnicity_european": "european girl",
        "chubby": "chubby body", "slim": "slim body", "fit": "fit body", "muscular": "muscular body",
        "short": "short girl", "tall": "tall girl", "loli": "young girl", "milf": "mature woman", "middle_age": "middle-aged woman",
        "furry_cow": "furry cow", "furry_cat": "furry cat", "furry_dog": "furry dog", "furry_dragon": "furry dragon", "furry_sylveon": "furry sylveon"
    }
    details = [map_tag.get(t, t) for t in tags]
    return base + ", " + ", ".join(details + ["nsfw, masterpiece, ultra detailed"])

def generate_image(prompt, model_version):
    url = "https://api.replicate.com/v1/predictions"
    headers = {"Authorization": f"Token {REPLICATE_TOKEN}", "Content-Type": "application/json"}
    data = {"version": model_version, "input": {"prompt": prompt}}
    res = requests.post(url, headers=headers, json=data)
    if res.status_code == 201:
        return res.json()["urls"]["get"], None
    return None, "Ошибка генерации"

def wait_for_image(status_url):
    headers = {"Authorization": f"Token {REPLICATE_TOKEN}"}
    for _ in range(40):
        time.sleep(2)
        res = requests.get(status_url, headers=headers)
        if res.status_code == 200:
            data = res.json()
            if data["status"] == "succeeded":
                return data["output"][0] if isinstance(data["output"], list) else data["output"]
            elif data["status"] == "failed":
                return None
    return None

@app.route("/", methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "OK", 200

@app.route("/", methods=["GET"])
def index():
    return "Бот работает", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=PORT)