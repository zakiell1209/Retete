import os
import time
import requests
import logging
from flask import Flask, request
import telebot
from telebot import types
from collections import defaultdict
from datetime import datetime, timedelta

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
user_activity = defaultdict(list)
user_stats = defaultdict(lambda: {"total": 0, "success": 0})

# Группы взаимоисключающих тегов
EXCLUSIVE_GROUPS = {
    "breast_size": ["big_breasts", "small_breasts"],
    "body_type": ["body_fat", "body_thin", "body_normal", "body_fit", "body_muscular"],
    "skin_color": ["skin_white", "skin_black"],
    "age": ["age_loli", "age_milf", "age_21"]
}

# Категории и теги
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

# Промты для тегов
TAG_PROMPTS = {
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
    "long_dildo_path": "dildo inserted into anus, pushing visibly through intestines with clear belly bulge, exiting from mouth, seamless and continuous dildo, consistent texture, realistic rubber",
    "doggy": "doggy style",
    "standing": "standing pose",
    "splits": "doing a split",
    "hor_split": "horizontal split, legs stretched fully to sides, pelvis on floor, thighs spread open, inner thighs visible, high detail",
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
    "rias": "red long hair, blue eyes, pale skin, large breasts, rias gremory, highschool dxd",
    "akeno": "long black hair, purple eyes, large breasts, akeno himejima, highschool dxd",
    "kafka": "purple wavy hair, cold expression, kafka, honkai star rail",
    "eula": "light blue hair, fair skin, eula, genshin impact",
    "fu_xuan": "pink hair, fu xuan, honkai star rail",
    "ayase": "black hair, school uniform, ayase seiko"
}

def check_rate_limit(user_id):
    """Проверка ограничения запросов (10 в 5 минут)"""
    now = datetime.now()
    user_activity[user_id] = [t for t in user_activity[user_id] if now - t < timedelta(minutes=5)]
    return len(user_activity[user_id]) < 10

def update_stats(user_id, success=True):
    """Обновление статистики пользователя"""
    user_stats[user_id]["total"] += 1
    if success:
        user_stats[user_id]["success"] += 1

def filter_tags(tags):
    """Фильтрация конфликтующих тегов"""
    filtered = list(tags)
    for group in EXCLUSIVE_GROUPS.values():
        found = [t for t in filtered if t in group]
        if len(found) > 1:
            for t in found[1:]:
                filtered.remove(t)
    return filtered

def build_prompt(tags):
    """Создание промта для генерации"""
    valid_tags = filter_tags(tags)
    base = "nsfw, masterpiece, ultra detailed, anime style, best quality"
    mandatory = ["fully nude", "no clothing covering chest or genitals"]
    tag_prompts = [TAG_PROMPTS.get(tag, tag) for tag in valid_tags if tag in TAG_PROMPTS]
    return ", ".join([base] + mandatory + tag_prompts)

def main_menu():
    """Главное меню"""
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🧩 Выбрать теги", callback_data="choose_tags"),
        types.InlineKeyboardButton("🎨 Генерировать", callback_data="generate"),
        types.InlineKeyboardButton("ℹ Помощь", callback_data="help")
    )
    return kb

def category_menu():
    """Меню категорий"""
    kb = types.InlineKeyboardMarkup(row_width=2)
    for key, name in CATEGORY_NAMES.items():
        kb.add(types.InlineKeyboardButton(name, callback_data=f"cat_{key}"))
    kb.add(types.InlineKeyboardButton("✅ Готово", callback_data="done_tags"))
    return kb

def tag_menu(category, selected_tags):
    """Меню тегов"""
    kb = types.InlineKeyboardMarkup(row_width=2)
    for tag_key, tag_name in TAGS[category].items():
        label = f"✅ {tag_name}" if tag_key in selected_tags else tag_name
        kb.add(types.InlineKeyboardButton(label, callback_data=f"tag_{category}_{tag_key}"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="back_to_cat"))
    return kb

@bot.message_handler(commands=["start"])
def start(msg):
    """Обработчик команды /start"""
    cid = msg.chat.id
    user_settings[cid] = {"tags": [], "last_cat": None}
    bot.send_message(cid, "Привет! Что делаем?", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data == "help")
def show_help(call):
    """Показ справки"""
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

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def category_handler(call):
    """Обработчик выбора категории"""
    cid = call.message.chat.id
    cat = call.data[4:]
    user_settings[cid]["last_cat"] = cat
    selected = user_settings[cid]["tags"]
    bot.edit_message_text(
        f"Категория: {CATEGORY_NAMES[cat]}",
        cid,
        call.message.message_id,
        reply_markup=tag_menu(cat, selected)
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("tag_"))
def tag_handler(call):
    """Обработчик выбора тега"""
    cid = call.message.chat.id
    _, cat, tag = call.data.split("_", 2)
    tags = user_settings[cid]["tags"]
    
    if tag in tags:
        tags.remove(tag)
    else:
        tags.append(tag)
    
    bot.edit_message_reply_markup(
        cid,
        call.message.message_id,
        reply_markup=tag_menu(cat, tags)
    )

@bot.callback_query_handler(func=lambda call: call.data == "generate")
def generate_handler(call):
    """Обработчик генерации изображения"""
    cid = call.message.chat.id
    
    if not check_rate_limit(cid):
        bot.answer_callback_query(call.id, "⚠️ Слишком много запросов. Подождите 5 минут.")
        return
    
    if cid not in user_settings or not user_settings[cid]["tags"]:
        bot.answer_callback_query(call.id, "Сначала выберите теги!")
        return
    
    user_activity[cid].append(datetime.now())
    raw_tags = user_settings[cid]["tags"]
    filtered_tags = filter_tags(raw_tags)
    
    # Уведомление о фильтрации тегов
    if len(filtered_tags) != len(raw_tags):
        removed = set(raw_tags) - set(filtered_tags)
        warning = "⚠ Некоторые теги были автоматически удалены из-за конфликтов:\n"
        warning += "\n".join(f"• {TAGS.get(tag.split('_')[0], {}).get(tag, tag)}" for tag in removed)
        bot.send_message(cid, warning)
    
    prompt = build_prompt(filtered_tags)
    bot.edit_message_text("🔄 Генерация начата...", cid, call.message.message_id)
    
    # Генерация изображения
    url = replicate_generate(prompt)
    
    if url:
        update_stats(cid, True)
        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("🔁 Начать заново", callback_data="start"),
            types.InlineKeyboardButton("🔧 Изменить теги", callback_data="edit_tags"),
            types.InlineKeyboardButton("➡ Продолжить с этими", callback_data="generate")
        )
        bot.send_photo(cid, url, caption="✅ Готово!", reply_markup=kb)
    else:
        update_stats(cid, False)
        bot.send_message(cid, "❌ Ошибка генерации. Попробуйте другие теги.")

def replicate_generate(prompt):
    """Генерация изображения через Replicate API"""
    url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {REPLICATE_TOKEN}",
        "Content-Type": "application/json"
    }
    json_data = {
        "version": REPLICATE_MODEL,
        "input": {
            "prompt": prompt,
            "width": 512,
            "height": 768,
            "num_outputs": 1,
            "guidance_scale": 7.5,
            "num_inference_steps": 50
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=json_data, timeout=10)
        response.raise_for_status()
        
        status_url = response.json()["urls"]["get"]
        start_time = time.time()
        
        while time.time() - start_time < 120:  # 2 минуты таймаут
            time.sleep(5)
            response = requests.get(status_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data["status"] == "succeeded":
                return data["output"][0] if isinstance(data["output"], list) else data["output"]
            elif data["status"] == "failed":
                logger.error(f"Generation failed: {data.get('error', 'Unknown error')}")
                return None
                
        logger.error("Generation timed out")
        return None
        
    except Exception as e:
        logger.error(f"API request failed: {str(e)}")
        return None

@app.route("/", methods=["POST"])
def webhook():
    """Webhook для Telegram"""
    json_str = request.stream.read().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "ok", 200

@app.route("/", methods=["GET"])
def home():
    """Проверка работоспособности"""
    return "бот работает", 200

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