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

CATEGORY_NAMES = {
    "holes": "Отверстия",
    "toys": "Игрушки",
    "poses": "Позы",
    "clothes": "Одежда",
    "body": "Тело",
    "ethnos": "Этнос",
    "furry": "Фури",
    "characters": "Персонажи",
    "head": "Голова",
    "view": "Обзор"
}

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
        "piercing": "Пирсинг",
        "long_dildo_path": "Дилдо из ануса выходит изо рта"
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
        "lying_knees_up": "Лежа с согнутыми коленями",
        "bridge": "Мост",
        "suspended": "Подвешена"
    },
    "clothes": {
        "stockings": "Чулки",
        "bikini_tan_lines": "Загар от бикини",
        "mask": "Маска",
        "heels": "Каблуки",
        "shibari": "Шибари"
    },
    "body": {
        "big_breasts": "Большая грудь",
        "small_breasts": "Маленькая грудь",
        "skin_white": "Белая кожа",
        "skin_black": "Чёрная кожа",
        "body_fat": "Пышное тело",
        "body_thin": "Худое тело",
        "body_normal": "Нормальное тело",
        "body_fit": "Подтянутое тело",
        "body_muscular": "Мускулистое тело",
        "age_loli": "Лоли",
        "age_milf": "Милфа",
        "age_21": "Возраст 21",
        "cum": "Вся в сперме",
        "belly_bloat": "Вздутие живота",
        "succubus_tattoo": "Тату внизу живота"
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
        "furry_sylveon": "Фури сильвеон",
        "furry_fox": "Фури лисица",
        "furry_bunny": "Фури кролик",
        "furry_wolf": "Фури волчица"
    },
    "characters": {
        "rias": "Риас Гремори",
        "akeno": "Акено Химедзима",
        "kafka": "Кафка (Хонкай)",
        "eula": "Еола (Геншин)",
        "fu_xuan": "Фу Сюань (Хонкай)",
        "ayase": "Аясе Сейко",
        "qiyana": "Киана (Лига Легенд)",
        "chun_li": "Чун Ли (Стрит Файтер)",
        "yor": "Йор Форджер"
    },
    "head": {
        "ahegao": "Ахегао",
        "pain_face": "Лицо в боли",
        "ecstasy_face": "Лицо в экстазе",
        "gold_lipstick": "Золотая помада"
    },
    "view": {
        "view_below": "Снизу",
        "view_above": "Сверху",
        "view_side": "С боку",
        "view_far": "Дальше",
        "view_close": "Ближе"
    }
}

CHARACTER_EXTRA = {
    "rias": "red long hair, blue eyes, pale skin, large breasts, rias gremory, highschool dxd, no hands covering chest",
    "akeno": "long black hair, purple eyes, large breasts, akeno himejima, highschool dxd, no hands covering chest",
    "kafka": "purple wavy hair, cold expression, kafka, honkai star rail, no hands covering chest",
    "eula": "light blue hair, fair skin, eula, genshin impact, no hands covering chest",
    "fu_xuan": "pink hair, fu xuan, honkai star rail, no hands covering chest",
    "ayase": "black hair, school uniform, ayase seiko, no hands covering chest",
    "qiyana": (
        "tan skin, athletic body, white short hair, green markings on face, golden headdress, emerald eyes, "
        "qiyana from league of legends, wielding a circular blade, fierce expression, no hands covering chest"
    ),
    "chun_li": (
        "chun-li from street fighter, muscular thighs, blue qipao dress with gold trim, spiked bracelets, "
        "black hair in twin buns, white boots, asian face, intense gaze, no hands covering chest"
    ),
    "yor": (
        "yor forger from spy x family, long black hair, red eyes, elegant assassin dress, black stockings, "
        "red rose hairpin, slender body, anime style, pale skin, mysterious expression, no hands covering chest"
    )
}

TAG_PROMPTS = {
    **CHARACTER_EXTRA,
    "vagina": "spread pussy",
    "anal": "spread anus",
    "both": "spread pussy and anus",
    "dildo": "dildo inserted",
    "huge_dildo": "huge dildo",
    "horse_dildo": "horse dildo",
    "anal_beads": "anal beads inserted",
    "anal_plug": "anal plug",
    "anal_expander": "anal expander stretching anus",
    "gag": "ball gag",
    "piercing": "nipple and genital piercings",
    "long_dildo_path": (
        "dildo inserted into anus, pushing visibly through intestines with clear belly bulge, "
        "exiting from mouth, seamless and continuous dildo, consistent texture, realistic rubber"
    ),
    "doggy": "doggy style",
    "standing": "standing pose",
    "splits": "doing a split",
    "squat": "squat pose",
    "lying": "lying pose",
    "hor_split": (
        "one girl in horizontal split, legs fully stretched on floor, pelvis down, inner thighs visible, "
        "no other figures, no raised leg, no side lying, realistic pose"
    ),
    "ver_split": "vertical split, one girl standing with one leg raised straight up",
    "side_up_leg": "lying on side with one leg raised straight up",
    "front_facing": "facing viewer",
    "back_facing": "back to viewer",
    "lying_knees_up": "lying with knees bent and legs up",
    "bridge": "arched back bridge pose",
    "suspended": "suspended by ropes, hands and feet bound",
    "stockings": "wearing stockings only",
    "mask": "mask on face",
    "heels": "high heels with red soles",
    "shibari": "shibari ropes, body fully tied, no hands covering chest",
    "big_breasts": "big breasts, fully visible, no hands covering",
    "small_breasts": "small breasts",
    "skin_white": "white skin",
    "skin_black": "black skin",
    "body_fat": "curvy body",
    "body_thin": "thin body",
    "body_normal": "average body",
    "body_fit": "fit body",
    "body_muscular": "muscular body",
    "age_loli": "loli",
    "age_milf": "milf",
    "age_21": "age 21",
    "cum": "covered in semen",
    "belly_bloat": "belly bulge from toy",
    "succubus_tattoo": "succubus tattoo on lower abdomen",
    "futanari": "futanari girl with large breasts",
    "femboy": "femboy with feminine body",
    "ethnicity_asian": "asian girl",
    "ethnicity_european": "european girl",
    "furry_cow": "furry cow girl",
    "furry_cat": "furry cat girl",
    "furry_dog": "furry dog girl",
    "furry_dragon": "furry dragon girl",
    "furry_sylveon": "furry sylveon, pink, ribbons, sexy",
    "furry_fox": "furry fox girl",
    "furry_bunny": "furry bunny girl",
    "furry_wolf": "furry wolf girl",
    "ahegao": "ahegao face",
    "pain_face": "face in pain",
    "ecstasy_face": "face in ecstasy",
    "gold_lipstick": "gold lipstick",
    "view_below": "view from below, looking up at figure",
    "view_above": "view from above, looking down at figure",
    "view_side": "side view of figure",
    "view_far": "full body visible, clear view from distance",
    "view_close": "close-up, partial body visible, parts out of frame"
}

def main_menu():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🧩 Выбрать теги", callback_data="choose_tags"))
    kb.add(types.InlineKeyboardButton("🎨 Генерировать", callback_data="generate"))
    kb.add(types.InlineKeyboardButton("🔢 Выбрать количество", callback_data="choose_count"))
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

def count_menu():
    kb = types.InlineKeyboardMarkup(row_width=3)
    for n in range(1, 5):
        kb.add(types.InlineKeyboardButton(str(n), callback_data=f"count_{n}"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="main_menu"))
    return kb

@bot.message_handler(commands=["start"])
def start(msg):
    cid = msg.chat.id
    user_settings[cid] = {"tags": [], "last_cat": None, "last_prompt": None, "count": 1}
    bot.send_message(cid, "Привет! Что делаем?", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    cid = call.message.chat.id
    if cid not in user_settings:
        user_settings[cid] = {"tags": [], "last_cat": None, "last_prompt": None, "count": 1}

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
        if tag in tags:
            tags.remove(tag)
        else:
            tags.append(tag)
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
        user_settings[cid]["last_prompt"] = tags.copy()
        bot.send_message(cid, "⏳ Генерация изображения...")
        count = user_settings[cid].get("count", 1)
        urls = []
        for _ in range(count):
            url = replicate_generate(prompt)
            if url:
                urls.append(url)
        if urls:
            kb = types.InlineKeyboardMarkup()
            kb.add(
                types.InlineKeyboardButton("Начать заново", callback_data="reset"),
                types.InlineKeyboardButton("Редактировать теги", callback_data="choose_tags"),
                types.InlineKeyboardButton("Сгенерировать ещё", callback_data="generate")
            )
            media_group = []
            for url in urls:
                # Отправляем фото с spoiler (спойлером)
                media_group.append(types.InputMediaPhoto(media=url, spoiler=True))
            bot.send_media_group(cid, media_group)
            bot.send_message(cid, "Выберите действие:", reply_markup=kb)
        else:
            bot.send_message(cid, "Ошибка генерации. Попробуйте позже.")

    elif data == "reset":
        user_settings[cid]["tags"] = []
        user_settings[cid]["last_prompt"] = None
        bot.edit_message_text("Начнём заново.", cid, call.message.message_id, reply_markup=main_menu())

    elif data == "choose_count":
        bot.edit_message_text("Выберите количество изображений для генерации:", cid, call.message.message_id, reply_markup=count_menu())

    elif data.startswith("count_"):
        n = int(data.split("_")[1])
        user_settings[cid]["count"] = n
        bot.edit_message_text(f"Количество изображений установлено: {n}", cid, call.message.message_id, reply_markup=main_menu())

    elif data == "main_menu":
        bot.edit_message_text("Привет! Что делаем?", cid, call.message.message_id, reply_markup=main_menu())

def build_prompt(tags):
    prompt_parts = []
    for tag in tags:
        if tag in TAG_PROMPTS:
            prompt_parts.append(TAG_PROMPTS[tag])
    # Строго запрещаем руки, закрывающие грудь и интимные места, и добавим negative prompt в replicate_generate
    prompt_parts.append("no hands covering breasts or nipples")
    prompt_parts.append("no hands on genitalia")
    prompt_parts.append("realistic, high quality, detailed")
    return ", ".join(prompt_parts)

def replicate_generate(prompt):
    headers = {
        "Authorization": f"Token {REPLICATE_TOKEN}",
        "Content-Type": "application/json",
    }
    # Добавим негативный prompt для еще более строгого контроля
    negative_prompt = ("hands, finger, arm, hand covering breasts, hand covering genitalia, "
                       "blurry, low quality, watermark, text, logo")

    json_data = {
        "version": REPLICATE_MODEL,
        "input": {
            "prompt": prompt,
            "negative_prompt": negative_prompt
        },
    }
    try:
        response = requests.post("https://api.replicate.com/v1/predictions", headers=headers, json=json_data)
        response.raise_for_status()
        prediction = response.json()
        prediction_id = prediction["id"]

        status = ""
        while status not in ("succeeded", "failed"):
            time.sleep(1.5)
            r = requests.get(f"https://api.replicate.com/v1/predictions/{prediction_id}", headers=headers)
            r.raise_for_status()
            prediction = r.json()
            status = prediction["status"]

        if status == "succeeded":
            image_url = prediction["output"][0] if isinstance(prediction["output"], list) else prediction["output"]
            return image_url
        else:
            return None
    except Exception as e:
        print("Error generating image:", e)
        return None

@app.route('/', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

def set_webhook():
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=WEBHOOK_URL)

if __name__ == '__main__':
    set_webhook()
    app.run(host='0.0.0.0', port=PORT)