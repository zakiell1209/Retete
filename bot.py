import os
import replicate
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ⛓️ Токены и параметры
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)
replicate_client = replicate.Client(api_token=REPLICATE_API_TOKEN)

# 🏷️ Теги и настройки
TAGS_PER_PAGE = 8

TAGS = {
    "тело": {
        "Лоли": "loli",
        "Милфа": "milf",
        "21 год": "age 21",
        "Худая": "skinny",
        "Накачаная": "muscular",
        "Пышная": "curvy",
        "Норм. тело": "normal body"
    },
    "игрушки": {
        "Анальные бусы": "anal beads",
        "Фаллоимитатор": "dildo",
        "Пирсинг": "piercing"
    },
    "этнос": {
        "Фембой": "femboy",
        "Азиатка": "asian girl",
        "Европейка": "european girl",
        "Футанари": "futanari"
    },
    "фури": {
        "Фури-королева": "furry queen",
        "Фури-кошка": "furry cat",
        "Фури-собака": "furry dog",
        "Фури-дракон": "furry dragon",
        "Сильвеон": "furry_silveon"
    },
    "одежда": {
        "Загар от бикини": "bikini_tan_lines",
        "Костюм коровы": "cow_costume"
    },
    "позы": {
        "Горизонт. шпагат": "horizontal split",
        "Вертик. шпагат": "vertical split",
        "На боку нога вверх": "side pose one leg up",
        "Лицом к нам": "facing viewer",
        "Спиной к нам": "back to viewer",
        "Лёжа раздвинутые": "lying with spread legs",
        "Мостик": "bridging pose",
        "Подвешена": "suspended ropes"
    }
}

user_state = {}

# 🔘 Кнопки
def get_tags_keyboard(category, page, selected_tags):
    tags = list(TAGS[category].items())
    start = page * TAGS_PER_PAGE
    end = start + TAGS_PER_PAGE
    page_tags = tags[start:end]
    markup = InlineKeyboardMarkup(row_width=2)
    for name, prompt in page_tags:
        checked = "✅ " if prompt in selected_tags else ""
        markup.add(InlineKeyboardButton(f"{checked}{name}", callback_data=f"tag|{category}|{prompt}"))
    nav_buttons = []
    if start > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"nav|{category}|{page-1}"))
    if end < len(tags):
        nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"nav|{category}|{page+1}"))
    markup.row(*nav_buttons)
    markup.row(InlineKeyboardButton("Готово", callback_data="tags_done"))
    return markup

def get_categories_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    for cat in TAGS.keys():
        markup.add(InlineKeyboardButton(cat, callback_data=f"category|{cat}"))
    return markup

def get_generate_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Начать заново", callback_data="start_over"))
    markup.add(InlineKeyboardButton("Редактировать теги", callback_data="edit_tags"))
    return markup

# 🧠 Обработчики
@bot.message_handler(commands=["start"])
def start(message):
    user_state[message.chat.id] = {"selected": [], "last_category": None, "page": 0}
    bot.send_message(message.chat.id, "Выбери категорию тегов:", reply_markup=get_categories_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id
    data = call.data

    if chat_id not in user_state:
        user_state[chat_id] = {"selected": [], "last_category": None, "page": 0}

    state = user_state[chat_id]

    if data.startswith("category|"):
        _, cat = data.split("|")
        state["last_category"] = cat
        state["page"] = 0
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
                              text=f"Выбери теги ({cat}):", reply_markup=get_tags_keyboard(cat, 0, state["selected"]))

    elif data.startswith("tag|"):
        _, cat, prompt = data.split("|")
        if prompt in state["selected"]:
            state["selected"].remove(prompt)
        else:
            state["selected"].append(prompt)
        bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id,
                                      reply_markup=get_tags_keyboard(cat, state["page"], state["selected"]))

    elif data.startswith("nav|"):
        _, cat, page = data.split("|")
        page = int(page)
        state["page"] = page
        bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id,
                                      reply_markup=get_tags_keyboard(cat, page, state["selected"]))

    elif data == "tags_done":
        if not state["selected"]:
            bot.answer_callback_query(call.id, "Вы не выбрали ни одного тега!")
        else:
            bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
                                  text="Генерирую изображение...")
            generate_and_send(chat_id, state["selected"])

    elif data == "start_over":
        start(call.message)

    elif data == "edit_tags":
        cat = state.get("last_category", list(TAGS.keys())[0])
        page = 0
        state["page"] = page
        bot.send_message(chat_id, f"Редактируй теги ({cat}):", reply_markup=get_tags_keyboard(cat, page, state["selected"]))

def generate_and_send(chat_id, tags):
    prompt = ", ".join(tags)
    try:
        output_url = replicate_client.run(
            "aitechtree/nsfw-novel-generation:3f313108c30f05798c1ae6f44d8ecf939591c98c58315f358db5b9e0c184d168",
            input={"prompt": prompt}
        )
        bot.send_photo(chat_id, output_url, reply_markup=get_generate_keyboard())
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка генерации: {e}")

# 🌍 Вебхук
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "ok", 200

@app.route("/", methods=["GET"])
def index():
    return "Бот работает", 200

if __name__ == "__main__":
    import sys
    import logging
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    bot.remove_webhook()
    bot.set_webhook(url=f"https://your_render_url.onrender.com/{TELEGRAM_TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))