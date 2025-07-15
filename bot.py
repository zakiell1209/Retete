import os
import time
import requests
from flask import Flask, request
import telebot
from telebot import types

# Получение токенов и URL из переменных окружения
API_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 5000))

# ID новой модели Replicate, которую вы используете
REPLICATE_MODEL = "e28ab49ae4c4fb92f9646c221d2aec239cbd461f1bcbee45c8e792aa8c95e133"

# Инициализация бота и Flask приложения
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
user_settings = {} # Словарь для хранения настроек пользователей

# --- Категории для меню ---
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
    "fetish": "Фетиши",
    "pokemon": "Покемоны"
}

# --- Теги с новыми добавлениями ---
TAGS = {
    "holes": {
        "vagina": "Вагина",
        "anus": "Анус",
        "both": "Вагина и анус",
        "dilated_anus": "Расширенный анус",
        "dilated_vagina": "Расширенная киска",
        "prolapsed_uterus": "Выпавшая матка",
        "prolapsed_anus": "Выпавший анус",
        "two_dildos_one_hole": "Два дилдо в одно отверстие"
    },
    "toys": {
        "dildo": "Дилдо",
        "huge_dildo": "Большое дилдо",
        "horse_dildo": "Конский дилдо",
        "anal_beads": "Анальные шарики",
        "anal_plug": "Анальная пробка",
        "long_dildo_path": "Дилдо сквозь все тело"
    },
    "poses": {
        "doggy": "На четвереньках",
        "standing": "Стоя",
        "squat": "Приседание",
        "lying": "Лежа",
        "hor_split": "Горизонтальный шпагат",
        "ver_split": "Вертикальный шпагат",
        "on_back_legs_behind_head": "На спине ноги за головой",
        "on_side_leg_up": "На боку нога вверх",
        "suspended": "Подвешена",
        "front_facing": "Вид спереди",
        "back_facing": "Вид сзади",
        "top_down_view": "Вид сверху",
        "bottom_up_view": "Вид снизу",
        "hands_spreading_vagina": "Руки раздвигают влагалище"
    },
    "clothes": {
        "stockings": "Чулки обычные",
        "stockings_fishnet": "Чулки сеточкой",
        "bikini_tan_lines": "Линии от загара в бикини",
        "shibari": "Шибари",
        "cow_costume": "Костюм коровы"
    },
    "body": {
        "big_breasts": "Большая грудь",
        "small_breasts": "Маленькая грудь",
        "body_fit": "Подтянутое тело",
        "body_fat": "Пышное тело",
        "body_muscular": "Мускулистое тело",
        "age_loli": "Лоли",
        "age_milf": "Милфа",
        "age_21": "21 год",
        "cum": "Вся в сперме",
        "belly_bloat": "Вздутие живота(похоже на беременность)",
        "succubus_tattoo": "Татуировка суккуба"
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
    "head": {
        "ahegao": "Ахегао",
        "pain_face": "Лицо в боли",
        "ecstasy_face": "Лицо в экстазе",
        "gold_lipstick": "Золотая помада"
    },
    "fetish": {
        "nipple_piercing": "Пирсинг сосков",
        "clitoral_piercing": "Пирсинг клитора",
        "foot_fetish": "Футфетиш",
        "footjob": "Футджоб",
        "mouth_nipples": "Вместо сосков рты"
    },
    "pokemon": {
        "reshiram": "Реширам",
        "mew": "Мю",
        "mewtwo": "Мюту",
        "gardevoir": "Гардевуар"
    },
    "characters": {
        "rias": "Риас Грегори",
        "akeno": "Акено Химеджима",
        "kafka": "Кафка",
        "eula": "Еола",
        "fu_xuan": "Фу Сюань",
        "yor_forger": "Йор Форджер",
        "2b_nier": "2B (NieR Automata)",
        "esdeath": "Есдес",
        "formidable": "Formidable",
        "sparkle": "Искорка",
        "acheron": "Геоцина",
        "castoria": "Кастория",
        "lady_dimitrescu": "Леди Димитреску",
        "chun_li": "Чун Ли",
        "atomic_heart_twins": "Близняшки (Atomic Heart)",
        "yoruichi_shihoin": "Шихоин Йориичи",
        "saber": "Сейбер",
        "mona": "Мона",
        "klee": "Кли",
        "raiden_shogun": "Райден",
        "astolfo": "Астольфо",
        "hestia": "Гестия",
        "lucifer_helltaker": "Люцифер (Helltaker)"
    }
}

# --- Промпты для модели ---
CHARACTER_EXTRA = {
    "rias": "red long hair, blue eyes, pale skin, large breasts, rias gremory, highschool dxd",
    "akeno": "long black hair, purple eyes, large breasts, akeno himejima, highschool dxd",
    "kafka": "purple wavy hair, cold expression, kafka, honkai star rail",
    "eula": "light blue hair, fair skin, eula, genshin impact",
    "fu_xuan": "pink hair, fu xuan, honkai star rail",
    "yor_forger": "yor forger, spy x family, black hair, red dress",
    "2b_nier": "2b, nier automata, white hair, black dress",
    "esdeath": "esdeath, akame ga kill, blue hair, military uniform, high heels",
    "formidable": "formidable, azur lane, long white hair, dress",
    "sparkle": "sparkle, honkai star rail, pink hair, elegant dress, theatrical",
    "acheron": "(acheron:1.2), (honkai star rail:1.2), purple hair, long coat, samurai",
    "castoria": "(castoria:1.2), (fate grand order:1.2), white hair, dress, long sleeves",
    "lady_dimitrescu": "lady dimitrescu, resident evil, tall female, white dress, elegant hat, sharp claws, mature female",
    "chun_li": "chun li, street fighter, muscular thighs, qipao, hair buns",
    "atomic_heart_twins": "(robot:1.5), (twin sisters:1.5), (black bodysuit:1.5), (black hair, white hair:1.5), atomic heart",
    "yoruichi_shihoin": "yoruichi shihoin, bleach, dark skin, purple hair",
    "saber": "saber, artoria pendragon, fate series, blonde hair, blue dress",
    "mona": "mona, genshin impact, black hair, leotard, golden headdress",
    "klee": "klee, genshin impact, blonde hair, red dress, explosive",
    "raiden_shogun": "raiden shogun, genshin impact, purple hair, kimono, electro archon",
    "astolfo": "astolfo, fate series, pink hair, femboy, androgynous",
    "hestia": "hestia, danmachi, black hair, blue ribbons, white dress",
    "lucifer_helltaker": "lucifer, helltaker, long black hair, business suit"
}

TAG_PROMPTS = {
    **CHARACTER_EXTRA,
    "vagina": "spread pussy",
    "anus": "spread anus",
    "both": "spread pussy and anus",
    "dilated_anus": "(dilated anus:1.5), (anus stretched:1.5), internal view of anus, anus gaping",
    "dilated_vagina": "(dilated vagina:1.5), (vagina stretched:1.5), internal view of vagina, vagina gaping, spread pussy, labia spread, realistic, detailed, high focus",
    "prolapsed_uterus": "prolapsed uterus, uterus exposed, visible uterus",
    "prolapsed_anus": "prolapsed anus, anus exposed, visible anus",
    "two_dildos_one_hole": "(two dildos inserted:1.5), (two dildos into one orifice:1.5)",
    "dildo": "dildo inserted",
    "huge_dildo": "huge dildo",
    "horse_dildo": "horse dildo",
    "anal_beads": "anal beads inserted",
    "anal_plug": "anal plug",
    "long_dildo_path": (
        "dildo inserted into anus, pushing visibly through intestines with clear belly bulge, "
        "exiting from mouth, seamless and continuous dildo, consistent texture, realistic rubber"
    ),
    "doggy": "doggy style, on all fours",
    "squat": "squatting pose",
    "lying": "lying down",
    "hor_split": "(horizontal split:1.2), (legs stretched fully to sides:1.2), pelvis on floor, inner thighs visible",
    "ver_split": "(vertical split:1.2)",
    "on_back_legs_behind_head": "on back, legs behind head",
    "on_side_leg_up": "on side with leg raised",
    "suspended": "suspended",
    "front_facing": "front to viewer",
    "back_facing": "back to viewer",
    "top_down_view": "(shot from above:1.5), (top-down view:1.5)",
    "bottom_up_view": "(shot from below:1.5), (bottom-up view:1.5)",
    "hands_spreading_vagina": "hands spreading vagina",
    "stockings": "wearing stockings only",
    "stockings_fishnet": "fishnet stockings",
    "bikini_tan_lines": "bikini tan lines",
    "shibari": "shibari ropes",
    "cow_costume": "cow costume, cow ears, cow horns, cow tail, wearing stockings only",
    "big_breasts": "big breasts",
    "small_breasts": "small breasts",
    "body_fit": "fit body",
    "body_fat": "curvy body",
    "body_muscular": "muscular body",
    "age_loli": "loli",
    "age_milf": "milf",
    "age_21": "age 21",
    "cum": "cum covered",
    "belly_bloat": "belly bulge, pregnant looking belly",
    "succubus_tattoo": "succubus tattoo on lower abdomen",
    "futanari": "(futanari:1.7)",
    "femboy": "male, boy, very feminine body, femboy, androgynous, flat chest, penis, testicles, thin waist, wide hips, boyish hips, no breasts",
    "ethnicity_asian": "asian girl",
    "ethnicity_european": "european girl",
    "furry_cow": "(furry cow girl:1.2), (cow costume:1.2)",
    "furry_cat": "(furry cat girl:1.2), (cat costume:1.2)",
    "furry_dog": "(furry dog girl:1.2), (dog costume:1.2)",
    "furry_dragon": "(furry dragon girl:1.2), (dragon costume:1.2)",
    "furry_sylveon": "(furry sylveon:1.2), (sylveon costume:1.2), pink, ribbons, sexy",
    "furry_fox": "(furry fox girl:1.2), (fox costume:1.2)",
    "furry_bunny": "(furry bunny girl:1.2), (bunny costume:1.2)",
    "furry_wolf": "(furry wolf girl:1.2), (wolf costume:1.2)",
    "ahegao": "ahegao face",
    "pain_face": "face in pain",
    "ecstasy_face": "ecstasy face",
    "gold_lipstick": "gold lipstick",
    "nipple_piercing": "nipple piercing",
    "clitoral_piercing": "clitoral piercing",
    "foot_fetish": "foot fetish",
    "footjob": "footjob",
    "mouth_nipples": "(mouths instead of nipples:2.0)",
    "reshiram": "reshiram, pokemon",
    "mew": "mew, pokemon",
    "mewtwo": "mewtwo, pokemon",
    "gardevoir": "gardevoir, pokemon"
}

# --- Функции для создания клавиатур ---
def main_menu():
    """Создает главное меню бота."""
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🧩 Выбрать теги", callback_data="choose_tags"))
    kb.add(types.InlineKeyboardButton("🎨 Генерировать", callback_data="generate"))
    return kb

def category_menu():
    """Создает меню выбора категорий тегов."""
    kb = types.InlineKeyboardMarkup(row_width=2)
    for key, name in CATEGORY_NAMES.items():
        kb.add(types.InlineKeyboardButton(name, callback_data=f"cat_{key}"))
    kb.add(types.InlineKeyboardButton("✅ Готово", callback_data="done_tags"))
    return kb

def tag_menu(category, selected_tags):
    """Создает меню выбора тегов внутри определенной категории."""
    kb = types.InlineKeyboardMarkup(row_width=2)
    for tag_key, tag_name in TAGS[category].items():
        label = f"✅ {tag_name}" if tag_key in selected_tags else tag_name
        kb.add(types.InlineKeyboardButton(label, callback_data=f"tag_{category}_{tag_key}"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="back_to_cat"))
    return kb

# --- Обработчики сообщений и колбэков ---
@bot.message_handler(commands=["start"])
def start(msg):
    """Обработчик команды /start."""
    cid = msg.chat.id
    user_settings[cid] = {"tags": [], "last_cat": None}
    bot.send_message(cid, "Привет! Что делаем?", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    """Общий обработчик для всех кнопок колбэка."""
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

        prompt_info = build_prompt(tags)
        positive_prompt = prompt_info["positive_prompt"]
        negative_prompt = prompt_info["negative_prompt"]
        truncated = prompt_info["truncated"]

        user_settings[cid]["last_prompt_tags"] = tags.copy()

        if truncated:
            bot.send_message(cid, "⚠️ **Внимание**: Некоторые теги были отброшены из-за превышения лимита длины запроса. Попробуйте выбрать меньше тегов для лучшего результата.", parse_mode="Markdown")

        bot.send_message(cid, "⏳ Генерация изображения...")
        url = replicate_generate(positive_prompt, negative_prompt)
        if url:
            kb = types.InlineKeyboardMarkup()
            kb.add(
                types.InlineKeyboardButton("🔁 Начать заново", callback_data="start"),
                types.InlineKeyboardButton("🔧 Изменить теги", callback_data="edit_tags"),
                types.InlineKeyboardButton("➡ Продолжить с этими", callback_data="generate")
            )
            bot.send_photo(cid, url, caption="✅ Готово!", reply_markup=kb)
        else:
            bot.send_message(cid, "❌ Ошибка генерации. Пожалуйста, попробуйте еще раз.")

    elif data == "edit_tags":
        if "last_prompt_tags" in user_settings[cid]:
            user_settings[cid]["tags"] = user_settings[cid]["last_prompt_tags"]
            bot.send_message(cid, "Изменяем теги, использованные в предыдущей генерации:", reply_markup=category_menu())
        else:
            bot.send_message(cid, "Нет сохранённых тегов с предыдущей генерации. Сначала сделай генерацию.")

    elif data == "start":
        user_settings[cid] = {"tags": [], "last_cat": None}
        bot.send_message(cid, "Настройки сброшены. Начнем заново!", reply_markup=main_menu())

# --- Функция для построения промпта ---
def build_prompt(tags):
    """
    Строит промпт для модели Replicate на основе выбранных тегов.
    """
    base_positive = "masterpiece, best quality, ultra detailed, anime style, highly detailed, expressive eyes, perfect lighting, volumetric lighting, fully nude, no clothing covering chest or genitals, solo"
    base_negative = (
        "lowres, bad anatomy, bad hands, bad face, deformed, disfigured, "
        "poorly drawn face, poorly drawn hands, missing limbs, extra limbs, "
        "fused fingers, too many fingers, too few fingers, "
        "jpeg artifacts, signature, watermark, username, blurry, artist name, "
        "cropped, worst quality, low quality, normal quality, "
        "extra_digit, fewer_digits, text, error, "
        "mutated hands and fingers, bad hand, malformed hands, "
        "long neck, bad nose, bad mouth, "
        "(hands on chest:3.0), (hands covering breasts:3.0), (hands on breasts)"
    )

    positive_tags = []
    negative_tags = []
    truncated = False

    for tag in tags:
        prompt = TAG_PROMPTS.get(tag)
        if prompt:
            if "hands on chest" in prompt or "femboy" in prompt:
                # Пример логики, если нужно добавлять в негативный промпт
                # Сейчас все идет в позитивный, но я оставлю это для примера
                positive_tags.append(prompt)
            else:
                positive_tags.append(prompt)

    positive_prompt = f"{base_positive}, {', '.join(positive_tags)}"
    # Проверка на лимит (примерный)
    if len(positive_prompt) > 2048:
        positive_prompt = positive_prompt[:2048]
        truncated = True

    return {
        "positive_prompt": positive_prompt,
        "negative_prompt": base_negative,
        "truncated": truncated
    }

# --- Функция для генерации на Replicate ---
def replicate_generate(positive_prompt, negative_prompt):
    """
    Отправляет запрос на генерацию изображения в Replicate.
    """
    headers = {
        "Authorization": f"Token {REPLICATE_TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "version": REPLICATE_MODEL,
        "input": {
            "prompt": positive_prompt,
            "negative_prompt": negative_prompt,
            "width": 768,
            "height": 768
        }
    }

    try:
        response = requests.post("https://api.replicate.com/v1/predictions", headers=headers, json=data)
        response.raise_for_status()
        prediction_id = response.json().get("id")

        if not prediction_id:
            print("Ошибка: Не удалось получить ID предсказания.")
            return None

        # Ожидаем завершения генерации
        for _ in range(30): # Попытки ожидания
            time.sleep(3)
            status_response = requests.get(f"https://api.replicate.com/v1/predictions/{prediction_id}", headers=headers)
            status = status_response.json().get("status")

            if status == "succeeded":
                output_url = status_response.json()["output"][0]
                return output_url
            elif status == "failed":
                print("Генерация не удалась.")
                return None

        print("Таймаут ожидания генерации.")
        return None

    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса к Replicate: {e}")
        return None

# --- Настройка вебхука и запуск ---
@app.route("/", methods=["GET", "POST"])
def webhook():
    """Обработчик вебхука для Telegram."""
    if request.method == "POST":
        update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
        bot.process_new_updates([update])
        return "OK", 200
    else:
        return "Bot is running on webhook.", 200

def set_webhook():
    """Устанавливает вебхук для бота."""
    try:
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=WEBHOOK_URL)
        print(f"Webhook установлен: {WEBHOOK_URL}")
    except Exception as e:
        print(f"Ошибка при установке вебхука: {e}")

if __name__ == "__main__":
    if WEBHOOK_URL:
        set_webhook()
        app.run(host="0.0.00.0", port=PORT)
    else:
        print("WEBHOOK_URL не установлен. Запуск в режиме long polling...")
        bot.polling(none_stop=True)
