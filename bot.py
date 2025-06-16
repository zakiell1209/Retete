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
        "vertical_splits", "horizontal_splits", "lying_legs_apart",
        "side_leg_up", "facing_viewer", "back_to_viewer",
        "bridge_pose", "suspended_rope"
    ],
    "clothes": ["stockings", "bikini", "mask", "heels", "shibari", "cow_costume", "bikini_tan_lines"],
    "body": ["loli", "milf", "age_21", "thin", "muscular", "curvy", "normal"],
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

CLOTHES_NAMES_EMOJI = {
    "stockings": "Чулки 🧦", "bikini": "Бикини 👙", "mask": "Маска 😷", "heels": "Туфли 👠",
    "shibari": "Шибари ⛓️", "cow_costume": "Костюм коровы 🐄", "bikini_tan_lines": "Загар от бикини ☀️"
}

TAG_NAMES_EMOJI = {
    "holes": {"vagina": "Вагина ♀️", "anal": "Анал 🍑", "both": "Оба 🔥"},
    "toys": {"dildo": "Дилдо 🍆", "anal_beads": "Анальные бусы 🔴", "anal_plug": "Пробка 🔵", "gag": "Кляп 😶", "piercing": "Пирсинг 💎"},
    "poses": {
        "doggy": "Догги 🐕",
        "standing": "Стоя 🧍",
        "splits": "Шпагат 🤸",
        "squat": "Присед 🧎",
        "lying": "Лежа 🛌",
        "vertical_splits": "Вертикальный шпагат ↕️",
        "horizontal_splits": "Горизонтальный шпагат ↔️",
        "lying_legs_apart": "Лежа, ноги врозь 🛌",
        "side_leg_up": "На боку, нога вверх 🦵",
        "facing_viewer": "Лицом к зрителю 👁",
        "back_to_viewer": "Спиной к зрителю 🔙",
        "bridge_pose": "Мост 🌉",
        "suspended_rope": "Подвешена на верёвках 🪢"
    },
    "body": {
        "loli": "Лоли 👧",
        "milf": "Милфа 👩‍🦳",
        "age_21": "Возраст 21 🎂",
        "thin": "Худое 🦴",
        "muscular": "Накачаное 💪",
        "curvy": "Пышное 🍑",
        "normal": "Нормальное 🙂"
    },
    "ethnicity": {"femboy": "Фембой ⚧", "ethnicity_asian": "Азиатка 🈶", "ethnicity_european": "Европейка 🇪🇺"},
    "furry": {
        "furry_cow": "Фури корова 🐄",
        "furry_cat": "Фури кошка 🐱",
        "furry_dog": "Фури собака 🐶",
        "furry_dragon": "Фури дракон 🐉",
        "furry_silveon": "Фури сильвеон 🦄"
    },
    "clothes": CLOTHES_NAMES_EMOJI
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
            name = "✅ " + name
        markup.add(types.InlineKeyboardButton(name, callback_data=f"tag_{tag}"))
    markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="tags_back"))
    return markup

def postgen_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔄 Продолжить генерацию", callback_data="continue_generation"),
        types.InlineKeyboardButton("✏️ Редактировать теги", callback_data="edit_tags"),
        types.InlineKeyboardButton("♻️ Начать выбор тегов заново", callback_data="restart_tags"),
        types.InlineKeyboardButton("⬅ Главное меню", callback_data="main_menu")
    )
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
        model = data.split("_")[1]
        user_settings[cid]["model"] = model
        bot.edit_message_text(f"Модель установлена: {model}", cid, call.message.message_id, reply_markup=main_keyboard())

    elif data == "tags":
        bot.edit_message_text("Выбери категорию:", cid, call.message.message_id, reply_markup=category_keyboard())

    elif data.startswith("cat_"):
        cat = data.split("_")[1]
        bot.edit_message_text(f"Выбери теги категории {CATEGORY_NAMES_EMOJI[cat]}:", cid, call.message.message_id, reply_markup=tags_keyboard(cat, user_settings[cid]["features"]))

    elif data.startswith("tag_"):
        tag = data.split("_")[1]
        tags = user_settings[cid]["features"]
        if tag in tags:
            tags.remove(tag)
            status = "удалён"
        else:
            tags.append(tag)
            status = "добавлен"
        user_settings[cid]["features"] = tags
        name = None
        # Определяем категорию тега для правильного имени
        for cat_key, cat_tags in TAGS.items():
            if tag in cat_tags:
                name = TAG_NAMES_EMOJI.get(cat_key, {}).get(tag, tag)
                current_category = cat_key
                break
        bot.answer_callback_query(call.id, f"{name} {status}")
        # Остаёмся в той же категории, обновляем клавиатуру
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=tags_keyboard(current_category, tags))

    elif data == "tags_done":
        bot.edit_message_text("Теги сохранены.", cid, call.message.message_id, reply_markup=main_keyboard())

    elif data == "tags_back":
        bot.edit_message_text("Выбери категорию:", cid, call.message.message_id, reply_markup=category_keyboard())

    elif data == "generate":
        user_settings[cid]["waiting_for_prompt"] = True
        bot.send_message(cid, "✏️ Введи описание картинки:")

    elif data == "continue_generation":
        user_settings[cid]["waiting_for_prompt"] = True
        bot.send_message(cid, "✏️ Введи описание картинки (будут использованы текущие теги):")

    elif data == "edit_tags":
        bot.send_message(cid, "Выбери категорию для редактирования тегов:", reply_markup=category_keyboard())

    elif data == "restart_tags":
        user_settings[cid]["features"] = []
        bot.send_message(cid, "Выбери категорию для выбора тегов заново:", reply_markup=category_keyboard())

    elif data == "main_menu":
        bot.edit_message_text("Привет! Выбери действие:", cid, call.message.message_id, reply_markup=main_keyboard())

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
        bot.send_photo(cid, image_url, caption="Вот результат!", reply_markup=postgen_keyboard())
    else:
        bot.send_message(cid, "❌ Ошибка генерации изображения.")

# ==== ПРОМТ ====
def build_prompt(base, tags):
    additions = []
    map_tag = {
        # Holes
        "vagina": "vaginal penetration",
        "anal": "anal penetration",
        "both": "double penetration",
        # Toys
        "dildo": "dildo",
        "anal_beads": "anal beads",
        "anal_plug": "anal plug",
        "gag": "gag",
        "piercing": "body piercing",
        # Poses
        "doggy": "doggy style",
        "standing": "standing pose",
        "splits": "splits",
        "squat": "squatting",
        "lying": "laying",
        "vertical_splits": "doing a vertical split, one leg up",
        "horizontal_splits": "doing a horizontal split, legs wide apart",
        "lying_legs_apart": "lying on back with legs spread apart",
        "side_leg_up": "lying on side with one leg lifted",
        "facing_viewer": "facing the viewer directly",
        "back_to_viewer": "back turned to viewer",
        "bridge_pose": "bridge pose, arched back",
        "suspended_rope": "suspended by ropes, rope bondage",
        # Clothes
        "stockings": "stockings",
        "bikini": "bikini",
        "mask": "mask",
        "heels": "high heels",
        "shibari": "shibari",
        "cow_costume": "woman in cow print stockings with cow horns and tail, no underwear",
        "bikini_tan_lines": "tanned skin with white bikini tan lines",
        # Body
        "loli": "young girl, loli style",
        "milf": "mature woman, milf",
        "age_21": "age 21 years old",
        "thin": "thin body",
        "muscular": "muscular body",
        "curvy": "curvy body",
        "normal": "normal body",
        # Ethnicity
        "femboy": "femboy",
        "ethnicity_asian": "asian girl",
        "ethnicity_european": "european girl",
        # Furry (Silveon - максимально похож на Сильвеона из игр/аниме)
        "furry_cow": "furry cow",
        "furry_cat": "furry cat",
        "furry_dog": "furry dog",
        "furry_dragon": "furry dragon",
        "furry_silveon": ("silveon anthro, majestic and elegant, with glowing markings, soft blue and purple hues, anime style, fantasy creature, detailed fur"),
        # Skin
        "skin_white": "white skin",
        "skin_black": "black skin"
    }
    for tag in tags:
        additions.append(map_tag.get(tag, tag))
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
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/", methods=["GET"])
def index():
    return "Бот работает", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=PORT)