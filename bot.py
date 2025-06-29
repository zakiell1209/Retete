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
        "gag": "Кляп", "piercing": "Пирсинг", "long_dildo_path": "Дилдо через рот", "double_dildo": "Два дилдо"
    },
    "furry": {
        "furry_cow": "Фури корова", "furry_cat": "Фури кошка", "furry_dog": "Фури собака",
        "furry_dragon": "Фури дракон", "furry_fox": "Фури лисица", "furry_bunny": "Фури кролик",
        "furry_wolf": "Фури волчица", "furry_sylveon": "Фури сильвеон"
    },
    "characters": {
        "rias": "Риас Гремори", "akeno": "Акено", "kafka": "Кафка",
        "eula": "Еола", "fu_xuan": "Фу Сюань", "ayase": "Аясе Сейко",
        "2b": "2B", "yor": "Йор Форжер", "kiana": "Киана", "katarina": "Катарина",
        "esdeath": "Эсдес", "koneko": "Конеко", "sparkle": "Светлячок"
    },
    "head": {
        "ahegao": "Ахегао", "ecstasy_face": "Экстаз", "pain_face": "Боль", "gold_lipstick": "Золотая помада"
    },
    "view": {
        "view_top": "Сверху", "view_bottom": "Снизу", "view_side": "Сбоку",
        "view_close": "Близко", "view_full": "Полный рост"
    }
}

RU_TO_TAG = {}
for cat in TAGS.values():
    for key, ru in cat.items():
        RU_TO_TAG[ru.lower()] = key

TAG_PROMPTS = {
    # Персонажи
    "rias": "red hair, blue eyes, rias gremory, large breasts",
    "akeno": "black hair, purple eyes, akeno himejima",
    "kafka": "purple wavy hair, kafka, honkai star rail",
    "eula": "light blue hair, eula, genshin impact",
    "fu_xuan": "pink twin tails, fu xuan, honkai star rail",
    "ayase": "black hair, school uniform, ayase seiko, dandadan anime, accurate",
    "2b": "white bob haircut, blindfold, black leotard, nier automata, 2b",
    "yor": "black long hair, red eyes, assassin dress, spy x family, yor forger",
    "kiana": "white hair, blue eyes, kiana kaslana, league of legends",
    "katarina": "red hair, daggers, assassin outfit, katarina, league of legends",
    "esdeath": "blue military uniform, long blue hair, akame ga kill, esdeath",
    "koneko": "white hair, yellow eyes, petite body, highschool dxd, koneko toujou",
    "sparkle": "sparkle, honkai star rail, pink hair, sci-fi outfit",
    # Игрушки
    "dildo": "dildo inserted in vagina",
    "huge_dildo": "huge dildo in anus",
    "horse_dildo": "horse dildo, anal",
    "anal_beads": "anal beads in anus",
    "anal_plug": "anal plug inserted",
    "anal_expander": "anal expander in anus",
    "gag": "ball gag in mouth",
    "piercing": "nipple piercing, genital piercing",
    "long_dildo_path": "dildo inserted in anus exiting mouth, belly bulge",
    "double_dildo": "two dildos inserted in anus, stretched",
    # Отверстия
    "vagina": "realistic spread vagina, open",
    "anal": "spread anus, gaping, realistic",
    "both": "spread vagina and anus, detailed",
    # Пол, тело, этнос
    "futanari": "futanari with realistic penis and vagina, no balls",
    "femboy": "feminine femboy, small penis, slim body, girly face",
    "ethnicity_asian": "asian girl",
    "ethnicity_european": "european girl",
    "big_breasts": "very large natural breasts",
    "small_breasts": "flat chest, small breasts",
    "body_thin": "thin body",
    "body_fit": "athletic body",
    "body_fat": "plump curvy body",
    "body_normal": "average female body",
    "skin_white": "pale white skin",
    "skin_black": "dark african skin",
    "body_muscular": "muscular defined body",
    "age_loli": "petite body, youthful",
    "age_milf": "mature face and body",
    "age_21": "adult female, 21 years old",
    "cum": "cum on face, breasts, body",
    "belly_bloat": "belly bulge from toy",
    "succubus_tattoo": "succubus tattoo on belly",
    # Позы
    "doggy": "on all fours, doggy style",
    "standing": "standing pose, open legs",
    "splits": "doing splits, flexible",
    "squat": "squatting, spread legs",
    "lying": "lying down, seductive",
    "hor_split": "horizontal split pose, legs wide",
    "ver_split": "vertical split, leg raised",
    "side_up_leg": "side pose, one leg up",
    "bridge": "bridge pose, back arched",
    "suspended": "tied and suspended in air, bondage ropes",
    "front_facing": "facing viewer",
    "back_facing": "back to viewer",
    "lying_knees_up": "lying, knees bent upward",
    # Одежда
    "stockings": "black thigh-high stockings only",
    "heels": "red high heels",
    "mask": "blindfold mask",
    "shibari": "shibari rope bondage",
    "bikini_tan_lines": "bikini tan lines only, no clothes",
    # Голова
    "ahegao": "ahegao expression, tongue out",
    "ecstasy_face": "face of pleasure, flushed cheeks",
    "pain_face": "painful expression, tears",
    "gold_lipstick": "shiny gold lipstick",
    # Обзор
    "view_top": "view from above",
    "view_bottom": "view from below",
    "view_side": "side profile",
    "view_close": "close-up shot",
    "view_full": "full body visible"
}

NEGATIVE_PROMPT = (
    "bad anatomy, lowres, blurry, watermark, signature, text, "
    "hands covering, male, clothes, censored, distorted face, broken fingers"
)

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
    kb = types.InlineKeyboardMarkup(row_width=4)
    for i in range(1, 5):
        kb.add(types.InlineKeyboardButton(str(i), callback_data=f"count_{i}"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="back_to_cat"))
    return kb

def tag_menu(category, selected):
    kb = types.InlineKeyboardMarkup(row_width=2)
    for key, name in TAGS[category].items():
        label = f"✅ {name}" if key in selected else name
        kb.add(types.InlineKeyboardButton(label, callback_data=f"tag_{category}_{key}"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="back_to_cat"))
    return kb

@bot.message_handler(commands=["start"])
def cmd_start(msg):
    cid = msg.chat.id
    user_settings[cid] = {"tags": [], "last_prompt": [], "count": 1, "last_cat": None}
    bot.send_message(cid, "Привет! Что делаем?", reply_markup=main_menu())

@bot.message_handler(func=lambda m: True, content_types=["text"])
def handle_manual(m):
    cid = m.chat.id
    names = [n.strip().lower() for n in m.text.split(",")]
    keys = [RU_TO_TAG[n] for n in names if n in RU_TO_TAG]
    if not keys:
        bot.send_message(cid, "❌ Теги не распознаны.")
        return
    user_settings[cid] = {"tags": keys, "last_prompt": keys.copy(), "count": 1, "last_cat": None}
    bot.send_message(cid, f"✅ Теги обновлены.", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda c: True)
def callback(c):
    cid = c.message.chat.id
    data = c.data
    if cid not in user_settings:
        user_settings[cid] = {"tags": [], "last_prompt": [], "count": 1, "last_cat": None}
    if data == "choose_tags":
        bot.edit_message_text("Выбери категорию:", cid, c.message.message_id, reply_markup=category_menu())
    elif data.startswith("cat_"):
        cat = data.split("_", 1)[1]
        user_settings[cid]["last_cat"] = cat
        bot.edit_message_text(f"Категория: {CATEGORY_NAMES[cat]}", cid, c.message.message_id,
                              reply_markup=tag_menu(cat, user_settings[cid]["tags"]))
    elif data.startswith("tag_"):
        _, cat, tag = data.split("_", 2)
        tags = user_settings[cid]["tags"]
        if tag in tags: tags.remove(tag)
        else: tags.append(tag)
        bot.edit_message_reply_markup(cid, c.message.message_id, reply_markup=tag_menu(cat, tags))
    elif data == "done_tags":
        bot.edit_message_text("Теги сохранены.", cid, c.message.message_id, reply_markup=main_menu())
    elif data == "choose_count":
        bot.edit_message_text("Сколько изображений сгенерировать?", cid,
                              c.message.message_id, reply_markup=count_menu())
    elif data.startswith("count_"):
        cnt = int(data.split("_", 1)[1])
        user_settings[cid]["count"] = cnt
        bot.edit_message_text(f"✅ Количество: {cnt}", cid, c.message.message_id, reply_markup=main_menu())
    elif data == "back_to_cat":
        bot.edit_message_text("Выбери категорию:", cid, c.message.message_id, reply_markup=category_menu())
    elif data == "generate":
        tags = user_settings[cid]["tags"]
        if not tags:
            bot.send_message(cid, "❌ Сначала выбери теги!", reply_markup=main_menu())
            return
        bot.send_message(cid, "⏳ Генерация...")
        prompt = ", ".join(TAG_PROMPTS.get(t, t) for t in tags)
        final = f"nsfw, anime style, high detail, masterpiece, best quality, fully nude, {prompt}"
        size = user_settings[cid]["count"]
        urls = replicate_generate(final, NEGATIVE_PROMPT, size)
        if urls:
            media = [types.InputMediaPhoto(u) for u in urls]
            bot.send_media_group(cid, media)
            kb = types.InlineKeyboardMarkup()
            kb.add(
                types.InlineKeyboardButton("🔁 Начать заново", callback_data="start"),
                types.InlineKeyboardButton("🔧 Изменить теги", callback_data="choose_tags"),
                types.InlineKeyboardButton("➡ Продолжить", callback_data="generate")
            )
            bot.send_message(cid, "✅ Готово!", reply_markup=kb)
        else:
            bot.send_message(cid, "❌ Не удалось сгенерировать.", reply_markup=main_menu())
    elif data == "start":
        user_settings[cid] = {"tags": [], "last_prompt": [], "count": 1, "last_cat": None}
        bot.send_message(cid, "🔄 Сброшено.", reply_markup=main_menu())

def replicate_generate(prompt, negative_prompt, count):
    url = "https://api.replicate.com/v1/predictions"
    headers = {"Authorization": f"Token {REPLICATE_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "version": REPLICATE_MODEL,
        "input": {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "num_outputs": count
        }
    }
    r = requests.post(url, headers=headers, json=payload)
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