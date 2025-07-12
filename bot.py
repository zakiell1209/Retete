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

# Параметры генерации по умолчанию
DEFAULT_GENERATION_PARAMS = {
    "width": 512,
    "height": 768,
    "num_outputs": 1,
    "guidance_scale": 7.5,
    "num_inference_steps": 50,
    "negative_prompt": ("bad anatomy, extra limbs, poorly drawn hands, fused fingers, "
                       "extra digits, missing arms, missing legs, extra arms, extra legs, "
                       "mutated hands, fused fingers, long neck")
}

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
    "vagina": "spread pussy, hands not covering",
    "anal": "spread anus, hands not covering",
    "both": "spread pussy and anus, hands not covering",
    "dildo": "dildo inserted, hands not covering",
    "huge_dildo": "huge dildo, hands not covering",
    "horse_dildo": "horse dildo, hands not covering",
    "anal_beads": "anal beads inserted, hands not covering",
    "anal_plug": "anal plug, hands not covering",
    "anal_expander": "anal expander stretching anus, hands not covering",
    "gag": "ball gag, hands not covering",
    "piercing": "nipple and genital piercings, hands not covering",
    "long_dildo_path": (
        "dildo inserted into anus, pushing visibly through intestines with clear belly bulge, "
        "exiting from mouth, seamless and continuous dildo, consistent texture, realistic rubber"
    ),
    "doggy": "doggy style, hands on floor or holding ankles",
    "standing": "standing pose, arms at sides or holding something",
    "splits": "doing a split, arms balanced or raised",
    "hor_split": (
        "horizontal split, legs stretched fully to sides, pelvis on floor, thighs spread open, "
        "inner thighs visible, high detail, hands not covering"
    ),
    "ver_split": "vertical split, arms balanced",
    "side_up_leg": "on side with leg raised, hands not covering",
    "front_facing": "facing viewer, hands not covering",
    "back_facing": "back to viewer, hands not covering",
    "lying_knees_up": "legs up, knees bent, hands not covering",
    "bridge": "arched back bridge pose, hands supporting weight",
    "suspended": "suspended by ropes, hands not covering",
    "stockings": "wearing stockings only, hands not covering",
    "mask": "mask on face, hands not covering",
    "heels": "high heels with red soles, hands not covering",
    "shibari": "shibari ropes, hands not covering",
    "big_breasts": "big breasts, hands not covering",
    "small_breasts": "small breasts, hands not covering",
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
    "femboy": "male, feminine body, flat chest, no breasts, feminine facial features",
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
    "gold_lipstick": "gold lipstick"
}

EXCLUSIVE_GROUPS = {
    "breast_size": ["big_breasts", "small_breasts"],
    "body_type": ["body_fat", "body_thin", "body_normal", "body_fit", "body_muscular"],
    "skin_color": ["skin_white", "skin_black"],
    "age": ["age_loli", "age_milf", "age_21"]
}

def filter_tags(tags):
    filtered = list(tags)
    for group in EXCLUSIVE_GROUPS.values():
        found = [t for t in filtered if t in group]
        if len(found) > 1:
            for t in found[1:]:
                filtered.remove(t)
    return filtered

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

def build_prompt(tags):
    valid_tags = filter_tags(tags)
    base = "nsfw, masterpiece, ultra detailed, anime style, best quality"
    mandatory = ["fully nude", "no clothing covering chest or genitals", "hands not covering"]
    tag_prompts = [TAG_PROMPTS.get(tag, tag) for tag in valid_tags]
    return ", ".join([base] + mandatory + tag_prompts)

def replicate_generate(prompt):
    url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {REPLICATE_TOKEN}",
        "Content-Type": "application/json"
    }
    
    input_data = {"prompt": prompt}
    input_data.update(DEFAULT_GENERATION_PARAMS)
    
    try:
        r = requests.post(url, headers=headers, json={"version": REPLICATE_MODEL, "input": input_data}, timeout=10)
        r.raise_for_status()
        status_url = r.json()["urls"]["get"]
        start_time = time.time()
        
        while time.time() - start_time < 120:
            time.sleep(5)
            r = requests.get(status_url, headers=headers, timeout=10)
            r.raise_for_status()
            data = r.json()
            
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

@bot.message_handler(commands=["start"])
def start(msg):
    cid = msg.chat.id
    user_settings[cid] = {"tags": [], "last_cat": None}
    bot.send_message(cid, "Привет! Что делаем?", reply_markup=main_menu())

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

@bot.callback_query_handler(func=lambda call: call.data == "generate")
def generate_handler(call):
    cid = call.message.chat.id
    if cid not in user_settings or not user_settings[cid]["tags"]:
        bot.answer_callback_query(call.id, "Сначала выберите теги!")
        return
    
    raw_tags = user_settings[cid]["tags"]
    filtered_tags = filter_tags(raw_tags)
    
    if len(filtered_tags) != len(raw_tags):
        removed = set(raw_tags) - set(filtered_tags)
        warning = (
            "⚠ Некоторые теги были автоматически удалены из-за конфликтов:\n" +
            "\n".join(f"• {TAGS.get(tag.split('_')[0], {}).get(tag, tag)}" 
            for tag in removed)
        bot.send_message(cid, warning)
    
    prompt = build_prompt(filtered_tags)
    user_settings[cid]["last_prompt"] = tuple(filtered_tags)  # Сохраняем как кортеж
    
    bot.edit_message_text("🔄 Генерация начата...", cid, call.message.message_id)
    
    url = replicate_generate(prompt)
    if url:
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("🔁 Начать заново", callback_data="start"),
            types.InlineKeyboardButton("🔧 Изменить теги", callback_data="edit_tags"),
            types.InlineKeyboardButton("➡ Продолжить с этими", callback_data="generate")
        )
        bot.send_photo(cid, url, caption="✅ Готово!", reply_markup=kb)
    else:
        bot.send_message(cid, "❌ Ошибка генерации. Попробуйте другие теги.")

@bot.callback_query_handler(func=lambda call: call.data in ["start", "edit_tags", "generate"])
def post_generation_handler(call):
    cid = call.message.chat.id
    try:
        if call.data == "start":
            user_settings[cid] = {"tags": [], "last_cat": None}
            bot.edit_message_text(
                "Настройки сброшены. Что делаем?",
                chat_id=cid,
                message_id=call.message.message_id,
                reply_markup=main_menu()
            )
        elif call.data == "edit_tags":
            if "last_prompt" in user_settings.get(cid, {}):
                user_settings[cid]["tags"] = list(user_settings[cid]["last_prompt"])
                bot.edit_message_text(
                    "Изменяем теги:",
                    chat_id=cid,
                    message_id=call.message.message_id,
                    reply_markup=category_menu()
                )
            else:
                bot.answer_callback_query(call.id, "Нет сохранённых тегов")
        elif call.data == "generate":
            if cid in user_settings and user_settings[cid].get("last_prompt"):
                generate_handler(call)
            else:
                bot.answer_callback_query(call.id, "Сначала выберите теги")
    except Exception as e:
        logger.error(f"Error in post_generation_handler: {str(e)}")
        bot.answer_callback_query(call.id, "⚠ Ошибка обработки запроса")

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        if request.headers.get('content-type') == 'application/json':
            json_data = request.get_json()
            update = telebot.types.Update.de_json(json_data)
            bot.process_new_updates([update])
            return '', 200
        return 'Invalid content type', 400
    return 'Bot is running', 200

if __name__ == '__main__':
    logger.info("Starting bot...")
    try:
        if WEBHOOK_URL:
            bot.remove_webhook()
            time.sleep(1)
            bot.set_webhook(url=WEBHOOK_URL)
            app.run(host='0.0.0.0', port=PORT)
        else:
            bot.remove_webhook()
            bot.infinity_polling()
    except Exception as e:
        logger.error(f"Bot crashed: {str(e)}")
        raise