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
    "anime": "c1d5b02687df6081c7953c74bcc527858702e8c153c9382012ccc3906752d3ec"
}

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
user_settings = {}

TAGS = {
    "holes": ["vagina", "anal", "both"],
    "toys": ["dildo", "huge_dildo", "horse_dildo", "anal_beads", "anal_plug", "anal_expander", "gag", "piercing"],
    "poses": ["doggy", "standing", "splits", "squat", "lying", "hor_split", "ver_split", "side_up_leg", "front_facing", "back_facing", "lying_knees_up"],
    "clothes": ["stockings", "bikini_tan_lines", "mask", "heels", "shibari", "cow_costume"],
    "body": [
        "big_breasts", "small_breasts", "skin_white", "skin_black",
        "body_fat", "body_thin", "body_normal", "body_fit", "body_muscular",
        "height_tall", "height_short",
        "age_loli", "age_milf", "age_middle", "age_21",
        "cum", "belly_bloat", "long_dildo_path", "succubus_tattoo"
    ],
    "ethnos": ["futanari", "femboy", "ethnicity_asian", "ethnicity_european"],
    "furry": ["furry_cow", "furry_cat", "furry_dog", "furry_dragon", "furry_sylveon"]
}

CATEGORY_NAMES_EMOJI = {
    "holes": "Отверстия 🕳️", "toys": "Игрушки 🧸", "poses": "Позиции 🤸‍♀️",
    "clothes": "Одежда 👗", "body": "Тело 🧍", "ethnos": "Этнос 🌍", "furry": "Фури 🐾"
}

TAG_NAMES_EMOJI = {
    "body": {
        "big_breasts": "Большая грудь 🍒", "small_breasts": "Маленькая грудь 🥥",
        "skin_white": "Белая кожа ⚪", "skin_black": "Чёрная кожа ⚫",
        "body_fat": "Пышное 🍰", "body_thin": "Худое 🪶", "body_normal": "Обычное 🧍",
        "body_fit": "Подтянутое 🏃", "body_muscular": "Мускулистое 💪",
        "height_tall": "Высокая 📏", "height_short": "Низкая 📐",
        "age_loli": "Лоли 👧", "age_milf": "Милфа 💋", "age_middle": "Средний возраст 👩", "age_21": "21 год 🎂",
        "cum": "Сперма 💦", "belly_bloat": "Вздутие 💨",
        "long_dildo_path": "Дилдо через тело 🔄", "succubus_tattoo": "Тату сукуба ❤️"
    },
    "holes": {"vagina": "Вагина ♀️", "anal": "Анал 🍑", "both": "Оба 🔥"},
    "toys": {
        "dildo": "Дилдо 🍆", "huge_dildo": "Огромное 🍆🔥", "horse_dildo": "Конское 🐎🍆",
        "anal_beads": "Анальные бусы 🔴", "anal_plug": "Пробка 🔵",
        "anal_expander": "Расширитель ⚙️", "gag": "Кляп 😶", "piercing": "Пирсинг 💎"
    },
    "poses": {
        "doggy": "Догги 🐕", "standing": "Стоя 🧍", "splits": "Шпагат 🤸",
        "squat": "Присед 🧎", "lying": "Лежа 🛌", "hor_split": "Гор. шпагат ↔️",
        "ver_split": "Вер. шпагат ↕️", "side_up_leg": "Бок + нога 🔝",
        "front_facing": "Лицом 👁", "back_facing": "Спиной 🍑", "lying_knees_up": "Лёжа, колени вверх 🧷"
    },
    "clothes": {
        "stockings": "Чулки 🧦", "bikini_tan_lines": "Загар от бикини ☀️", "mask": "Маска 😷",
        "heels": "Туфли 👠", "shibari": "Шибари ⛓️", "cow_costume": "Костюм коровы 🐄"
    },
    "ethnos": {
        "futanari": "Футанари 🍆", "femboy": "Фембой ⚧",
        "ethnicity_asian": "Азиатка 🈶", "ethnicity_european": "Европейка 🇪🇺"
    },
    "furry": {
        "furry_cow": "Фури-Коровка 🐄", "furry_cat": "Фури-Кошка 🐱",
        "furry_dog": "Фури-Собака 🐶", "furry_dragon": "Фури-Дракон 🐉", "furry_sylveon": "Сильвеон 🎀"
    }
}

def main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("🧩 Выбрать теги", callback_data="tags"))
    markup.add(types.InlineKeyboardButton("✅ Генерировать", callback_data="generate"))
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
        markup.add(types.InlineKeyboardButton(name, callback_data=f"tag_{category}_{tag}"))
    markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="tags_back"))
    return markup

@bot.message_handler(commands=["start"])
def start(message):
    cid = message.chat.id
    user_settings[cid] = {"features": [], "waiting_for_prompt": False}
    bot.send_message(cid, "Привет! Выбери действие:", reply_markup=main_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    cid = call.message.chat.id
    data = call.data
    if cid not in user_settings:
        user_settings[cid] = {"features": [], "waiting_for_prompt": False}

    if data == "tags":
        time.sleep(0.3)
        bot.edit_message_text("Выбери категорию:", cid, call.message.message_id, reply_markup=category_keyboard())

    elif data.startswith("cat_"):
        cat = data.split("_", 1)[1]
        user_settings[cid]["last_category"] = cat
        bot.edit_message_text(f"Выбери теги из категории {CATEGORY_NAMES_EMOJI[cat]}:", cid, call.message.message_id, reply_markup=tags_keyboard(cat, cid))

    elif data.startswith("tag_"):
        _, cat, tag = data.split("_", 2)
        tags = user_settings[cid]["features"]
        if tag in tags:
            tags.remove(tag)
            action = "Удалено"
        else:
            tags.append(tag)
            action = "Добавлено"
        user_settings[cid]["features"] = tags
        bot.answer_callback_query(call.id, action)
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=tags_keyboard(cat, cid))

    elif data == "tags_done":
        bot.edit_message_text("Теги сохранены.", cid, call.message.message_id, reply_markup=main_keyboard())

    elif data == "tags_back":
        bot.edit_message_text("Выбери категорию:", cid, call.message.message_id, reply_markup=category_keyboard())

    elif data == "generate":
        features = user_settings[cid].get("features", [])
        if not features:
            bot.send_message(cid, "⚠️ Сначала выбери теги для генерации.")
            return
        bot.send_message(cid, "⏳ Генерация изображения...")
        prompt = build_prompt(features)
        status_url, err = generate_image(prompt, REPLICATE_MODELS["anime"])
        if err:
            bot.send_message(cid, err)
            return
        image_url = wait_for_image(status_url)
        if image_url:
            result_markup = types.InlineKeyboardMarkup()
            result_markup.add(
                types.InlineKeyboardButton("🔁 Начать заново", callback_data="start_over"),
                types.InlineKeyboardButton("🔂 Продолжить генерацию", callback_data="generate")
            )
            result_markup.add(
                types.InlineKeyboardButton("🛠 Редактировать теги", callback_data="edit_tags")
            )
            bot.send_photo(cid, image_url, caption="Вот результат!", reply_markup=result_markup)
        else:
            bot.send_message(cid, "❌ Ошибка генерации изображения.")

    elif data == "start_over":
        user_settings[cid] = {"features": [], "waiting_for_prompt": False}
        bot.send_message(cid, "Привет! Выбери действие:", reply_markup=main_keyboard())

    elif data == "edit_tags":
        last_cat = user_settings[cid].get("last_category")
        if last_cat:
            bot.send_message(cid, f"Редактируем: {CATEGORY_NAMES_EMOJI[last_cat]}", reply_markup=tags_keyboard(last_cat, cid))
        else:
            bot.send_message(cid, "Выбери категорию:", reply_markup=category_keyboard())


def build_prompt(tags):
    base = "nsfw, masterpiece, ultra detailed, anime style, best quality"
    map_tag = {
        "vagina": "open vagina", "anal": "open anus", "both": "open anus and vagina",
        "dildo": "dildo", "huge_dildo": "huge dildo", "horse_dildo": "horse dildo",
        "anal_beads": "anal beads causing belly bloat", "anal_plug": "anal plug", "anal_expander": "anal expander",
        "gag": "gag", "piercing": "body piercing",
        "doggy": "doggy style", "standing": "standing pose", "splits": "splits", "squat": "squatting",
        "lying": "lying", "hor_split": "horizontal splits", "ver_split": "vertical splits",
        "side_up_leg": "lying on side, one leg up", "front_facing": "facing viewer",
        "back_facing": "back facing", "lying_knees_up": "lying, knees up and apart",

        # Жёсткие ограничения по запросу пользователя:
        # "stockings" должен генерировать только чулки, без трусов и прочего,
        # если не выбран "bikini_tan_lines"
        "stockings": "stockings only, no panties, no other clothes",

        # "bikini_tan_lines" — загар от бикини без одежды (не должно быть бикини, только загар)
        "bikini_tan_lines": "dark tanned skin with white bikini tan lines, no bikini, no clothing",

        # Остальная одежда — как было
        "mask": "mask", "heels": "high heels", "shibari": "shibari",
        "cow_costume": "girl wearing cow pattern stockings, horns, tail, no underwear, no cow body, sexy",

        "big_breasts": "large breasts", "small_breasts": "small breasts", "skin_white": "white skin", "skin_black": "black skin",
        "body_fat": "curvy body", "body_thin": "thin body", "body_normal": "average body",
        "body_fit": "fit body", "body_muscular": "muscular body", "height_tall": "tall height", "height_short": "short height",
        "age_loli": "loli", "age_milf": "milf", "age_middle": "mature woman", "age_21": "21 years old",
        "cum": "cum", "belly_bloat": "extremely bloated belly due to anal inflation or toys, exaggerated pressure, visible bulge",

        # "long_dildo_path" — должен генерировать дилдо проходящее через тело
        # Другие теги дилдо не должны его содержать
        "long_dildo_path": "dildo inserted in anus, exiting through mouth, visible bulge through body, extreme penetration",

        # Другие дилдо не должны генерировать дилдо проходящее через тело
        "dildo": "dildo",
        "huge_dildo": "huge dildo",
        "horse_dildo": "horse dildo",

        "succubus_tattoo": "black heart tattoo located on lower abdomen, above uterus, clearly visible on skin, erotic",
        "futanari": "futanari", "femboy": "femboy", "ethnicity_asian": "asian girl", "ethnicity_european": "european girl",
        "furry_cow": "furry cow", "furry_cat": "furry cat", "furry_dog": "furry dog",
        "furry_dragon": "furry dragon", "furry_sylveon": "anthro sylveon, pink and white fur, ribbons, large breasts, sexy"
    }
    additions = [map_tag.get(tag, tag) for tag in tags]
    return base + ", " + ", ".join(additions)

def generate_image(prompt, model_version):
    url = "https://api.replicate.com/v1/predictions"
    headers = {"Authorization": f"Token {REPLICATE_TOKEN}", "Content-Type": "application/json"}
    data = {"version": model_version, "input": {"prompt": prompt}}
    res = requests.post(url, headers=headers, json=data)
    if res.status_code == 201:
        return res.json()["urls"]["get"], None
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