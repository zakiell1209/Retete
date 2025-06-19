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
    "hor_split": (
        "one girl horizontal split, legs fully stretched on floor, pelvis touching floor, "
        "thighs spread open, inner thighs visible, no raised legs, realistic pose"
    ),
    "ver_split": (
        "one girl vertical split, legs straight up and down, pelvis aligned, realistic pose"
    ),
    "side_up_leg": "on side with leg raised",
    "front_facing": "facing viewer",
    "back_facing": "back to viewer",
    "lying_knees_up": "legs up, knees bent",
    "bridge": "arched back bridge pose",
    "suspended": "suspended by ropes, no male figure visible",
    "stockings": "wearing stockings only",
    "mask": "mask on face",
    "heels": "high heels with red soles",
    "shibari": "shibari ropes binding body, no hands covering breasts or genitals",
    "big_breasts": "very large breasts, fully visible, no hands covering",
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
    "cum": "cum covered",
    "belly_bloat": "belly bulge from toy",
    "succubus_tattoo": "succubus tattoo on lower abdomen",
    "futanari": "futanari girl with large breasts, erect penis, fully visible",
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
    "gold_lipstick": "gold lipstick on lips only"
}

# Negative prompts to reduce undesired elements (like hands on chest)
NEGATIVE_PROMPT = (
    "hands covering breasts, hands covering nipples, hands covering genitals, "
    "two girls, multiple girls, men in background, male figure, "
    "blurred, distorted, low quality, text, watermark"
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
        prompt, negative_prompt = build_prompt(tags)
        user_settings[cid]["last_prompt"] = tags.copy()
        bot.send_message(cid, "⏳ Генерирую изображение...")
        image_url = replicate_generate(prompt, negative_prompt)
        if image_url:
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("🔄 Начать заново", callback_data="choose_tags"))
            kb.add(types.InlineKeyboardButton("✏️ Редактировать теги", callback_data="choose_tags"))
            bot.send_photo(cid, image_url, reply_markup=kb)
        else:
            bot.send_message(cid, "Ошибка генерации изображения. Попробуй позже.")

def build_prompt(tags):
    # Добавим персонажей в начало с детальными описаниями
    prompt_parts = []
    negative_parts = [NEGATIVE_PROMPT]

    # Собираем детализированные промпты по тегам
    for tag in tags:
        if tag in TAG_PROMPTS:
            prompt_parts.append(TAG_PROMPTS[tag])
        else:
            # На случай неизвестного тега - просто название
            prompt_parts.append(tag)

    # Корректировки для шпагатов и персонажей:
    if "hor_split" in tags:
        # Убедимся, что только одна девушка в горизонтальном шпагате с ногами на полу
        prompt_parts.append("one girl horizontal split, legs fully on floor, pelvis touching floor, realistic anatomy, no extra figures")
    if "ver_split" in tags:
        prompt_parts.append("one girl vertical split, legs straight up and down, pelvis aligned, realistic anatomy")
    # Убираем руки с груди и груди закрывающие объекты
    negative_parts.append("hands on breasts, hands covering nipples, clothes covering breasts, objects covering breasts")
    negative_parts.append("hands on vagina or anus")

    # Убедимся, что при обзорах теги влияют на точку обзора
    if "view_far" in tags:
        # Требуем видеть всю фигуру
        prompt_parts.append("full body visible, entire figure in frame, clear view")

    prompt = ", ".join(prompt_parts)
    negative_prompt = ", ".join(negative_parts)
    return prompt, negative_prompt

def replicate_generate(prompt, negative_prompt):
    headers = {
        "Authorization": f"Token {REPLICATE_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "version": REPLICATE_MODEL,
        "input": {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "num_inference_steps": 40,
            "guidance_scale": 7.5,
            "width": 512,
            "height": 512,
            "seed": None
        }
    }
    try:
        response = requests.post(
            "https://api.replicate.com/v1/predictions",
            headers=headers,
            json=data,
            timeout=60
        )
        response.raise_for_status()
        prediction = response.json()
        prediction_id = prediction["id"]

        # Ожидаем завершения
        for _ in range(60):
            time.sleep(1)
            status_resp = requests.get(f"https://api.replicate.com/v1/predictions/{prediction_id}", headers=headers)
            status_resp.raise_for_status()
            status_json = status_resp.json()
            if status_json["status"] == "succeeded":
                return status_json["output"][0]
            if status_json["status"] == "failed":
                return None
        return None
    except Exception as e:
        print("Replicate error:", e)
        return None

@app.route("/", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=PORT)