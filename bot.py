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
    "poses": [
        "doggy", "standing", "splits", "squat", "lying",
        "hor_split", "ver_split", "side_up_leg", "front_facing", "back_facing", "lying_knees_up"
    ],
    "clothes": ["stockings", "bikini", "mask", "heels", "shibari", "cow_costume", "bikini_tan_lines"],
    "body": [
        "big_breasts", "small_breasts", "skin_white", "skin_black",
        "body_fat", "body_thin", "body_fit", "body_muscular",
        "height_tall", "height_short", "age_loli", "age_milf", "age_middle"
    ],
    "ethnos": ["futanari", "femboy", "ethnicity_asian", "ethnicity_european"],
    "furry": ["furry_cow", "furry_cat", "furry_dog", "furry_dragon", "furry_sylveon"]
}

CATEGORY_NAMES_EMOJI = {
    "holes": "Отверстия 🕳️",
    "toys": "Игрушки 🧸",
    "poses": "Позиции 🤸‍♀️",
    "clothes": "Одежда 👗",
    "body": "Тело 🧍",
    "ethnos": "Этнос 🌍",
    "furry": "Фури 🐾"
}

TAG_NAMES_EMOJI = {
    "holes": {"vagina": "Вагина ♀️", "anal": "Анал 🍑", "both": "Оба 🔥"},
    "toys": {
        "dildo": "Дилдо 🍆", "anal_beads": "Анальные бусы 🔴",
        "anal_plug": "Пробка 🔵", "gag": "Кляп 😶", "piercing": "Пирсинг 💎"
    },
    "poses": {
        "doggy": "Догги 🐕", "standing": "Стоя 🧍", "splits": "Шпагат 🤸",
        "squat": "Присед 🧎", "lying": "Лежа 🛌", "hor_split": "Гор. шпагат ↔️",
        "ver_split": "Вер. шпагат ↕️", "side_up_leg": "На боку с ногой 🔝",
        "front_facing": "Лицом 👁", "back_facing": "Спиной 🍑", "lying_knees_up": "Лёжа, колени вверх 🧷"
    },
    "clothes": {
        "stockings": "Чулки 🧦", "bikini": "Бикини 👙", "mask": "Маска 😷",
        "heels": "Туфли 👠", "shibari": "Шибари ⛓️", "cow_costume": "Коровка 🐄",
        "bikini_tan_lines": "Загар от бикини ☀️"
    },
    "body": {
        "big_breasts": "Большая грудь 🍒", "small_breasts": "Маленькая грудь 🥥",
        "skin_white": "Белая кожа ⚪", "skin_black": "Чёрная кожа ⚫",
        "body_fat": "Пышное тело 🍰", "body_thin": "Худое тело 🪶",
        "body_fit": "Подтянутое тело 🏃", "body_muscular": "Накачанное тело 💪",
        "height_tall": "Высокая 📏", "height_short": "Низкая 📐",
        "age_loli": "Лоли 👧", "age_milf": "Милфа 💋", "age_middle": "Средний возраст 👩"
    },
    "ethnos": {
        "futanari": "Футанари 🍆", "femboy": "Фембой ⚧",
        "ethnicity_asian": "Азиатка 🈶", "ethnicity_european": "Европейка 🇪🇺"
    },
    "furry": {
        "furry_cow": "Фури-Коровка 🐄", "furry_cat": "Фури-Кошка 🐱",
        "furry_dog": "Фури-Собака 🐶", "furry_dragon": "Фури-Дракон 🐉", "furry_sylveon": "Фури-Сильвеон 🎀"
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

def tags_keyboard(category, cid=None):
    markup = types.InlineKeyboardMarkup(row_width=2)
    selected = user_settings.get(cid, {}).get("features", []) if cid else []
    for tag in TAGS.get(category, []):
        name = TAG_NAMES_EMOJI.get(category, {}).get(tag, tag)
        if tag in selected:
            name = f"✅ {name}"
        markup.add(types.InlineKeyboardButton(name, callback_data=f"tag_{tag}"))
    markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="tags_back"))
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
    if cid not in user_settings:
        user_settings[cid] = {"features": [], "model": "anime", "waiting_for_prompt": False}

    if data == "model":
        bot.edit_message_text("Выбери модель:", cid, call.message.message_id, reply_markup=model_keyboard())

    elif data.startswith("model_"):
        model = data[len("model_"):]
        user_settings[cid]["model"] = model
        bot.edit_message_text(f"Модель установлена: {model}", cid, call.message.message_id, reply_markup=main_keyboard())

    elif data == "tags":
        bot.edit_message_text("Выбери категорию:", cid, call.message.message_id, reply_markup=category_keyboard())

    elif data.startswith("cat_"):
        cat = data[len("cat_"):]
        bot.edit_message_text(f"Выбери теги категории {CATEGORY_NAMES_EMOJI.get(cat, cat)}:", cid, call.message.message_id, reply_markup=tags_keyboard(cat, cid))

    elif data.startswith("tag_"):
        tag = data[len("tag_"):]
        tags = user_settings[cid]["features"]
        if tag in tags:
            tags.remove(tag)
        else:
            tags.append(tag)
        user_settings[cid]["features"] = tags
        bot.answer_callback_query(call.id, f"{'Добавлено' if tag in tags else 'Удалено'}")
        # Обновим текущее меню с правильной категорией
        for cat, tag_list in TAGS.items():
            if tag in tag_list:
                bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=tags_keyboard(cat, cid))
                break

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

# ==== ПРОМТ ====
def build_prompt(base, tags):
    map_tag = {
        "vagina": "vaginal penetration", "anal": "anal penetration", "both": "double penetration",
        "dildo": "dildo", "anal_beads": "anal beads", "anal_plug": "anal plug", "gag": "gag", "piercing": "body piercing",
        "doggy": "doggy style", "standing": "standing pose", "splits": "splits", "squat": "squatting", "lying": "laying",
        "hor_split": "horizontal splits", "ver_split": "vertical splits", "side_up_leg": "lying on side, one leg up",
        "front_facing": "facing viewer", "back_facing": "back facing", "lying_knees_up": "lying, knees up and apart",
        "stockings": "stockings", "bikini": "bikini", "mask": "mask", "heels": "high heels", "shibari": "shibari",
        "cow_costume": "cow costume", "bikini_tan_lines": "bikini tan lines",
        "big_breasts": "large breasts", "small_breasts": "small breasts",
        "skin_white": "white skin", "skin_black": "black skin",
        "futanari": "futanari", "femboy": "femboy", "ethnicity_asian": "asian girl", "ethnicity_european": "european girl",
        "body_fat": "curvy body", "body_thin": "thin body", "body_fit": "fit body", "body_muscular": "muscular body",
        "height_tall": "tall height", "height_short": "short height",
        "age_loli": "loli", "age_milf": "milf", "age_middle": "mature woman",
        "furry_cow": "furry cow", "furry_cat": "furry cat", "furry_dog": "furry dog",
        "furry_dragon": "furry dragon", "furry_sylveon": "furry sylveon"
    }
    additions = [map_tag.get(tag, tag) for tag in tags]
    additions.append("nsfw, masterpiece, ultra detailed")
    return base + ", " + ", ".join(additions)

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