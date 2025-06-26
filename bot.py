# --- bot.py ---
import os
import time
import requests
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

CATEGORY_NAMES = {
    "poses": "Позы", "clothes": "Одежда", "body": "Тело", "ethnos": "Этнос",
    "holes": "Отверстия", "toys": "Игрушки", "furry": "Фури", "characters": "Персонажи",
    "head": "Голова", "view": "Обзор"
}

TAGS = {
    "poses": {
        "doggy": "Наездница", "standing": "Стоя", "splits": "Шпагат",
        "squat": "Присед", "lying": "Лежа", "hor_split": "Горизонтальный шпагат",
        "ver_split": "Вертикальный шпагат", "side_up_leg": "Нога вверх", "bridge": "Мост",
        "suspended": "Подвешена", "front_facing": "Лицом к зрителю", "back_facing": "Спиной",
        "lying_knees_up": "Лежа, колени вверх"
    },
    "clothes": {
        "stockings": "Чулки", "heels": "Каблуки", "mask": "Маска",
        "shibari": "Шибари", "bikini_tan_lines": "Загар от бикини"
    },
    "body": {
        "big_breasts": "Большая грудь", "small_breasts": "Маленькая грудь",
        "body_thin": "Худое", "body_fit": "Подтянутое", "body_fat": "Пышное",
        "body_normal": "Нормальное", "skin_white": "Белая кожа", "skin_black": "Чёрная кожа",
        "body_muscular": "Мускулистое", "age_loli": "Лоли", "age_milf": "Милфа", "age_21": "Возраст 21",
        "cum": "Вся в сперме", "belly_bloat": "Вздутие живота", "succubus_tattoo": "Тату на животе"
    },
    "ethnos": {
        "ethnicity_asian": "Азиатка", "ethnicity_european": "Европейка",
        "futanari": "Футанари", "femboy": "Фембой"
    },
    "holes": {
        "vagina": "Вагина", "anal": "Анус", "both": "Вагина и анус"
    },
    "toys": {
        "dildo": "Дилдо", "huge_dildo": "Большое дилдо", "horse_dildo": "Лошадиное дилдо",
        "anal_beads": "Анальные бусы", "anal_plug": "Анальная пробка", "anal_expander": "Анальный расширитель",
        "gag": "Кляп", "piercing": "Пирсинг", "long_dildo_path": "Дилдо через рот"
    },
    "furry": {
        "furry_cow": "Фури корова", "furry_cat": "Фури кошка", "furry_dog": "Фури собака",
        "furry_dragon": "Фури дракон", "furry_fox": "Фури лисица", "furry_bunny": "Фури кролик",
        "furry_wolf": "Фури волчица", "furry_sylveon": "Фури сильвеон"
    },
    "characters": {
        "rias": "Риас Гремори", "akeno": "Акено", "kafka": "Кафка",
        "eula": "Еола", "fu_xuan": "Фу Сюань", "ayase": "Аясе Сейко", "2b": "2B", "yor": "Йор Форжер"
    },
    "head": {
        "ahegao": "Ахегао", "ecstasy_face": "Экстаз", "pain_face": "Боль", "gold_lipstick": "Золотая помада"
    },
    "view": {
        "view_top": "Сверху", "view_bottom": "Снизу", "view_side": "Сбоку", "view_close": "Близко", "view_full": "Полный рост"
    }
}

TAG_PROMPTS = {
    "rias": "red hair, blue eyes, rias gremory, large breasts",
    "akeno": "black hair, purple eyes, akeno himejima",
    "kafka": "purple wavy hair, honkai star rail, kafka",
    "eula": "blue hair, genshin impact, eula",
    "fu_xuan": "pink twin tails, honkai star rail, fu xuan",
    "ayase": "black hair, school uniform, ayase seiko",
    "2b": "white hair, blindfold, nier automata, 2b",
    "yor": "black hair, red eyes, spy x family, yor forger",

    "vagina": "spread pussy", "anal": "spread anus", "both": "spread pussy and anus",
    "dildo": "dildo inserted", "huge_dildo": "huge dildo", "horse_dildo": "horse dildo",
    "anal_beads": "anal beads inserted", "anal_plug": "anal plug", "anal_expander": "anal expander",
    "gag": "ball gag", "piercing": "nipple and genital piercing",
    "long_dildo_path": "dildo in anus, exiting mouth, belly bulge",

    "doggy": "doggy style", "standing": "standing", "splits": "split pose", "squat": "squatting",
    "lying": "lying down", "hor_split": "horizontal split", "ver_split": "vertical split",
    "side_up_leg": "on side, leg raised", "bridge": "arched bridge", "suspended": "suspended in ropes",
    "front_facing": "facing viewer", "back_facing": "back to viewer", "lying_knees_up": "knees up",

    "stockings": "black stockings", "heels": "red high heels", "mask": "face mask", "shibari": "shibari rope",
    "bikini_tan_lines": "bikini tan lines",

    "big_breasts": "large breasts", "small_breasts": "small breasts", "body_thin": "thin body",
    "body_fit": "fit body", "body_fat": "curvy body", "body_normal": "normal body",
    "skin_white": "white skin", "skin_black": "dark skin", "body_muscular": "muscular",
    "age_loli": "young girl", "age_milf": "mature woman", "age_21": "age 21 girl",
    "cum": "cum covered", "belly_bloat": "belly bulge", "succubus_tattoo": "succubus tattoo on belly",

    "futanari": "futanari girl", "femboy": "femboy", "ethnicity_asian": "asian girl", "ethnicity_european": "european girl",

    "furry_cow": "furry cow girl", "furry_cat": "furry cat girl", "furry_dog": "furry dog girl",
    "furry_dragon": "furry dragon girl", "furry_fox": "furry fox girl", "furry_bunny": "furry bunny girl",
    "furry_wolf": "furry wolf girl", "furry_sylveon": "furry sylveon",

    "ahegao": "ahegao", "ecstasy_face": "face in ecstasy", "pain_face": "face in pain", "gold_lipstick": "gold lipstick",

    "view_top": "from above", "view_bottom": "from below", "view_side": "side view",
    "view_close": "close-up", "view_full": "full body"
}

NEGATIVE_PROMPT = "bad anatomy, blurry, cropped, watermark, lowres, text, hands on chest, hands covering nipples or genitals, censor, male"

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
    kb = types.InlineKeyboardMarkup()
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
    if cid not in user_settings:
        user_settings[cid] = {"tags": [], "last_cat": None, "count": 1}
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
        tags.remove(tag) if tag in tags else tags.append(tag)
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=tag_menu(cat, tags))
    elif data == "done_tags":
        bot.edit_message_text("Теги сохранены.", cid, call.message.message_id, reply_markup=main_menu())
    elif data == "back_to_cat":
        bot.edit_message_text("Выбери категорию:", cid, call.message.message_id, reply_markup=category_menu())
    elif data == "choose_count":
        bot.edit_message_text("Сколько изображений сгенерировать?", cid, call.message.message_id, reply_markup=count_menu())
    elif data.startswith("count_"):
        count = int(data.split("_")[1])
        user_settings[cid]["count"] = count
        bot.edit_message_text(f"✅ Количество: {count}", cid, call.message.message_id, reply_markup=category_menu())
    elif data == "generate":
        tags = user_settings[cid]["tags"]
        count = user_settings[cid].get("count", 1)
        prompt = ", ".join([TAG_PROMPTS.get(tag, tag) for tag in tags])
        final_prompt = f"nsfw, masterpiece, anime style, best quality, {prompt}"
        urls = replicate_generate(final_prompt, NEGATIVE_PROMPT, count)
        if urls:
            media = [types.InputMediaPhoto(url) for url in urls]
            bot.send_media_group(cid, media)
            kb = types.InlineKeyboardMarkup()
            kb.add(
                types.InlineKeyboardButton("🔁 Начать заново", callback_data="start"),
                types.InlineKeyboardButton("🔧 Изменить теги", callback_data="choose_tags"),
                types.InlineKeyboardButton("➡ Продолжить с этими", callback_data="generate")
            )
            bot.send_message(cid, "✅ Готово!", reply_markup=kb)
        else:
            bot.send_message(cid, "❌ Ошибка генерации.")

def replicate_generate(prompt, negative_prompt, count):
    url = "https://api.replicate.com/v1/predictions"
    headers = {"Authorization": f"Token {REPLICATE_TOKEN}", "Content-Type": "application/json"}
    json_data = {
        "version": REPLICATE_MODEL,
        "input": {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "num_outputs": count
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