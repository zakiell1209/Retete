# --- bot.py ---
import os
import time
import requests
import random
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

# Категории и теги
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
        "eula": "Еола", "fu_xuan": "Фу Сюань", "ayase": "Аясе Сейко",
        "2b": "2B", "yor": "Йор Форжер"
    },
    "head": {
        "ahegao": "Ахегао", "ecstasy_face": "Экстаз", "pain_face": "Боль", "gold_lipstick": "Золотая помада"
    },
    "view": {
        "view_top": "Сверху", "view_bottom": "Снизу", "view_side": "Сбоку",
        "view_close": "Близко", "view_full": "Полный рост"
    }
}

# Соответствие русских названий тегов их ключам
RU_TO_TAG = {}
for cat in TAGS.values():
    for key, ru in cat.items():
        RU_TO_TAG[ru.lower()] = key

# Преобразование тегов в промпты
TAG_PROMPTS = {
    # персонажи
    "rias": "red hair, blue eyes, rias gremory, large breasts",
    "akeno": "black hair, purple eyes, akeno himejima",
    "kafka": "purple wavy hair, kafka, honkai star rail",
    "eula": "light blue hair, eula, genshin impact",
    "fu_xuan": "pink hair, fu xuan, honkai star rail",
    "ayase": "black hair, school uniform, ayase seiko",
    "2b": "white hair, blindfold, nier automata, 2b",
    "yor": "black hair, red eyes, spy x family, yor forger",
    # отверстия
    "vagina": "detailed spread vagina",
    "anal": "detailed spread anus",
    "both": "vagina and anus spread",
    # игрушки
    "dildo": "dildo inserted",
    "huge_dildo": "huge dildo",
    "horse_dildo": "horse dildo",
    "anal_beads": "anal beads inserted",
    "anal_plug": "anal plug",
    "anal_expander": "anal expander stretching anus",
    "gag": "ball gag",
    "piercing": "nipple and genital piercings",
    "long_dildo_path": "dildo in anus, exiting mouth, belly bulge",
    # позы
    "doggy": "doggy style",
    "standing": "standing pose",
    "splits": "split pose",
    "squat": "squatting",
    "lying": "lying down",
    "hor_split": "horizontal split, legs wide, realistic",
    "ver_split": "vertical split, leg up",
    "side_up_leg": "side pose, leg raised",
    "bridge": "arched back bridge pose",
    "suspended": "suspended in ropes, full body visible",
    "front_facing": "facing viewer",
    "back_facing": "back to viewer",
    "lying_knees_up": "lying, knees up",
    # одежда
    "stockings": "black thigh-high stockings",
    "heels": "red high heels",
    "mask": "face mask",
    "shibari": "shibari rope bondage",
    "bikini_tan_lines": "bikini tan lines",
    # тело
    "big_breasts": "large breasts",
    "small_breasts": "small breasts",
    "body_thin": "thin body",
    "body_fit": "fit body",
    "body_fat": "curvy body",
    "body_normal": "normal body",
    "skin_white": "pale skin",
    "skin_black": "dark skin",
    "body_muscular": "muscular body",
    "age_loli": "young girl style",
    "age_milf": "mature woman",
    "age_21": "21 years old",
    "cum": "cum covered",
    "belly_bloat": "belly bulge",
    "succubus_tattoo": "succubus tattoo on lower abdomen",
    # этнос
    "futanari": "futanari girl, realistic anatomy",
    "femboy": "femboy with feminine body",
    "ethnicity_asian": "asian girl",
    "ethnicity_european": "european girl",
    # фури
    "furry_cow": "furry cow girl",
    "furry_cat": "furry cat girl",
    "furry_dog": "furry dog girl",
    "furry_dragon": "furry dragon girl",
    "furry_fox": "furry fox girl",
    "furry_bunny": "furry bunny girl",
    "furry_wolf": "furry wolf girl",
    "furry_sylveon": "furry sylveon style",
    # голова
    "ahegao": "ahegao face, tongue out",
    "ecstasy_face": "face in ecstasy, flushed cheeks",
    "pain_face": "face in pain, distressed",
    "gold_lipstick": "gold lipstick on lips only",
    # обзор
    "view_top": "top-down view",
    "view_bottom": "low-angle view",
    "view_side": "side view",
    "view_close": "close-up",
    "view_full": "full body shot"
}

# Негативный промпт
NEGATIVE_PROMPT = (
    "bad anatomy, blurry, cropped, watermark, lowres, text, "
    "hands on chest, hands covering nipples or genitals, male, clothing"
)

# Главное меню
def main_menu():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🧩 Выбрать теги", callback_data="choose_tags"))
    kb.add(types.InlineKeyboardButton("🎨 Генерировать", callback_data="generate"))
    return kb

# Меню категорий
def category_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    for key, name in CATEGORY_NAMES.items():
        kb.add(types.InlineKeyboardButton(name, callback_data=f"cat_{key}"))
    kb.add(types.InlineKeyboardButton("✅ Готово", callback_data="done_tags"))
    kb.add(types.InlineKeyboardButton("📸 Кол-во фото", callback_data="choose_count"))
    return kb

# Меню количества изображений (1–4)
def count_menu():
    kb = types.InlineKeyboardMarkup(row_width=4)
    for i in range(1, 5):
        kb.add(types.InlineKeyboardButton(str(i), callback_data=f"count_{i}"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="back_to_cat"))
    return kb

# Меню тегов в категории
def tag_menu(category, selected):
    kb = types.InlineKeyboardMarkup(row_width=2)
    for key, name in TAGS[category].items():
        label = f"✅ {name}" if key in selected else name
        kb.add(types.InlineKeyboardButton(label, callback_data=f"tag_{category}_{key}"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="back_to_cat"))
    return kb

# Обработка /start
@bot.message_handler(commands=["start"])
def cmd_start(msg):
    cid = msg.chat.id
    user_settings[cid] = {"tags": [], "last_prompt": [], "count": 1, "last_cat": None}
    bot.send_message(cid, "Привет! Что делаем?", reply_markup=main_menu())

# Обработка ручного ввода тегов (русские названия через запятую)
@bot.message_handler(func=lambda m: True, content_types=["text"])
def handle_manual(m):
    cid = m.chat.id
    names = [n.strip().lower() for n in m.text.split(",")]
    keys = [RU_TO_TAG[n] for n in names if n in RU_TO_TAG]
    if not keys:
        bot.send_message(cid, "❌ Теги не распознаны. Проверь правильность написания.")
        return
    user_settings[cid] = {"tags": keys, "last_prompt": keys.copy(), "count": 1, "last_cat": None}
    ru = ", ".join([TAGS[c][k] for c in TAGS for k in keys if k in TAGS[c]])
    bot.send_message(cid, f"✅ Выбраны теги: {ru}", reply_markup=main_menu())

# Обработка нажатий кнопок
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
        if tag in tags:
            tags.remove(tag)
        else:
            tags.append(tag)
        bot.edit_message_reply_markup(cid, c.message.message_id,
                                      reply_markup=tag_menu(cat, tags))

    elif data == "done_tags":
        bot.edit_message_text("Теги сохранены.", cid, c.message.message_id, reply_markup=main_menu())

    elif data == "choose_count":
        bot.edit_message_text("Сколько изображений сгенерировать?", cid,
                              c.message.message_id, reply_markup=count_menu())

    elif data.startswith("count_"):
        cnt = int(data.split("_", 1)[1])
        user_settings[cid]["count"] = cnt
        bot.edit_message_text(f"✅ Количество: {cnt}", cid, c.message.message_id, reply_markup=main_menu())

    elif data == "generate":
        settings = user_settings[cid]
        tags = settings["tags"]
        if not tags:
            bot.send_message(cid, "❌ Сначала выбери теги!", reply_markup=main_menu())
            return
        bot.send_message(cid, "⏳ Генерация...")
        prompt = ", ".join(TAG_PROMPTS.get(t, t) for t in tags)
        final = f"nsfw, anime style, masterpiece, best quality, fully nude, {prompt}"
        size = settings["count"]
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
            bot.send_message(cid, "❌ Ошибка генерации.", reply_markup=main_menu())

    elif data == "start":
        user_settings[cid] = {"tags": [], "last_prompt": [], "count": 1, "last_cat": None}
        bot.send_message(cid, "🔄 Настройки сброшены.", reply_markup=main_menu())

# Отправка запроса в Replicate
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
            out = data["output"]
            return out if isinstance(out, list) else [out]
        elif data["status"] == "failed":
            return []
    return []

# Вебхук
@app.route("/", methods=["POST"])
def webhook():
    upd = request.stream.read().decode("utf-8")
    update = telebot.types.Update.de_json(upd)
    bot.process_new_updates([update])
    return "ok", 200

@app.route("/", methods=["GET"])
def home():
    return "бот работает", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=PORT)