import os
import time
import requests
import logging
from flask import Flask, request
import telebot
from telebot import types

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
API_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 5000))
REPLICATE_MODEL = "c1d5b02687df6081c7953c74bcc527858702e8c153c9382012ccc3906752d3ec"

# Инициализация бота и приложения
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
user_settings = {}

# Базы данных тегов
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
    }
}

# Группы исключающих тегов
EXCLUSIVE_GROUPS = {
    "breast_size": ["big_breasts", "small_breasts"],
    "body_type": ["body_fat", "body_thin", "body_normal", "body_fit", "body_muscular"],
    "skin_color": ["skin_white", "skin_black"],
    "age": ["age_loli", "age_milf", "age_21"]
}

# Функции меню
def main_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🧩 Выбрать теги", callback_data="choose_tags"),
        types.InlineKeyboardButton("🎨 Генерировать", callback_data="generate"),
        types.InlineKeyboardButton("ℹ Помощь", callback_data="help")
    )
    return kb

def category_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for key, name in CATEGORY_NAMES.items():
        buttons.append(types.InlineKeyboardButton(name, callback_data=f"cat_{key}"))
    kb.add(*buttons)
    kb.add(types.InlineKeyboardButton("✅ Готово", callback_data="done_tags"))
    return kb

def tag_menu(category, selected_tags):
    kb = types.InlineKeyboardMarkup(row_width=2)
    
    if category not in TAGS:
        return kb
    
    for tag_key, tag_name in TAGS[category].items():
        emoji = "✅ " if tag_key in selected_tags else ""
        kb.add(types.InlineKeyboardButton(
            f"{emoji}{tag_name}",
            callback_data=f"tag_{category}_{tag_key}"
        ))
    
    kb.add(types.InlineKeyboardButton(
        "⬅ Назад",
        callback_data="back_to_cat"
    ))
    
    return kb

# Обработчики команд
@bot.message_handler(commands=["start"])
def start(msg):
    cid = msg.chat.id
    user_settings[cid] = {"tags": [], "last_cat": None}
    bot.send_message(cid, "Привет! Что делаем?", reply_markup=main_menu())

# Обработчики callback-запросов
@bot.callback_query_handler(func=lambda call: call.data == "help")
def show_help(call):
    help_text = (
        "📚 <b>Инструкция по использованию бота:</b>\n\n"
        "1. Нажмите '🧩 Выбрать теги' для выбора параметров генерации\n"
        "2. Выберите нужные категории и теги\n"
        "3. Нажмите '🎨 Генерировать' для создания изображения\n\n"
        "⏳ Генерация обычно занимает 1-2 минуты\n"
        "🔄 Вы можете изменить теги и сгенерировать заново"
    )
    bot.edit_message_text(
        help_text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "choose_tags")
def choose_tags_handler(call):
    cid = call.message.chat.id
    if cid not in user_settings:
        user_settings[cid] = {"tags": [], "last_cat": None}
    
    try:
        bot.edit_message_text(
            "Выбери категорию тегов:",
            chat_id=cid,
            message_id=call.message.message_id,
            reply_markup=category_menu()
        )
    except Exception as e:
        logger.error(f"Error in choose_tags_handler: {str(e)}")
        bot.answer_callback_query(call.id, "⚠ Ошибка обновления меню")

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def category_handler(call):
    cid = call.message.chat.id
    category = call.data.split("_", 1)[1]
    
    if cid not in user_settings:
        user_settings[cid] = {"tags": [], "last_cat": None}
    
    user_settings[cid]["last_cat"] = category
    
    try:
        bot.edit_message_text(
            f"Категория: {CATEGORY_NAMES.get(category, '???')}",
            chat_id=cid,
            message_id=call.message.message_id,
            reply_markup=tag_menu(category, user_settings[cid]["tags"])
        )
    except Exception as e:
        logger.error(f"Error in category_handler: {str(e)}")
        bot.answer_callback_query(call.id, "⚠ Ошибка загрузки тегов")

@bot.callback_query_handler(func=lambda call: call.data.startswith("tag_"))
def tag_handler(call):
    cid = call.message.chat.id
    _, category, tag = call.data.split("_", 2)
    
    if cid not in user_settings:
        user_settings[cid] = {"tags": [], "last_cat": None}
    
    tags = user_settings[cid]["tags"]
    
    if tag in tags:
        tags.remove(tag)
    else:
        tags.append(tag)
    
    try:
        bot.edit_message_reply_markup(
            chat_id=cid,
            message_id=call.message.message_id,
            reply_markup=tag_menu(category, tags)
        )
    except Exception as e:
        logger.error(f"Error in tag_handler: {str(e)}")
        bot.answer_callback_query(call.id, "⚠ Ошибка обновления тегов")

@bot.callback_query_handler(func=lambda call: call.data == "back_to_cat")
def back_to_cat_handler(call):
    cid = call.message.chat.id
    try:
        bot.edit_message_text(
            "Выбери категорию:",
            chat_id=cid,
            message_id=call.message.message_id,
            reply_markup=category_menu()
        )
    except Exception as e:
        logger.error(f"Error in back_to_cat_handler: {str(e)}")
        bot.answer_callback_query(call.id, "⚠ Ошибка возврата")

@bot.callback_query_handler(func=lambda call: call.data == "done_tags")
def done_tags_handler(call):
    cid = call.message.chat.id
    try:
        bot.edit_message_text(
            "Теги сохранены. Что дальше?",
            chat_id=cid,
            message_id=call.message.message_id,
            reply_markup=main_menu()
        )
    except Exception as e:
        logger.error(f"Error in done_tags_handler: {str(e)}")
        bot.answer_callback_query(call.id, "⚠ Ошибка сохранения")

# Остальные функции (build_prompt, replicate_generate) остаются без изменений

if __name__ == "__main__":
    logger.info("Starting bot...")
    try:
        if WEBHOOK_URL:
            bot.remove_webhook()
            time.sleep(1)
            bot.set_webhook(url=WEBHOOK_URL)
            app.run(host="0.0.0.0", port=PORT)
        else:
            bot.infinity_polling()
    except Exception as e:
        logger.error(f"Bot crashed: {str(e)}")
        raise