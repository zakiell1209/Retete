# --- bot.py ---
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

# ID модели Replicate, которую вы используете
REPLICATE_MODEL = "c1d5b02687df6081c7953c74bcc527858702e8c153c9382012ccc3906752d3ec"

# Инициализация бота и Flask приложения
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
user_settings = {} # Словарь для хранения настроек пользователей

# Названия категорий для меню выбора тегов
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

# Словарь тегов, сгруппированных по категориям
TAGS = {
    "holes": {
        "vagina": "Вагина",
        "anal": "Анус",
        "both": "Вагина и анус",
        "prolapsed_uterus": "Выпавшая матка", 
        "prolapsed_anus": "Выпавший анус",     
        "dilated_anus": "Расширенный анус",    
        "dilated_vagina": "Расширенная киска"  
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
    }
}

# Дополнительные промпты для персонажей
CHARACTER_EXTRA = {
    "rias": "red long hair, blue eyes, pale skin, large breasts, rias gremory, highschool dxd",
    "akeno": "long black hair, purple eyes, large breasts, akeno himejima, highschool dxd",
    "kafka": "purple wavy hair, cold expression, kafka, honkai star rail",
    "eula": "light blue hair, fair skin, eula, genshin impact",
    "fu_xuan": "pink hair, fu xuan, honkai star rail",
    "ayase": "black hair, school uniform, ayase seiko"
}

# Полный список промптов для тегов
TAG_PROMPTS = {
    **CHARACTER_EXTRA,
    "vagina": "spread pussy",
    "anal": "spread anus",
    "both": "spread pussy and anus",
    "prolapsed_uterus": "prolapsed uterus, uterus exposed, visible uterus", 
    "prolapsed_anus": "prolapsed anus, anus exposed, visible anus",         
    "dilated_anus": "dilated anus, anus stretched, internal view of anus, anus gaping", 
    "dilated_vagina": "dilated vagina, vagina stretched, internal view of vagina, vagina gaping, spread pussy, labia spread", 
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
        "horizontal split, legs stretched fully to sides, pelvis on floor, thighs spread open, "
        "inner thighs visible, high detail"
    ),
    "ver_split": "vertical split",
    "side_up_leg": "on side with leg raised",
    "front_facing": "facing viewer",
    "back_facing": "back to viewer",
    "lying_knees_up": "legs up, knees bent",
    "bridge": "arched back bridge pose",
    "suspended": "suspended by ropes",
    "stockings": "wearing stockings only",
    "mask": "mask on face",
    "heels": "high heels with red soles",
    "shibari": "shibari ropes",
    "big_breasts": "big breasts",
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
    "futanari": "futanari girl with large breasts",
    "femboy": "male, boy, very feminine body, femboy, androgynous, flat chest, penis, testicles", # ОБНОВЛЕННЫЙ И УСИЛЕННЫЙ ПРОМПТ ДЛЯ ФЕМБОЯ
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
    "ecstasy_face": "ecstasy face",
    "gold_lipstick": "gold lipstick"
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
    user_settings[cid] = {"tags": [], "last_cat": None} # Инициализация настроек пользователя
    bot.send_message(cid, "Привет! Что делаем?", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    """Общий обработчик для всех кнопок колбэка."""
    cid = call.message.chat.id
    # Убедимся, что настройки для пользователя существуют
    if cid not in user_settings:
        user_settings[cid] = {"tags": [], "last_cat": None}

    data = call.data # Данные из колбэка кнопки

    if data == "choose_tags":
        bot.edit_message_text("Выбери категорию тегов:", cid, call.message.message_id, reply_markup=category_menu())

    elif data.startswith("cat_"):
        cat = data[4:] # Извлекаем название категории
        user_settings[cid]["last_cat"] = cat # Сохраняем последнюю выбранную категорию
        selected = user_settings[cid]["tags"] # Текущие выбранные теги
        bot.edit_message_text(f"Категория: {CATEGORY_NAMES[cat]}", cid, call.message.message_id, reply_markup=tag_menu(cat, selected))

    elif data.startswith("tag_"):
        _, cat, tag = data.split("_", 2) # Извлекаем категорию и тег
        tags = user_settings[cid]["tags"]
        if tag in tags:
            tags.remove(tag) # Если тег уже выбран, удаляем его
        else:
            tags.append(tag) # Иначе добавляем
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
        
        # Строим промпт и получаем информацию о его усечении
        prompt_info = build_prompt(tags)
        prompt = prompt_info["prompt"]
        truncated = prompt_info["truncated"]

        # Сохраняем исходные выбранные теги для кнопки "Изменить теги"
        user_settings[cid]["last_prompt_tags"] = tags.copy() 
        
        if truncated:
            bot.send_message(cid, "⚠️ **Внимание**: Некоторые теги были отброшены из-за превышения лимита длины запроса. Попробуйте выбрать меньше тегов для лучшего результата.", parse_mode="Markdown")
        
        bot.send_message(cid, "⏳ Генерация изображения...")
        url = replicate_generate(prompt) # Вызываем функцию генерации
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
        # Загружаем последние использованные теги для редактирования
        if "last_prompt_tags" in user_settings[cid]:
            user_settings[cid]["tags"] = user_settings[cid]["last_prompt_tags"]
            bot.send_message(cid, "Изменяем теги, использованные в предыдущей генерации:", reply_markup=category_menu())
        else:
            bot.send_message(cid, "Нет сохранённых тегов с предыдущей генерации. Сначала сделай генерацию.")

    elif data == "start":
        # Сброс настроек пользователя и возвращение в главное меню
        user_settings[cid] = {"tags": [], "last_cat": None}
        bot.send_message(cid, "Настройки сброшены. Начнем заново!", reply_markup=main_menu())

# --- Функция для построения промпта ---
def build_prompt(tags):
    """
    Строит промпт для модели Replicate на основе выбранных тегов.
    Управляет длиной промпта, чтобы избежать его усечения моделью.
    Формирует позитивный и негативный части промпта.
    """
    # Базовый позитивный промпт: сфокусирован на желаемом качестве
    base_positive = "nsfw, masterpiece, ultra detailed, anime style, best quality, fully nude, no clothing covering chest or genitals"
    
    # Базовый негативный промпт: что модель ДОЛЖНА ИЗБЕГАТЬ.
    # Используем синтаксис с весом (слово:число) для усиления
    base_negative = "bad anatomy, deformed, disfigured, poorly drawn face, poorly drawn hands, missing limbs, extra limbs, fused fingers, too many fingers, too few fingers, lowres, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, artist name, (hands on chest:1.5), (hands covering breasts:1.5), (hands covering crotch:1.5), (out of frame:1.2), (ugly:1.2), (femboy as girl:1.5)"

    positive_parts = []
    # Сортируем теги для обеспечения согласованности промпта
    sorted_tags = sorted(tags)
    
    for tag in sorted_tags:
        # Используем конкретный промпт из TAG_PROMPTS или сам тег в качестве запасного варианта
        prompt_segment = TAG_PROMPTS.get(tag, tag)
        positive_parts.append(prompt_segment)
    
    # Используем набор (set) для удаления дубликатов сегментов промпта
    unique_positive_parts = set(positive_parts)
    
    # Объединяем позитивные части
    final_positive_prompt_str = base_positive
    if unique_positive_parts:
        final_positive_prompt_str += ", " + ", ".join(unique_positive_parts)

    # Комбинируем позитивный и негативный промпт.
    # В этой модели нет отдельного параметра negative_prompt, поэтому добавляем его в конец.
    # Это распространенный способ для некоторых моделей, хотя и не идеальный.
    combined_prompt = f"{final_positive_prompt_str} AND {base_negative}"

    # --- УПРАВЛЕНИЕ ДЛИНОЙ ПРОМПТА ---
    # Максимально допустимая длина промпта.
    # Это важный параметр, который нужно будет регулировать экспериментально.
    MAX_PROMPT_LENGTH = 700  # Начнем с 700, возможно, потребуется корректировка
    truncated = False # Флаг, указывающий, был ли промпт усечен

    if len(combined_prompt) > MAX_PROMPT_LENGTH:
        truncated = True
        # Если промпт слишком длинный, мы сначала формируем позитивную часть,
        # а затем добавляем негативную, усекая ее при необходимости.
        
        # Разделяем на позитивную и негативную части для усечения
        current_positive_length = len(base_positive)
        truncated_positive_parts = [base_positive]

        for part in unique_positive_parts:
            if current_positive_length + len(part) + 2 <= MAX_PROMPT_LENGTH - len(f" AND {base_negative}"):
                truncated_positive_parts.append(part)
                current_positive_length += len(part) + 2
            else:
                break
        
        final_positive_prompt_str = ", ".join(truncated_positive_parts)
        
        # Теперь добавляем негативную часть, убедившись, что она помещается
        # Если вся комбинация все еще слишком длинная, возможно, придется усечь и негативную часть,
        # но это менее желательно. Сейчас просто пытаемся вставить ее.
        
        combined_prompt = f"{final_positive_prompt_str} AND {base_negative}"
        
        # Если даже после усечения позитивной части общий промпт все равно слишком длинный
        # (что маловероятно, если MAX_PROMPT_LENGTH достаточно большой),
        # то придется обрезать и негативную часть. Но пока оставляем так.
        if len(combined_prompt) > MAX_PROMPT_LENGTH:
            combined_prompt = combined_prompt[:MAX_PROMPT_LENGTH] # Грубое усечение, если уж совсем не помещается

    return {"prompt": combined_prompt, "truncated": truncated}

# --- Функция для генерации изображения через Replicate ---
def replicate_generate(prompt):
    """Отправляет запрос на генерацию изображения в Replicate API и ожидает результат."""
    url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {REPLICATE_TOKEN}",
        "Content-Type": "application/json"
    }
    json_data = {
        "version": REPLICATE_MODEL,
        "input": {"prompt": prompt}
    }
    
    # Отправка запроса на создание предсказания
    r = requests.post(url, headers=headers, json=json_data)
    if r.status_code != 201:
        print(f"Ошибка при отправке предсказания: {r.status_code} - {r.text}")
        return None
    
    status_url = r.json()["urls"]["get"] # URL для получения статуса предсказания

    # Ожидание завершения генерации (до 3 минут)
    for i in range(90): # Увеличено с 60 до 90 попыток (3 минуты)
        time.sleep(2) # Ожидание 2 секунды между попытками
        r = requests.get(status_url, headers=headers)
        if r.status_code != 200:
            print(f"Ошибка при получении статуса предсказания: {r.status_code} - {r.text}")
            return None
        data = r.json()
        if data["status"] == "succeeded":
            # Возвращаем URL первого изображения, если оно есть
            return data["output"][0] if isinstance(data["output"], list) and data["output"] else None
        elif data["status"] == "failed":
            print(f"Предсказание не удалось: {data.get('error', 'Сообщение об ошибке не предоставлено')}")
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
    # Убираем старый вебхук и устанавливаем новый
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    # Запускаем Flask приложение
    app.run(host="0.0.0.0", port=PORT)
