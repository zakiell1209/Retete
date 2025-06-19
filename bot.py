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
        "ayase": "Аясе Сейко"
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
        "view_side": "Сбоку",
        "view_far": "Дальше",
        "view_close": "Ближе"
    }
}

CHARACTER_EXTRA = {
    "rias": "red long hair, blue eyes, pale skin, large breasts, rias gremory, highschool dxd",
    "akeno": "long black hair, purple eyes, large breasts, akeno himejima, highschool dxd",
    "kafka": "purple wavy hair, cold expression, kafka, honkai star rail",
    "eula": "light blue hair, fair skin, eula, genshin impact",
    "fu_xuan": "pink hair, fu xuan, honkai star rail",
    "ayase": "black hair, school uniform, ayase seiko"
}

# Улучшенные промты, чтобы убрать руки с груди и усилить позы (горизонтальный и вертикальный шпагат)

TAG_PROMPTS = {
    **CHARACTER_EXTRA,
    "vagina": "spread pussy, fully visible, no obstruction",
    "anal": "spread anus, fully visible, no obstruction",
    "both": "spread pussy and anus, fully visible, no obstruction",
    "dildo": "dildo inserted, fully visible, no hands or objects covering body parts",
    "huge_dildo": "huge dildo, fully visible, no obstruction",
    "horse_dildo": "horse dildo, fully visible",
    "anal_beads": "anal beads inserted, no obstruction",
    "anal_plug": "anal plug, fully visible",
    "anal_expander": "anal expander stretching anus, no hands covering",
    "gag": "ball gag on mouth",
    "piercing": "nipple and genital piercings fully visible",
    "long_dildo_path": (
        "dildo inserted into anus, pushing visibly through intestines with clear belly bulge, "
        "exiting from mouth, seamless and continuous dildo, consistent texture, realistic rubber, no hands"
    ),
    "doggy": "doggy style pose, no hands covering breasts or genitals",
    "standing": "standing pose, no hands on chest",
    "splits": "doing a split, legs fully extended, no obstruction, no hands on chest",
    "hor_split": (
        "horizontal split, legs stretched fully to sides, pelvis on floor, thighs spread open, "
        "inner thighs visible, high detail, legs flat on floor, no legs raised, no hands on chest"
    ),
    "ver_split": (
        "vertical split, legs straight up and down, fully visible, no obstruction, no hands on chest"
    ),
    "side_up_leg": "on side with leg raised, no hands on chest",
    "front_facing": "facing viewer, no hands on chest",
    "back_facing": "back to viewer, no hands on chest",
    "lying_knees_up": "legs up, knees bent, no hands on chest",
    "bridge": "arched back bridge pose, no hands covering body",
    "suspended": "suspended by ropes, no hands covering chest",
    "stockings": "wearing stockings only, no obstruction",
    "mask": "mask on face",
    "heels": "high heels with red soles",
    "shibari": "shibari ropes, no hands covering chest",
    "big_breasts": "very large breasts, fully visible, no hands covering",
    "small_breasts": "small breasts, fully visible",
    "skin_white": "white skin",
    "skin_black": "black skin",
    "body_fat": "curvy body",
    "body_thin": "thin body",
    "body_normal": "average body",
    "body_fit": "fit body",
    "body_muscular": "muscular body",
    "age_loli": "loli girl, fully visible",
    "age_milf": "milf woman, fully visible",
    "age_21": "age 21",
    "cum": "cum covered, visible",
    "belly_bloat": "belly bulge from toy, visible",
    "succubus_tattoo": "succubus tattoo on lower abdomen",
    "futanari": "futanari girl with large breasts, no hands covering body",
    "femboy": "femboy with feminine body",
    "ethnicity_asian": "asian girl",
    "ethnicity_european": "european girl",
    "furry_cow": "furry cow girl, no hands covering",
    "furry_cat": "furry cat girl, no hands covering",
    "furry_dog": "furry dog girl, no hands covering",
    "furry_dragon": "furry dragon girl, no hands covering",
    "furry_sylveon": "furry sylveon, pink, ribbons, sexy, no hands covering",
    "furry_fox": "furry fox girl, no hands covering",
    "furry_bunny": "furry bunny girl, no hands covering",
    "furry_wolf": "furry wolf girl, no hands covering",
    "ahegao": "ahegao face",
    "pain_face": "face in pain",
    "ecstasy_face": "face in ecstasy",
    "gold_lipstick": "gold lipstick on lips only",
    "view_below": "viewpoint from below, showing body pressed against surface, no obstruction",
    "view_above": "viewpoint from above, full body visible",
    "view_side": "side view of full body",
    "view_far": "full body visible from distance, no clipping",
    "view_close": "close up view, partial body visible, no obstruction"
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
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back"))
    return kb

def tags_menu(category, user_id):
    kb = types.InlineKeyboardMarkup(row_width=2)
    selected = user_settings.get(user_id, {}).get("tags", [])
    for tag, desc in TAGS[category].items():
        text = f"{desc}"
        if tag in selected:
            text = "✅ " + text
        kb.add(types.InlineKeyboardButton(text, callback_data=f"tag_{tag}"))
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_cat"))
    kb.add(types.InlineKeyboardButton("Готово", callback_data="done_tags"))
    return kb

def build_prompt(user_id):
    tags = user_settings.get(user_id, {}).get("tags", [])
    prompt_parts = []

    # Если выбран персонаж — добавляем расширенное описание персонажа
    for tag in tags:
        if tag in CHARACTER_EXTRA:
            prompt_parts.append(CHARACTER_EXTRA[tag])
    # Добавляем остальные теги с улучшенными промптами
    for tag in tags:
        if tag in TAG_PROMPTS and tag not in CHARACTER_EXTRA:
            prompt_parts.append(TAG_PROMPTS[tag])

    # Убираем руки с груди/сосков — всегда
    prompt_parts.append("no hands covering breasts or nipples or genitals")

    prompt = ", ".join(prompt_parts)
    return prompt

def generate_image(prompt):
    headers = {
        "Authorization": f"Token {REPLICATE_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "version": REPLICATE_MODEL,
        "input": {
            "prompt": prompt,
            "num_inference_steps": 50,
            "guidance_scale": 7.5
        }
    }
    response = requests.post("https://api.replicate.com/v1/predictions", headers=headers, json=data)
    if response.status_code != 201:
        return None, f"Ошибка генерации: {response.status_code} {response.text}"
    prediction = response.json()
    prediction_url = f"https://api.replicate.com/v1/predictions/{prediction['id']}"

    # Ждём результата
    for _ in range(60):
        time.sleep(1)
        r = requests.get(prediction_url, headers=headers)
        rj = r.json()
        if rj.get("status") == "succeeded":
            image_url = rj["output"][0]
            return image_url, None
        if rj.get("status") == "failed":
            return None, "Ошибка генерации: модель вернула ошибку"
    return None, "Ошибка генерации: время ожидания истекло"

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.from_user.id
    if user_id not in user_settings:
        user_settings[user_id] = {"tags": []}
    bot.send_message(message.chat.id, "Привет! Используй меню для выбора тегов и генерации.", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id

    if call.data == "choose_tags":
        bot.edit_message_text("Выберите категорию тегов:", call.message.chat.id, call.message.message_id, reply_markup=category_menu())
    elif call.data.startswith("cat_"):
        cat = call.data[4:]
        if cat in TAGS:
            bot.edit_message_text(f"Выберите теги в категории {CATEGORY_NAMES[cat]}:", call.message.chat.id, call.message.message_id, reply_markup=tags_menu(cat, user_id))
        else:
            bot.answer_callback_query(call.id, "Категория не найдена")
    elif call.data.startswith("tag_"):
        tag = call.data[4:]
        settings = user_settings.setdefault(user_id, {"tags": []})
        if tag in settings["tags"]:
            settings["tags"].remove(tag)
        else:
            settings["tags"].append(tag)
        # Обновляем меню тегов в той же категории
        for cat_key, cat_tags in TAGS.items():
            if tag in cat_tags:
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=tags_menu(cat_key, user_id))
                break
        bot.answer_callback_query(call.id)
    elif call.data == "done_tags":
        tags = user_settings.get(user_id, {}).get("tags", [])
        tags_list = ", ".join([TAGS[cat].get(tag, tag) for cat in TAGS for tag in tags if tag in TAGS[cat]])
        bot.edit_message_text(f"Вы выбрали теги:\n{tags_list}", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
    elif call.data == "generate":
        tags = user_settings.get(user_id, {}).get("tags", [])
        if not tags:
            bot.answer_callback_query(call.id, "Вы не выбрали теги для генерации")
            return
        bot.edit_message_text("Генерирую изображение, подождите...", call.message.chat.id, call.message.message_id)
        prompt = build_prompt(user_id)
        image_url, err = generate_image(prompt)
        if err:
            bot.send_message(call.message.chat.id, err)
        else:
            bot.send_photo(call.message.chat.id, image_url, caption=f"Сгенерировано по тегам:\n{prompt}")
        bot.send_message(call.message.chat.id, "Выберите действие:", reply_markup=main_menu())
    elif call.data == "back":
        bot.edit_message_text("Главное меню", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
    elif call.data == "back_to_cat":
        bot.edit_message_text("Выберите категорию тегов:", call.message.chat.id, call.message.message_id, reply_markup=category_menu())
    else:
        bot.answer_callback_query(call.id, "Неизвестная команда")

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