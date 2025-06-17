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

REPLICATE_MODEL = "c1d5b02687df6081c7953c74bcc527858702e8c153c9382012ccc3906752d3ec"

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
user_settings = {}

# Теги по категориям, ключи - внутренние имена, значения - русские названия
TAGS = {
    "holes": {
        "vagina": "Вагина",
        "anal": "Анус",
        "both": "Вагина и анус"
    },
    "toys": {
        "dildo": "Дилдо",
        "huge_dildo": "Большое дилдо",
        "horse_dildo": "Лошадиное дилдо",
        "anal_beads": "Анальные бусы",
        "anal_plug": "Анальная пробка",
        "anal_expander": "Анальный расширитель",
        "gag": "Кляп",
        "piercing": "Пирсинг"
    },
    "poses": {
        "doggy": "Наездница (догги-стайл)",
        "standing": "Стоя",
        "splits": "Шпагат",
        "squat": "Приседание",
        "lying": "Лежа",
        "hor_split": "Горизонтальный шпагат",
        "ver_split": "Вертикальный шпагат",
        "side_up_leg": "На боку с поднятой ногой",
        "front_facing": "Лицом к зрителю",
        "back_facing": "Спиной к зрителю",
        "lying_knees_up": "Лежа с раздвинутыми согнутыми коленями",
        "bridge": "Мост",
        "suspended": "Подвешена на верёвках"
    },
    "clothes": {
        "stockings": "Чулки",
        "bikini_tan_lines": "Загар от бикини",
        "mask": "Маска",
        "heels": "Туфли на каблуках",
        "shibari": "Шибари",
        "cow_costume": "Костюм коровы"
    },
    "body": {
        "big_breasts": "Большая грудь",
        "small_breasts": "Маленькая грудь",
        "skin_white": "Белая кожа",
        "skin_black": "Чёрная кожа",
        "body_fat": "Пышное тело",
        "body_thin": "Худое тело",
        "body_normal": "Нормальное телосложение",
        "body_fit": "Подтянутое тело",
        "body_muscular": "Мускулистое тело",
        "age_loli": "Лоли",
        "age_milf": "Милфа",
        "age_21": "Возраст 21 год",
        "cum": "Вся в сперме",
        "belly_bloat": "Вздутие живота от игрушки",
        "long_dildo_path": "Дилдо через анус выходит изо рта",
        "succubus_tattoo": "Тату сердечко на коже в области матки"
    },
    "ethnos": {
        "futanari": "Футанари",
        "femboy": "Фембой",
        "ethnicity_asian": "Азиатка",
        "ethnicity_european": "Европейка"
    },
    "furry": {
        "furry_cow": "Фури корова",
        "furry_cat": "Фури кошка",
        "furry_dog": "Фури собака",
        "furry_dragon": "Фури дракон",
        "furry_sylveon": "Фури Сильвеон",
        "furry_fox": "Фури лисица",
        "furry_rabbit": "Фури кролик",
        "furry_wolf": "Фури волчица"
    },
    "characters": {
        "rias_gremory": "Риас Гремори",
        "akeno_himejima": "Акено Химедзима"
    },
    "head": {
        "ahegao": "Ахегао",
        "pain_face": "Лицо скривившееся от боли",
        "ecstasy_face": "Лицо в экстазе",
        "gold_lipstick": "Золотая помада для губ"
    }
}

CATEGORY_NAMES = {
    "holes": "Отверстия",
    "toys": "Игрушки",
    "poses": "Позы",
    "clothes": "Одежда",
    "body": "Тело",
    "ethnos": "Этнос",
    "furry": "Фури",
    "characters": "Персонажи",
    "head": "Голова"
}

TAG_PROMPTS = {
    # отверстия
    "vagina": "открытая вагина",
    "anal": "открытый анус",
    "both": "открытый анус и вагина",
    # игрушки
    "dildo": "дилдо внутри вагины и ануса",
    "huge_dildo": "огромное дилдо в обоих отверстиях",
    "horse_dildo": "лошадиное дилдо в вагине и анусе",
    "anal_beads": "анальные бусы внутри ануса",
    "anal_plug": "анальная пробка",
    "anal_expander": "анальный расширитель, растягивает анус",
    "gag": "кляп-шар",
    "piercing": "пирсинг на сосках и гениталиях",
    # позы
    "doggy": "поза наездницы (догги-стайл)",
    "standing": "стоя",
    "splits": "шпагат",
    "squat": "приседание",
    "lying": "лежа на спине",
    "hor_split": "горизонтальный шпагат",
    "ver_split": "вертикальный шпагат",
    "side_up_leg": "на боку с поднятой ногой",
    "front_facing": "лицом к зрителю",
    "back_facing": "спиной к зрителю",
    "lying_knees_up": "лежа с раздвинутыми согнутыми коленями",
    "bridge": "мост",
    "suspended": "подвешена на верёвках",
    # одежда
    "stockings": "только чулки",
    "bikini_tan_lines": "смуглая кожа с белыми линиями от бикини, без одежды",
    "mask": "маска на лице",
    "heels": "туфли на высоком каблуке",
    "shibari": "шибари верёвки",
    "cow_costume": "девушка в чулках с узором коровы, с рогами и хвостом, без нижнего белья",
    # тело
    "big_breasts": "большая грудь",
    "small_breasts": "маленькая грудь",
    "skin_white": "белая кожа",
    "skin_black": "чёрная кожа",
    "body_fat": "пышное тело",
    "body_thin": "худое тело",
    "body_normal": "нормальное телосложение",
    "body_fit": "подтянутое тело",
    "body_muscular": "мускулистое тело",
    "age_loli": "лоли",
    "age_milf": "милфа",
    "age_21": "возраст 21 год",
    "cum": "вся в сперме",
    "belly_bloat": "вздутие живота от игрушки",
    "long_dildo_path": "дилдо через анус выходит изо рта",
    "succubus_tattoo": "тату сердечко на коже в области матки",
    # этнос
    "futanari": "футанари девушка с большой грудью",
    "femboy": "фембой с женственным телом",
    "ethnicity_asian": "азиатка",
    "ethnicity_european": "европейка",
    # фури
    "furry_cow": "фури корова с рогами и хвостом",
    "furry_cat": "фури кошка с ушами и хвостом",
    "furry_dog": "фури собака с ушами и хвостом",
    "furry_dragon": "фури дракон с чешуёй и крыльями",
    "furry_sylveon": "фури сильвеон, розовая шерсть, ленты, сексуальная",
    "furry_fox": "фури лисица с оранжевой шерстью, пушистый хвост и уши",
    "furry_rabbit": "фури кролик с белым мехом, длинные уши и хвостик",
    "furry_wolf": "фури волчица с серой шерстью, острые уши и хвост",
    # персонажи
    "rias_gremory": "Риас Гремори из High School DxD, длинные красные волосы, большая грудь, уверенное выражение лица",
    "akeno_himejima": "Акено Химедзима из High School DxD, длинные фиолетовые волосы, собраны в хвост, чувственное лицо",
    # голова
    "ahegao": "лицо в ахегао, высунутый язык, закатанные глаза",
    "pain_face": "лицо скривившееся от боли, слезы, страдальное выражение",
    "ecstasy_face": "лицо в экстазе, глаза полуоткрыты, рот приоткрыт",
    "gold_lipstick": "золотая помада на губах"
}

# Конфликты тегов по категориям (теги, которые не могут быть выбраны вместе)
CONFLICTS = {
    "holes": ["vagina", "anal", "both"],
    "body": ["skin_white", "skin_black"],
    "ethnos": ["futanari", "femboy", "ethnicity_asian", "ethnicity_european"],
    # т.к. "both" уже включает вагину и анус, при выборе "both" удалять вагину и анус
}

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
    user_settings[cid] = {"tags": [], "last_cat": None}
    bot.send_message(cid, "Привет! Что делаем?", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    cid = call.message.chat.id
    if cid not in user_settings:
        user_settings[cid] = {"tags": [], "last_cat": None}

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

        # Обработка конфликтов
        # Если выбирается тег, убираем конфликтующие из той же категории
        if tag in tags:
            # Убираем тег
            tags.remove(tag)
        else:
            # Добавляем тег, при этом удаляем конфликтующие теги из той же категории
            conflicts_in_cat = CONFLICTS.get(cat, [])
            if tag in conflicts_in_cat:
                # Убираем все конфликтующие теги кроме выбранного
                for conflict_tag in conflicts_in_cat:
                    if conflict_tag != tag and conflict_tag in tags:
                        tags.remove(conflict_tag)
            # Специальная логика для "holes" с тегом "both"
            if cat == "holes" and tag == "both":
                # Убираем vagina и anal если есть
                for hole_tag in ["vagina", "anal"]:
                    if hole_tag in tags:
                        tags.remove(hole_tag)
            elif cat == "holes" and tag in ["vagina", "anal"]:
                # Если выбран both, убрать его
                if "both" in tags:
                    tags.remove("both")

            tags.append(tag)

        # Перезаписать выбор
        user_settings[cid]["tags"] = tags
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=tag_menu(cat, tags))

    elif data == "done_tags":
        bot.edit_message_text("Теги сохранены.", cid, call.message.message_id, reply_markup=main_menu())

    elif data == "back_to_cat":
        bot.edit_message_text("Выбери категорию:", cid, call.message.message_id, reply_markup=category_menu())

    elif data == "generate":
        tags = user_settings[cid]["tags"]
        if not tags:
            bot.send_message(cid, "Сначала выбери теги!")
            return
        prompt = build_prompt(tags)
        bot.send_message(cid, "⏳ Генерация изображения...")
        url = replicate_generate(prompt)
        if url:
            kb = types.InlineKeyboardMarkup()
            kb.add(
                types.InlineKeyboardButton("🔁 Начать заново", callback_data="start"),
                types.InlineKeyboardButton("🔧 Изменить теги", callback_data="choose_tags")
            )
            bot.send_photo(cid, url, caption="✅ Готово!", reply_markup=kb)
        else:
            bot.send_message(cid, "❌ Ошибка генерации.")

    elif data == "start":
        user_settings[cid] = {"tags": [], "last_cat": None}
        bot.send_message(cid, "Сброс настроек.", reply_markup=main_menu())

def build_prompt(tags):
    base = "nsfw, masterpiece, ultra detailed, anime style, best quality"
    # Кастомная логика для смешанных отверстий и дилдо
    prompt_parts = []

    holes_selected = [tag for tag in tags if tag in TAGS["holes"]]
    toys_selected = [tag for tag in tags if tag in TAGS["toys"]]

    # Если выбран "both" - заменяем на оба отверстия
    if "both" in holes_selected:
        holes_selected = ["vagina", "anal"]

    # Генерируем дилдо для обоих отверстий, если выбраны и отверстия и дилдо
    dildo_tags = {"dildo", "huge_dildo", "horse_dildo"}
    dildo_selected = [t for t in toys_selected if t in dildo_tags]

    # Убираем дилдо из toys, чтобы потом добавить с правильным описанием
    toys_wo_dildo = [t for t in toys_selected if t not in dildo_tags]

    # Формируем промты для отверстий
    for hole in holes_selected:
        prompt_parts.append(TAG_PROMPTS.get(hole, hole))

    # Для дилдо — добавляем в оба отверстия, если отверстия выбраны
    for dildo in dildo_selected:
        for hole in holes_selected:
            # "дилдо внутри вагины" или "дилдо внутри ануса"
            if hole == "vagina":
                prompt_parts.append(f"{TAG_PROMPTS.get(dildo)} внутри вагины")
            elif hole == "anal":
                prompt_parts.append(f"{TAG_PROMPTS.get(dildo)} внутри ануса")

    # Остальные игрушки
    for toy in toys_wo_dildo:
        prompt_parts.append(TAG_PROMPTS.get(toy, toy))

    # Остальные теги кроме holes и toys
    for tag in tags:
        if tag not in holes_selected and tag not in toys_selected:
            prompt_parts.append(TAG_PROMPTS.get(tag, tag))

    return base + ", " + ", ".join(prompt_parts)

def replicate_generate(prompt):
    url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {REPLICATE_TOKEN}",
        "Content-Type": "application/json"
    }
    json_data = {
        "version": REPLICATE_MODEL,
        "input": {"prompt": prompt}
    }
    r = requests.post(url, headers=headers, json=json_data)
    if r.status_code != 201:
        return None
    status_url = r.json()["urls"]["get"]

    for _ in range(60):
        time.sleep(2)
        r = requests.get(status_url, headers=headers)
        if r.status_code != 200:
            return None
        data = r.json()
        if data["status"] == "succeeded":
            return data["output"][0] if isinstance(data["output"],