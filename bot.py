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

# ID модели Replicate, которую вы указали (из последнего кода)
REPLICATE_MODEL = "80441e2c32a55f2fcf9b77fa0a74c6c86ad7deac51eed722b9faedb253265cb4"

# Инициализация бота и Flask приложения
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
user_settings = {} # Словарь для хранения настроек пользователей

# --- Категории для меню (возвращены из предыдущих версий) ---
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

# --- Теги (возвращены из предыдущих версий) ---
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
        "lucifer_helltaker": "Люцифер (Helltaker)",
        "freya_danmachi": "Фрея (Danmachi)",
        "aphrodite_ragnarok": "Афродита (Повесть о конце света)",
        "hinata_naruto": "Хината (Наруто)",
        "tsunade_naruto": "Цунаде (Наруто)",
        "albedo_overlord": "Альбедо (Повелитель)",
        "shalltear_overlord": "Шалтир (Повелитель)",
        "yumeko_kakegurui": "Юмеко Джабами (Безумный азарт)",
        "kirari_kakegurui": "Кирари Момобами (Безумный азарт)",
        "mary_kakegurui": "Мэри Саотомэ (Безумный азарт)",
        "mei_mei_jujutsu": "Мэй Мэй (Магическая битва)"
    }
}

# --- Промпты для модели (возвращены из предыдущих версий) ---
CHARACTER_EXTRA = {
    "rias": "rias gremory, red long hair, blue eyes, pale skin, large breasts, highschool dxd",
    "akeno": "akeno himejima, long black hair, purple eyes, large breasts, highschool dxd",
    "kafka": "kafka, purple wavy hair, cold expression, honkai star rail",
    "eula": "eula, light blue hair, fair skin, genshin impact",
    "fu_xuan": "fu xuan, pink hair, honkai star rail",
    "yor_forger": "yor forger, spy x family, black hair, red dress",
    "2b_nier": "2b, nier automata, white hair, black dress",
    "esdeath": "esdeath, akame ga kill, blue hair, military uniform, high heels",
    "formidable": "formidable, azur lane, long white hair, dress",
    "sparkle": "sparkle, honkai star rail, pink hair, elegant dress, theatrical",
    "acheron": "acheron, honkai star rail, purple hair, long coat, samurai",
    "castoria": "castoria, fate grand order, white hair, dress, long sleeves",
    "lady_dimitrescu": "lady dimitrescu, resident evil, tall female, white dress, elegant hat, sharp claws, mature female",
    "chun_li": "chun li, street fighter, muscular thighs, qipao, hair buns",
    "atomic_heart_twins": "robot, twin sisters, black bodysuit, black hair, white hair, atomic heart",
    "yoruichi_shihoin": "yoruichi shihoin, bleach, dark skin, purple hair",
    "saber": "saber, artoria pendragon, fate series, blonde hair, blue dress",
    "mona": "mona, genshin impact, black hair, leotard, golden headdress",
    "klee": "klee, genshin impact, blonde hair, red dress, explosive",
    "raiden_shogun": "raiden shogun, genshin impact, purple hair, kimono, electro archon",
    "astolfo": "astolfo, fate series, pink hair, femboy, androgynous",
    "hestia": "hestia, danmachi, black hair, blue ribbons, white dress",
    "lucifer_helltaker": "lucifer, helltaker, long black hair, business suit",
    "freya_danmachi": "freya, danmachi, long silver hair, purple eyes, elegant dress",
    "aphrodite_ragnarok": "aphrodite, record of ragnarok, large breasts, blonde hair, revealing outfit",
    "hinata_naruto": "hinata hyuga, naruto, long dark blue hair, byakugan, shy, large breasts",
    "tsunade_naruto": "tsunade, naruto, blonde hair, large breasts, strong, medical ninja",
    "albedo_overlord": "albedo, overlord, succubus, black wings, white dress, long black hair",
    "shalltear_overlord": "shalltear bloodfallen, overlord, vampire, short blonde hair, frilly dress, parasol",
    "yumeko_kakegurui": "yumeko jabami, kakegurui, long black hair, red eyes, school uniform, insane smile",
    "kirari_kakegurui": "kirari momobami, kakegurui, white hair, blue lips, school uniform, student council president",
    "mary_kakegurui": "mary saotome, kakegurui, blonde hair, school uniform, twin tails",
    "mei_mei_jujutsu": "mei mei, jujutsu kaisen, long black hair, axe, confident expression"
}

TAG_PROMPTS = {
    **CHARACTER_EXTRA,
    "vagina": "spread pussy",
    "anus": "spread anus",
    "both": "spread pussy and anus",
    "dilated_anus": "dilated anus, anus stretched, open anus, internal view of anus, anus gaping",
    "dilated_vagina": "dilated vagina, vagina stretched, open pussy, internal view of vagina, vagina gaping, spread pussy, labia spread, realistic, detailed, high focus",
    "prolapsed_uterus": "prolapsed uterus, uterus exposed, visible uterus",
    "prolapsed_anus": "prolapsed anus, anus exposed, visible anus",
    "two_dildos_one_hole": "two dildos inserted, two dildos into one orifice",
    "dildo": "dildo inserted",
    "huge_dildo": "huge dildo",
    "horse_dildo": "horse dildo",
    "anal_beads": "anal beads inserted",
    "anal_plug": "anal plug",
    "long_dildo_path": (
        "dildo inserted into anus, pushing visibly through intestines with clear belly bulge, "
        "exiting from mouth, seamless and continuous dildo, consistent texture, realistic rubber"
    ),
    "doggy": "doggy style, on all fours, hands on floor",
    "squat": "squatting pose, hands behind head",
    "lying": "lying down",
    "hor_split": "horizontal split, legs stretched fully to sides, pelvis on floor, inner thighs visible",
    "ver_split": "vertical split, holding own raised leg",
    "on_back_legs_behind_head": "on back, legs behind head",
    "on_side_leg_up": "on side with leg raised",
    "suspended": "suspended",
    "front_facing": "front to viewer",
    "back_facing": "back to viewer",
    "top_down_view": "shot from above, top-down view",
    "bottom_up_view": "shot from below, bottom-up view",
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
    "futanari": "futanari",
    "femboy": "male, boy, very feminine body, femboy, androgynous, flat chest, penis, testicles, thin waist, wide hips, boyish hips, no breasts",
    "ethnicity_asian": "asian girl",
    "ethnicity_european": "european girl",
    "furry_cow": "furry cow girl, cow costume",
    "furry_cat": "furry cat girl, cat costume",
    "furry_dog": "furry dog girl, dog costume",
    "furry_dragon": "furry dragon girl, dragon costume",
    "furry_sylveon": "furry sylveon, sylveon costume, pink, ribbons, sexy",
    "furry_fox": "furry fox girl, fox costume",
    "furry_bunny": "furry bunny girl, bunny costume",
    "furry_wolf": "furry wolf girl, wolf costume",
    "ahegao": "ahegao face",
    "pain_face": "face in pain",
    "ecstasy_face": "ecstasy face",
    "gold_lipstick": "gold lipstick",
    "nipple_piercing": "nipple piercing",
    "clitoral_piercing": "clitoral piercing",
    "foot_fetish": "foot fetish",
    "footjob": "footjob",
    "mouth_nipples": "mouths instead of nipples",
    "reshiram": "reshiram, pokemon",
    "mew": "mew, pokemon",
    "mewtwo": "mewtwo, pokemon",
    "gardevoir": "gardevoir, pokemon"
}

# --- Функции для создания клавиатур (возвращены из предыдущих версий) ---
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

        # Используем функцию build_prompt для создания промптов из выбранных тегов
        prompt_info = build_prompt(tags)
        positive_prompt = prompt_info["positive_prompt"]
        negative_prompt = prompt_info["negative_prompt"]
        
        user_settings[cid]["last_prompt_tags"] = tags.copy()

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

# --- Функция для определения категории тега (возвращена из предыдущих версий) ---
def tag_category(tag):
    """Определяет категорию, к которой относится тег."""
    for cat, items in TAGS.items():
        if tag in items:
            if cat in ["body", "ethnos"]:
                return "body"
            if cat == "poses":
                return "pose"
            if cat == "holes":
                return "holes"
            if cat == "toys":
                return "toys"
            if cat == "clothes":
                return "clothes"
            if cat == "fetish":
                return "fetish"
            if cat == "head":
                return "face"
    return None

# --- Оптимизированная функция для построения промпта (возвращена из предыдущих версий) ---
def build_prompt(tags):
    """
    Строит промпт для модели Replicate на основе выбранных тегов,
    используя логику группировки и обработки конфликтов.
    """
    base = [
        "masterpiece", "best quality", "ultra detailed", "anime style", "highly detailed",
        "expressive eyes", "perfect lighting", "volumetric lighting", "fully nude", "solo"
    ]

    priority = {
        "character": [],
        "furry": [],
        "body": [],
        "pose": [],
        "holes": [],
        "toys": [],
        "clothes": [],
        "fetish": [],
        "face": []
    }
    
    base_negative = (
        "lowres, bad anatomy, bad hands, bad face, deformed, disfigured, poorly drawn, "
        "missing limbs, extra limbs, fused fingers, jpeg artifacts, signature, watermark, "
        "blurry, cropped, worst quality, low quality, text, error, mutated, censored, "
        "hands on chest, hands covering breasts, clothing covering genitals, shirt, bra, bikini, "
        "vagina not visible, anus not visible, penis not visible, bad proportions, "
        "all clothes, all clothing"
    )

    unique = set(tags)
    
    if "big_breasts" in unique and "small_breasts" in unique:
        unique.remove("small_breasts") 
    
    if "furry_cow" in unique:
        unique.discard("cow_costume") 

    for tag in unique:
        if tag in CHARACTER_EXTRA:
            priority["character"].append(CHARACTER_EXTRA[tag])
        elif tag.startswith("furry_"):
            priority["furry"].append(TAG_PROMPTS.get(tag, tag))
        elif tag in TAG_PROMPTS:
            key = tag_category(tag)
            if key:
                priority[key].append(TAG_PROMPTS[tag])

    prompt_parts = base[:]
    for section in ["character", "furry", "body", "pose", "holes", "toys", "clothes", "fetish", "face"]:
        prompt_parts.extend(priority[section])

    if "bikini_tan_lines" in unique:
        base_negative += ", bikini"

    return {
        "positive_prompt": ", ".join(prompt_parts),
        "negative_prompt": base_negative
    } 

# --- Функция для генерации изображения через Replicate (настройки из последнего кода) ---
def replicate_generate(prompt, negative_prompt):
    url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {REPLICATE_TOKEN}",
        "Content-Type": "application/json"
    }

    # Настройки модели взяты из последнего предоставленного вами кода
    json_data = {
        "version": REPLICATE_MODEL,
        "input": {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": 1024,
            "height": 1536,  # Высота из последнего кода
            "steps": 45,     # Шаги из последнего кода
            "cfg_scale": 12.5, # CFG Scale из последнего кода
            "scheduler": "DPM++ 2M SDE Karras", # Scheduler из последнего кода
            "clip_skip": 2, # Clip Skip из последнего кода
            "guidance_rescale": 1.0, # Guidance Rescale из последнего кода
            "refiner": True, # Refiner из последнего кода
            "refiner_strength": 0.45, # Refiner Strength из последнего кода
            "adetailer_face": True, # ADetailer Face из последнего кода
            "adetailer_hand": True, # ADetailer Hand из последнего кода
            "seed": -1
            # Обратите внимание: 'vae', 'prompt_conjunction', 'upscale', 'pag_scale' 
            # из предыдущей "оптимизированной" версии отсутствуют в вашем последнем коде.
            # Если они все еще нужны, их нужно добавить вручную в этот json_data['input'].
            # Я оставил только те параметры, которые были в вашем последнем предоставленном коде.
        }
    }

    try:
        r = requests.post(url, headers=headers, json=json_data)
        if r.status_code != 201:
            print("Ошибка при запуске:", r.text)
            return None

        status_url = r.json()["urls"]["get"]

        for _ in range(90): # Максимум 3 минуты ожидания (90 * 2 секунды)
            time.sleep(2)
            r = requests.get(status_url, headers=headers)
            data = r.json()
            if data["status"] == "succeeded":
                # Убедимся, что возвращаем первый элемент списка, если output - список
                return data["output"][0] if isinstance(data["output"], list) else data["output"]
            if data["status"] == "failed":
                print("Ошибка генерации:", data.get("error"))
                return None
        print("Превышено время ожидания")
        return None

    except Exception as e:
        print("Исключение:", str(e))
        return None

# Flask webhook
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
