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

# ==== ВСЕ ТЕГИ ====
TAGS = {
    "holes": ["vagina", "anal", "both"],
    "toys": ["dildo", "anal_beads", "anal_plug", "gag", "piercing"],
    "poses": ["doggy", "standing", "splits", "squat", "lying"],
    "clothes": ["stockings", "bikini", "mask", "heels", "shibari", "cow_costume", "bikini_tan_lines"],
    "body": ["big_breasts", "small_breasts", "skin_black", "skin_white", "loli", "milf", "age_21", "slim", "muscular", "curvy", "normal"],
    "ethnicity": ["femboy", "ethnicity_asian", "ethnicity_european"],
    "furry": ["furry_cow", "furry_cat", "furry_dog", "furry_dragon", "furry_silveon"]
}

CATEGORY_NAMES_EMOJI = {
    "holes": "Отверстия 🕳️",
    "toys": "Игрушки 🧸",
    "poses": "Позиции 🤸‍♀️",
    "clothes": "Одежда 👗",
    "body": "Тело 💪",
    "ethnicity": "Этнос 🌍",
    "furry": "Фури 🐾"
}

TAG_NAMES_EMOJI = {
    "holes": {"vagina": "Вагина ♀️", "anal": "Анал 🍑", "both": "Оба 🔥"},
    "toys": {"dildo": "Дилдо 🍆", "anal_beads": "Анальные бусы 🔴", "anal_plug": "Пробка 🔵", "gag": "Кляп 😶", "piercing": "Пирсинг 💎"},
    "poses": {"doggy": "Догги 🐕", "standing": "Стоя 🧍", "splits": "Шпагат 🤸", "squat": "Присед 🧎", "lying": "Лежа 🛌"},
    "clothes": {
        "stockings": "Чулки 🧦", "bikini": "Бикини 👙", "mask": "Маска 😷", "heels": "Туфли 👠",
        "shibari": "Шибари ⛓️", "cow_costume": "Костюм коровы 🐄", "bikini_tan_lines": "Загар от бикини ☀️"
    },
    "body": {
        "big_breasts": "Большая грудь 🍒", "small_breasts": "Маленькая грудь 🥥",
        "skin_black": "Чёрная кожа ⚫", "skin_white": "Белая кожа ⚪",
        "loli": "Лоли 👧", "milf": "Милфа 👩", "age_21": "21 год 🎂",
        "slim": "Худое 🦴", "muscular": "Накачанное 💪", "curvy": "Пышное 🍑", "normal": "Нормальное 🚶"
    },
    "ethnicity": {
        "femboy": "Фембой ⚧", "ethnicity_asian": "Азиатка 🈶", "ethnicity_european": "Европейка 🇪🇺"
    },
    "furry": {
        "furry_cow": "Фури корова 🐄", "furry_cat": "Фури кошка 🐱", "furry_dog": "Фури собака 🐶",
        "furry_dragon": "Фури дракон 🐉", "furry_silveon": "Фури сильвеон 🦄"
    }
}

# ==== КЛАВИАТУРЫ ====
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

def tags_keyboard(category, selected_tags):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for tag in TAGS.get(category, []):
        name = TAG_NAMES_EMOJI.get(category, {}).get(tag, tag)
        if tag in selected_tags:
            name += " ✅"
        markup.add(types.InlineKeyboardButton(name, callback_data=f"tag_{category}_{tag}"))
    markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="tags_back"))
    return markup

def post_generation_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🔁 Продолжить с теми же тегами", callback_data="generate"),
               types.InlineKeyboardButton("✏️ Редактировать выбранные теги", callback_data="tags"),
               types.InlineKeyboardButton("🧹 Сбросить и начать заново", callback_data="start_over"))
    return markup

# ==== ОБРАБОТКА ====
@bot.message_handler(commands=["start"])
def start(message):
    cid = message.chat.id
    user_settings[cid] = {"features": [], "model": "anime", "waiting_for_prompt": False}
    bot.send_message(cid, "Привет! Выбери действие:", reply_markup=main_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    cid = call.message.chat.id
    data = call.data
    settings = user_settings.setdefault(cid, {"features": [], "model": "anime", "waiting_for_prompt": False})

    if data == "model":
        bot.edit_message_text("Выбери модель:", cid, call.message.message_id, reply_markup=model_keyboard())
    elif data.startswith("model_"):
        model = data.split("_")[1]
        settings["model"] = model
        bot.edit_message_text(f"Модель установлена: {model}", cid, call.message.message_id, reply_markup=main_keyboard())
    elif data == "tags":
        bot.edit_message_text("Выбери категорию:", cid, call.message.message_id, reply_markup=category_keyboard())
    elif data.startswith("cat_"):
        cat = data.split("_")[1]
        settings["current_cat"] = cat
        bot.edit_message_text(f"Выбери теги категории {CATEGORY_NAMES_EMOJI[cat]}:", cid, call.message.message_id,
                              reply_markup=tags_keyboard(cat, settings["features"]))
    elif data.startswith("tag_"):
        _, category, tag = data.split("_", 2)
        if tag in settings["features"]:
            settings["features"].remove(tag)
        else:
            settings["features"].append(tag)
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=tags_keyboard(category, settings["features"]))
    elif data == "tags_done":
        bot.edit_message_text("Теги сохранены.", cid, call.message.message_id, reply_markup=main_keyboard())
    elif data == "tags_back":
        bot.edit_message_text("Выбери категорию:", cid, call.message.message_id, reply_markup=category_keyboard())
    elif data == "generate":
        settings["waiting_for_prompt"] = True
        bot.send_message(cid, "✏️ Введи описание картинки:")
    elif data == "start_over":
        user_settings[cid] = {"features": [], "model": "anime", "waiting_for_prompt": False}
        bot.send_message(cid, "Начни сначала:", reply_markup=main_keyboard())

@bot.message_handler(func=lambda m: user_settings.get(m.chat.id, {}).get("waiting_for_prompt"))
def handle_prompt(message):
    cid = message.chat.id
    settings = user_settings[cid]
    settings["waiting_for_prompt"] = False

    base = message.text
    features = settings["features"]
    model_key = settings["model"]
    model_id = REPLICATE_MODELS.get(model_key, REPLICATE_MODELS["anime"])
    full_prompt = build_prompt(base, features)

    bot.send_message(cid, "⏳ Генерация изображения...")
    status_url, err = generate_image(full_prompt, model_id)
    if err:
        bot.send_message(cid, err)
        return

    image_url = wait_for_image(status_url)
    if image_url:
        bot.send_photo(cid, image_url, caption="Вот результат!", reply_markup=post_generation_keyboard())
    else:
        bot.send_message(cid, "❌ Ошибка генерации изображения.")

# ==== ПРОМТ ====
def build_prompt(base, tags):
    additions = {
        "vagina": "vaginal penetration", "anal": "anal penetration", "both": "double penetration",
        "dildo": "dildo", "anal_beads": "anal beads", "anal_plug": "anal plug",
        "gag": "gag", "piercing": "body piercing",
        "doggy": "doggy style", "standing": "standing pose", "splits": "doing the splits",
        "squat": "squatting pose", "lying": "lying on back",
        "stockings": "wearing stockings", "bikini": "bikini",
        "mask": "face mask", "heels": "high heels", "shibari": "bondage shibari",
        "cow_costume": "girl in cow-patterned stockings, horns, tail, no underwear",
        "bikini_tan_lines": "tanned skin with pale bikini tan lines",
        "big_breasts": "large breasts", "small_breasts": "small breasts",
        "skin_black": "dark-skinned", "skin_white": "pale skin",
        "femboy": "femboy", "ethnicity_asian": "asian girl", "ethnicity_european": "european girl",
        "furry_cow": "anthro cow girl", "furry_cat": "anthro cat girl", "furry_dog": "anthro dog girl",
        "furry_dragon": "anthro dragon girl",
        "furry_silveon": "anthropomorphic silveon, detailed, anime style, pink and blue ribbons, big eyes",
        "loli": "young girl, small body", "milf": "mature woman, curvy body",
        "age_21": "21 years old female", "slim": "slim figure", "muscular": "muscular body",
        "curvy": "curvy figure", "normal": "average build"
    }

    prompt = base
    for tag in tags:
        if tag in additions:
            prompt += ", " + additions[tag]
    prompt += ", nsfw, masterpiece, ultra detailed"
    return prompt

# ==== ГЕНЕРАЦИЯ ====
def generate_image(prompt, model_version):
    url = "https://api.replicate.com/v1/predictions"
    headers = {"Authorization": f"Token {REPLICATE_TOKEN}", "Content-Type": "application/json"}
    data = {"version": model_version, "input": {"prompt": prompt}}
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        return response.json()["urls"]["get"], None
    return None, "Ошибка запуска генерации"

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

# ==== ВЕБХУК ====
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