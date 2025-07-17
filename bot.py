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
REPLICATE_MODEL = "80441e2c32a55f2fcf9b77fa0a74c6c86ad7deac51eed722b9faedb253265cb4"

# Инициализация бота и Flask приложения
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
user_settings = {} # Словарь для хранения настроек пользователей

# --- Категории для меню ---
CATEGORY_NAMES = {
    "holes": "🕳️ Отверстия",
    "toys": "🧸 Игрушки",
    "poses": "🧘 Позы",
    "clothes": "👗 Одежда",
    "body": "💪 Тело",
    "ethnos": "🌍 Этнос",
    "furry": "🐾 Фури",
    "characters": "🦸 Персонажи",
    "head": "🤯 Голова",
    "fetish": "🔗 Фетиши",
    "pokemon": "⚡ Покемоны"
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
        "belly_bloat": "Вздутие живота (похоже на беременность)",
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
        "mei_mei_jujutsu": "Мэй Мэй (Магическая битва)",
        "jessie_pokemon": "Джесси (Покемоны)",
        "lusamine_pokemon": "Лусамине (Покемоны)",
        "umbreon_pokemon": "Эмбреон (Покемоны)",
        "lugia_pokemon": "Лугия (Покемоны)",
        "shadow_lugia_pokemon": "Шадоу Лугия (Покемоны)",
        "lopunny_pokemon": "Лопанни (Покемоны)",
        "goodra_pokemon": "Гудра (Покемоны)",
        "paimon_genshin": "Паймон (Genshin Impact)",
        "ellen_joe_zzz": "Эллен Джо (Zenless Zone Zero)",
        "mirelia_melromarc": "Мирелия К. Мелромарк (Герой Щита)",
        "malty_melromarc": "Малти С. Мелромарк (Герой Щита)",
        "xenovia_quarta": "Ксеновия Кварта (Демоны старшей школы)",
        "serafall_leviathan": "Серафалл Левиафан (Демоны старшей школы)",
        "asia_argento": "Азия Ардженто (Демоны старшей школы)",
        "koneko_toujou": "Конеко Тодзё (Демоны старшей школы)",
        "shidou_irina": "Шидо Ирина (Демоны старшей школы)",
        "gasper_vladi": "Гаспер Влади (Демоны старшей школы)",
        "rossweisse_dxd": "Россвайссе (Демоны старшей школы)",
        "yasaka_dxd": "Ясака (High School DxD)",
        "grayfia_lucifuge": "Грейфия Люцифуг (Демоны старшей школы)"
    }
}

# --- Промпты для модели ---
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
    "mei_mei_jujutsu": "mei mei, jujutsu kaisen, long black hair, axe, confident expression",
    # --- Новые персонажи с промптами ---
    "jessie_pokemon": "jessie, pokemon, team rocket, red hair, long hair, ponytail",
    "lusamine_pokemon": "lusamine, pokemon, aether foundation, blonde hair, long hair, dress",
    "umbreon_pokemon": "umbreon, pokemon, dark type, quadruped, black fur, yellow rings",
    "lugia_pokemon": "lugia, pokemon, legendary pokemon, psychic type, flying type, white body, blue fins",
    "shadow_lugia_pokemon": "shadow lugia, pokemon, legendary pokemon, dark type, flying type, corrupted, dark aura",
    "lopunny_pokemon": "lopunny, pokemon, normal type, fighting type, rabbit, furry, long ears, fluffy tail",
    "goodra_pokemon": "goodra, pokemon, dragon type, gooey, slimy skin, soft body",
    "paimon_genshin": "paimon, genshin impact, floating companion, small body, white hair, crown, emergency food",
    "ellen_joe_zzz": "ellen joe, zenless zone zero, long blonde hair, school uniform, glasses, student",
    "mirelia_melromarc": "mirelia q melromarc, the rising of the shield hero, queen, blonde hair, elegant dress",
    "malty_melromarc": "malty s melromarc, the rising of the shield hero, bitch, cruel smile, red hair, blonde hair, princess, villainess",
    "xenovia_quarta": "xenovia quarta, highschool dxd, blue hair, short hair, sword, holy sword, devil wings, nun uniform",
    "serafall_leviathan": "serafall leviathan, highschool dxd, magical girl outfit, pink hair, magical wand, devil, large breasts",
    "asia_argento": "asia argento, highschool dxd, blonde hair, long hair, nun, innocent, healing magic, dragon slayer, devil wings",
    "koneko_toujou": "koneko toujou, highschool dxd, white hair, cat ears, cat tail, small breasts, stoic expression",
    "shidou_irina": "shidou irina, highschool dxd, blonde hair, twin tails, energetic, holy sword, angel wings, exorcist",
    "gasper_vladi": "gasper vladi, highschool dxd, male, trap, feminine clothing, long blonde hair, shy, vampire, crossdresser",
    "rossweisse_dxd": "rossweisse, highschool dxd, valkyrie, long silver hair, glasses, mature, large breasts",
    "yasaka_dxd": "yasaka, highschool dxd, kitsune, nine tails, fox ears, kimono, mature woman",
    "grayfia_lucifuge": "grayfia lucifuge, highschool dxd, maid outfit, long silver hair, red eyes, ice magic, sexy maid"
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
        # Убедитесь, что название категории отображается со смайликом
        category_display_name = CATEGORY_NAMES.get(cat, cat)
        bot.edit_message_text(f"Категория: {category_display_name}", cid, call.message.message_id, reply_markup=tag_menu(cat, selected))

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

# --- Функция для определения категории тега ---
def tag_category(tag):
    """Определяет категорию, к которой относится тег."""
    for cat, items in TAGS.items():
        if tag in items:
            if cat in ["body", "ethnos"]: # Объединяем "body" и "ethnos" в одну категорию "body" для приоритетов
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
            if cat == "head": # "head" для лица
                return "face"
            if cat == "pokemon":
                return "pokemon"
            if cat == "characters": # Добавлено для распознавания категории персонажей
                return "character"
    return None

# --- Оптимизированная функция для построения промпта ---
def build_prompt(tags):
    """
    Строит промпт для модели Replicate на основе выбранных тегов,
    используя новую логику группировки и обработки конфликтов.
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
        "face": [],
        "pokemon": []
    }
    
    base_negative = (
        "lowres, bad anatomy, bad hands, bad face, deformed, disfigured, poorly drawn, "
        "missing limbs, extra limbs, fused fingers, jpeg artifacts, signature, watermark, "
        "blurry, cropped, worst quality, low quality, text, error, mutated, censored, "
        "hands on chest, hands covering breasts, clothing covering genitals, shirt, bra, bikini, "
        "vagina not visible, anus not visible, penis not visible, bad proportions, "
        "all clothes, all clothing" # Добавлено для усиления удаления одежды
    )

    # Уникальные теги и спец. обработка конфликтов
    unique = set(tags)
    
    # Приоритет большим грудям
    if "big_breasts" in unique and "small_breasts" in unique:
        unique.remove("small_breasts") 
    
    # Костюм коровы уже включён в furry_cow
    if "furry_cow" in unique:
        unique.discard("cow_costume") 

    # Группировка по категориям
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
    # Порядок добавления важен: персонажи, фури, покемоны, тело, позы, отверстия, игрушки, одежда, фетиши, лицо
    for section in ["character", "furry", "pokemon", "body", "pose", "holes", "toys", "clothes", "fetish", "face"]:
        prompt_parts.extend(priority[section])

    # Танлайны убирают купальник из негативного промпта
    if "bikini_tan_lines" in unique:
        base_negative += ", bikini"

    return {
        "positive_prompt": ", ".join(prompt_parts),
        "negative_prompt": base_negative
    } 

# --- Функция для генерации изображения через Replicate ---
def replicate_generate(positive_prompt, negative_prompt):
    """
    Отправляет запрос на генерацию изображения в Replicate API,
    используя оптимальные настройки для достижения максимальной точности.
    """
    url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {REPLICATE_TOKEN}",
        "Content-Type": "application/json"
    }
    json_data = {
        "version": REPLICATE_MODEL,
        "input": {
            "prompt": positive_prompt,
            "negative_prompt": negative_prompt,
            "prepend_preprompt": False,
            "width": 1024,
            "height": 1024,
            "steps": 75,
            "guidance_scale": 18,
            "scheduler": "DPM++ 2M SDE Karras",
            "adetailer_face": True,
            "adetailer_hand": True,
            "seed": -1
        }
    }

    # Отправка запроса на создание предсказания
    r = requests.post(url, headers=headers, json=json_data)
    if r.status_code != 201:
        print(f"Ошибка при отправке предсказания: {r.status_code} - {r.text}")
        print(f"Request JSON: {json_data}")
        return None

    status_url = r.json()["urls"]["get"]

    # Ожидание завершения генерации (до 3 минут)
    for i in range(90):
        time.sleep(2)
        r = requests.get(status_url, headers=headers)
        if r.status_code != 200:
            print(f"Ошибка при получении статуса предсказания: {r.status_code} - {r.text}")
            return None
        data = r.json()
        if data["status"] == "succeeded":
            return data["output"][0] if isinstance(data["output"], list) and data["output"] else None
        elif data["status"] == "failed":
            print(f"Предсказание не удалось: {data.get('error', 'Сообщение об ошибке не предоставлено')}")
            print(f"Request JSON: {json_data}")
            return None

    print("Время ожидания предсказания истекло.")
    return None

# --- Настройка вебхука Flask ---
@app.route("/", methods=["POST"])
def webhook():
    """Обрабатывает входящие обновления от Telegram."""
    json_str = request.stream.read().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "ok", 200

@app.route("/", methods=["GET"])
def home():
    """Простой маршрут для проверки работы приложения."""
    return "бот работает", 200

# --- Запуск бота ---
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=PORT)
