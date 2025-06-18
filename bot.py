import os
import time
import requests
from telebot import TeleBot, types

# Токены из переменных окружения
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")

bot = TeleBot(BOT_TOKEN)

# Модель Replicate
REPLICATE_MODEL = "aitechtree/nsfw-novel-generation"

# Категории и теги

CATEGORY_NAMES = {
    "body": "Тело",
    "toys": "Игрушки",
    "ethnos": "Этнос",
    "furry": "Фури",
    "characters": "Персонажи",
    "head": "Голова",
    "holes": "Отверстия",
    "poses": "Позы",
    "view": "Обзор"
}

# Теги с четкими промтами для генерации (пример, можно дополнять)

TAGS = {
    "body": {
        "big_breasts": "большая грудь",
        "small_breasts": "маленькая грудь",
        "black_skin": "чёрная кожа",
        "white_skin": "белая кожа",
        "slim": "стройное телосложение",
        "young": "молодая"
    },
    "toys": {
        "anal_dildo": "анальный дилдо одного цвета и текстуры, без визуализации прохождения внутри",
        "dildo_anus_to_mouth": "дилдо одного цвета и размера, выходящее из ануса и изо рта, без эффекта прохода внутри тела",
        "piercing": "пирсинг",
        "cow_costume": "чулки, рога и хвост коровы (без трусов и лифчика)"
    },
    "ethnos": {
        "asian": "азиатка",
        "european": "европейка",
        "futanari": "футанари",
        "femboy": "фембой"
    },
    "furry": {
        "fox": "фури-лисица",
        "rabbit": "фури-кролик",
        "wolf": "фури-волчица",
        "furry_queen": "фури-королева",
        "furry_cat": "фури-кошка",
        "furry_dog": "фури-собака",
        "furry_dragon": "фури-дракон",
        "furry_sylveon": "фури-сильвеон"
    },
    "characters": {
        "rias_gremory": "Риас Гремори, красные волосы, большие груди, из аниме Демоны старшей школы",
        "akeno_himemizima": "Акено Химедзима, из аниме Демоны старшей школы, с синими волосами и характерным костюмом",
        "kafka": "Кафка из Хонкай Стар Рейл, характерная внешность, короткие волосы",
        "eola": "Еола из Геншин Импакт, блондинка с голубыми глазами",
        "fu_xuan": "Фу Сюань из Хонкай Стар Рейл",
        "ayase_seiko": "Аясе Сейко, из соответствующего аниме"
    },
    "head": {
        "ahegao": "ахегао",
        "face_pain": "лицо скривившееся от боли",
        "face_ecstasy": "лицо в экстазе",
        "golden_lipstick": "золотая помада для губ"
    },
    "holes": {
        "vagina": "вагина",
        "anus": "анус",
        "mouth": "рот"
    },
    "poses": {
        "doggy": "поза наездницы (догги-стайл)",
        "standing": "стоя",
        "splits": "шпагат простой",
        "hor_split": "горизонтальный шпагат, девушка сидит с ногами в стороны на полу, спина ровная",
        "ver_split": "вертикальный шпагат, девушка с вытянутыми ногами вверх",
        "squat": "приседание",
        "lying": "лежа",
        "side_up_leg": "на боку с поднятой ногой",
        "front_facing": "лицом к зрителю",
        "back_facing": "спиной к зрителю",
        "lying_knees_up": "лежа с раздвинутыми согнутыми коленями",
        "bridge": "мост",
        "suspended": "подвешена на верёвках"
    },
    "view": {
        "top_view": "вид сверху",
        "bottom_view": "вид снизу",
        "side_view": "вид сбоку"
    }
}

# Хранилище данных пользователя в памяти (можно заменить на БД)
user_data = {}

# Формируем клавиатуру выбора категории
def category_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    for key, name in CATEGORY_NAMES.items():
        kb.add(types.InlineKeyboardButton(name, callback_data=f"cat_{key}"))
    kb.add(types.InlineKeyboardButton("✅ Готово", callback_data="done_tags"))
    return kb

# Формируем клавиатуру тегов для категории
def tag_menu(category, selected_tags):
    kb = types.InlineKeyboardMarkup(row_width=2)
    if category not in TAGS:
        return kb
    for tag, prompt in TAGS[category].items():
        text = f"{tag} ✅" if tag in selected_tags else tag
        kb.add(types.InlineKeyboardButton(text, callback_data=f"tag_{category}_{tag}"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="back_to_cat"))
    return kb

# Основное меню
def main_menu():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("📝 Изменить теги", callback_data="choose_tags"),
        types.InlineKeyboardButton("▶ Генерировать", callback_data="generate")
    )
    return kb

# Строим промт из тегов — без конфликтов, с точным объединением
def build_prompt(tags):
    prompt_parts = []
    # Добавим персонализированные промты для персонажей, если есть
    if any(tag in TAGS["characters"] for tag in tags):
        for tag in tags:
            if tag in TAGS["characters"]:
                prompt_parts.append(TAGS["characters"][tag])
        # Удаляем теги персонажей, чтобы не дублировать
        tags = [t for t in tags if t not in TAGS["characters"]]
    # Добавляем остальные теги
    for tag in tags:
        # Ищем в какой категории тег
        found = False
        for cat, cat_tags in TAGS.items():
            if tag in cat_tags and tag not in prompt_parts:
                prompt_parts.append(cat_tags[tag])
                found = True
                break
        if not found:
            prompt_parts.append(tag)  # если не найден, просто добавляем тег как есть
    return ", ".join(prompt_parts)

# Генерация через replicate
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
    try:
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
                return data["output"][0] if isinstance(data["output"], list) else data["output"]
            elif data["status"] == "failed":
                return None
        return None
    except Exception as e:
        print(f"Ошибка генерации: {e}")
        return None

# Обработка команд /start
@bot.message_handler(commands=["start"])
def start(message):
    cid = message.chat.id
    user_data[cid] = {"tags": [], "last_cat": None}
    bot.send_message(cid, "Добро пожаловать! Выбери теги для генерации:", reply_markup=category_menu())

# Обработка callback кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    cid = call.message.chat.id
    if cid not in user_data:
        user_data[cid] = {"tags": [], "last_cat": None}
    data = call.data
    tags = user_data[cid]["tags"]

    if data == "choose_tags":
        bot.edit_message_text("Выбери категорию тегов:", cid, call.message.message_id, reply_markup=category_menu())

    elif data.startswith("cat_"):
        cat = data[4:]
        if cat not in TAGS:
            bot.answer_callback_query(call.id, "Пустая категория или ошибка.")
            return
        user_data[cid]["last_cat"] = cat
        bot.edit_message_text(f"Категория: {CATEGORY_NAMES.get(cat, cat)}", cid, call.message.message_id, reply_markup=tag_menu(cat, tags))

    elif data.startswith("tag_"):
        _, cat, tag = data.split("_", 2)
        if tag in tags:
            tags.remove(tag)
        else:
            tags.append(tag)
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=tag_menu(cat, tags))

    elif data == "back_to_cat":
        bot.edit_message_text("Выбери категорию тегов:", cid, call.message.message_id, reply_markup=category_menu())

    elif data == "done_tags":
        bot.edit_message_text("Теги сохранены.\nДля продолжения нажми Генерировать", cid, call.message.message_id, reply_markup=main_menu())

    elif data == "generate":
        if not tags:
            bot.answer_callback_query(call.id, "Сначала выберите теги.")
            return
        prompt = build_prompt(tags)
        bot.edit_message_text("⏳ Генерация изображения, пожалуйста подождите...", cid, call.message.message_id)
        url = replicate_generate(prompt)
        if url:
            kb = types.InlineKeyboardMarkup(row_width=1)
            kb.add(
                types.InlineKeyboardButton("🔁 Начать заново", callback_data="start_over"),
                types.InlineKeyboardButton("🔧 Изменить теги", callback_data="choose_tags"),
                types.InlineKeyboardButton("➡ Продолжить с этими тегами", callback_data="generate")
            )
            bot.send_photo(cid, url, caption=f"✅ Готово!\nПромт: {prompt}", reply_markup=kb)
        else:
            bot.send_message(cid, "❌ Ошибка генерации. Попробуйте снова.")

    elif data == "start_over":
        user_data[cid] = {"tags": [], "last_cat": None}
        bot.send_message(cid, "Настройки сброшены. Начни заново.", reply_markup=category_menu())

    else:
        bot.answer_callback_query(call.id, "Неизвестная команда.")

if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()