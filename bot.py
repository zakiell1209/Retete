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
    "poses": ["doggy", "standing", "splits", "squat", "lying"],
    "clothes": ["stockings", "bikini", "mask", "heels", "shibari", "cow_costume", "bikini_tan_lines"],
    "body": ["big_breasts", "small_breasts", "skin_black", "skin_white"],
    "ethnicity": ["femboy", "ethnicity_asian", "ethnicity_european"],
    "furry": ["furry_cow", "furry_cat", "furry_dog", "furry_dragon", "furry_silveon"]
}

CATEGORY_NAMES_EMOJI = {
    "holes": "Отверстия 🕳️", "toys": "Игрушки 🧸", "poses": "Позиции 🤸‍♀️",
    "clothes": "Одежда 👗", "body": "Тело 💪", "ethnicity": "Этнос 🌍", "furry": "Фури 🐾"
}

TAG_NAMES_EMOJI = {
    "holes": {"vagina": "Вагина ♀️", "anal": "Анал 🍑", "both": "Оба 🔥"},
    "toys": {"dildo": "Дилдо 🍆", "anal_beads": "Анальные бусы 🔴", "anal_plug": "Пробка 🔵", "gag": "Кляп 😶", "piercing": "Пирсинг 💎"},
    "poses": {"doggy": "Догги 🐕", "standing": "Стоя 🧍", "splits": "Шпагат 🤸", "squat": "Присед 🧎", "lying": "Лежа 🛌"},
    "clothes": {"stockings": "Чулки 🧦", "bikini": "Бикини 👙", "mask": "Маска 😷", "heels": "Туфли 👠", "shibari": "Шибари ⛓️", "cow_costume": "Костюм коровы 🐄", "bikini_tan_lines": "Загар от бикини ☀️"},
    "body": {"big_breasts": "Большая грудь 🍒", "small_breasts": "Маленькая грудь 🥥", "skin_black": "Чёрная кожа ⚫", "skin_white": "Белая кожа ⚪"},
    "ethnicity": {"femboy": "Фембой ⚧", "ethnicity_asian": "Азиатка 🈶", "ethnicity_european": "Европейка 🇪🇺"},
    "furry": {"furry_cow": "Фури корова 🐄", "furry_cat": "Фури кошка 🐱", "furry_dog": "Фури собака 🐶", "furry_dragon": "Фури дракон 🐉", "furry_silveon": "Фури сильвеон 🦄"}
}

def main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🎨 Модель", callback_data="model"),
        types.InlineKeyboardButton("🧩 Теги", callback_data="tags"),
        types.InlineKeyboardButton("✅ Генерация", callback_data="generate")
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
        emoji_name = TAG_NAMES_EMOJI.get(category, {}).get(tag, tag)
        check = " ✅" if tag in selected_tags else ""
        markup.add(types.InlineKeyboardButton(emoji_name + check, callback_data=f"tag_{tag}"))
    markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="tags_back"))
    return markup

@bot.message_handler(commands=["start"])
def start(message):
    cid = message.chat.id
    user_settings[cid] = {"features": [], "model": "anime", "waiting": False, "category": None}
    bot.send_message(cid, "Привет! Выбери действие:", reply_markup=main_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    cid = call.message.chat.id
    data = call.data
    if cid not in user_settings:
        user_settings[cid] = {"features": [], "model": "anime", "waiting": False, "category": None}

    if data == "model":
        bot.edit_message_text("Выбери модель:", cid, call.message.message_id, reply_markup=model_keyboard())
    elif data.startswith("model_"):
        user_settings[cid]["model"] = data.split("_")[1]
        bot.edit_message_text("Модель выбрана ✅", cid, call.message.message_id, reply_markup=main_keyboard())
    elif data == "tags":
        bot.edit_message_text("Выбери категорию:", cid, call.message.message_id, reply_markup=category_keyboard())
    elif data.startswith("cat_"):
        cat = data.split("_", 1)[1]
        user_settings[cid]["category"] = cat
        bot.edit_message_text(f"Выбери теги {CATEGORY_NAMES_EMOJI[cat]}:", cid, call.message.message_id, reply_markup=tags_keyboard(cat, user_settings[cid]["features"]))
    elif data.startswith("tag_"):
        tag = data.split("_", 1)[1]
        tags = user_settings[cid]["features"]
        if tag in tags:
            tags.remove(tag)
        else:
            tags.append(tag)
        cat = user_settings[cid].get("category")
        if cat:
            bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=tags_keyboard(cat, tags))
    elif data == "tags_done" or data == "tags_back":
        bot.edit_message_text("Категории тегов:", cid, call.message.message_id, reply_markup=category_keyboard())
    elif data == "generate":
        user_settings[cid]["waiting"] = True
        bot.send_message(cid, "✏️ Введи описание сцены:")
    elif data.startswith("after_"):
        option = data.split("_", 1)[1]
        if option == "continue":
            user_settings[cid]["waiting"] = True
            bot.send_message(cid, "✏️ Введи новое описание сцены:")
        elif option == "edit":
            bot.send_message(cid, "Категории тегов:", reply_markup=category_keyboard())
        elif option == "reset":
            user_settings[cid]["features"] = []
            bot.send_message(cid, "Выбери категории заново:", reply_markup=category_keyboard())
        else:
            bot.send_message(cid, "Главное меню:", reply_markup=main_keyboard())
    elif data == "main_menu":
        bot.edit_message_text("Выбери действие:", cid, call.message.message_id, reply_markup=main_keyboard())

@bot.message_handler(func=lambda m: user_settings.get(m.chat.id, {}).get("waiting"))
def handle_prompt(message):
    cid = message.chat.id
    user_settings[cid]["waiting"] = False
    base = message.text
    features = user_settings[cid]["features"]
    model_key = user_settings[cid]["model"]
    model_id = REPLICATE_MODELS.get(model_key, REPLICATE_MODELS["anime"])
    prompt = build_prompt(base, features)

    bot.send_message(cid, "⏳ Генерация изображения...")
    status_url, err = generate_image(prompt, model_id)
    if err:
        bot.send_message(cid, err)
        return

    image_url = wait_for_image(status_url)
    if image_url:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("🔁 Продолжить", callback_data="after_continue"),
            types.InlineKeyboardButton("✏️ Редактировать теги", callback_data="after_edit"),
            types.InlineKeyboardButton("🗑 Сбросить теги", callback_data="after_reset")
        )
        bot.send_photo(cid, image_url, caption="Готово! Что дальше?", reply_markup=markup)
    else:
        bot.send_message(cid, "❌ Не удалось сгенерировать изображение.")

def build_prompt(base, tags):
    mapping = {
        "vagina": "vaginal penetration", "anal": "anal penetration", "both": "double penetration",
        "dildo": "dildo", "anal_beads": "anal beads", "anal_plug": "anal plug", "gag": "gag", "piercing": "body piercing",
        "doggy": "doggy style", "standing": "standing pose", "splits": "splits", "squat": "squatting", "lying": "laying",
        "stockings": "stockings", "bikini": "bikini", "mask": "mask", "heels": "high heels", "shibari": "shibari",
        "cow_costume": "cow costume", "bikini_tan_lines": "bikini tan lines",
        "big_breasts": "large breasts", "small_breasts": "small breasts", "skin_black": "black skin", "skin_white": "white skin",
        "femboy": "femboy", "ethnicity_asian": "asian girl", "ethnicity_european": "european girl",
        "furry_cow": "furry cow", "furry_cat": "furry cat", "furry_dog": "furry dog", "furry_dragon": "furry dragon", "furry_silveon": "furry silveon"
    }
    return base + ", " + ", ".join(mapping.get(t, t) for t in tags) + ", nsfw, masterpiece, ultra detailed"

def generate_image(prompt, model_version):
    url = "https://api.replicate.com/v1/predictions"
    headers = {"Authorization": f"Token {REPLICATE_TOKEN}", "Content-Type": "application/json"}
    data = {"version": model_version, "input": {"prompt": prompt}}
    r = requests.post(url, headers=headers, json=data)
    if r.status_code == 201:
        return r.json()["urls"]["get"], None
    return None, "⚠️ Ошибка генерации"

def wait_for_image(status_url):
    headers = {"Authorization": f"Token {REPLICATE_TOKEN}"}
    for _ in range(40):
        time.sleep(2)
        r = requests.get(status_url, headers=headers)
        if r.status_code == 200:
            data = r.json()
            if data["status"] == "succeeded":
                return data["output"][0] if isinstance(data["output"], list) else data["output"]
            if data["status"] == "failed":
                break
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