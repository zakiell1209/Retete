import os
import json
import logging
import requests
from flask import Flask, request
from telebot import TeleBot, types

BOT_TOKEN = os.getenv("BOT_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_TOKEN")
REPLICATE_MODEL = "aitechtree/nsfw-novel-generation"

bot = TeleBot(BOT_TOKEN)
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Хранилище состояний
user_states = {}
user_tags = {}
user_model = {}

# Категории и теги
CATEGORIES = {
    "персонажи": ["Риас Гремори", "Акено Химедзима", "Кафка", "Еола", "Фу Сюань", "Аясе Сейко"],
    "поза": ["горизонтальный шпагат", "вертикальный шпагат", "на боку с одной ногой вверх", "лёжа на спине с раздвинутыми ногами, согнутыми в коленях", "мост", "подвешенная на верёвках"],
    "отверстия": ["анал", "вагина", "орально"],
    "игрушки": ["дилдо", "дилдо из ануса выходит изо рта"],
    "голова": ["ахегао", "лицо в боли", "лицо в экстазе", "золотая помада"],
    "фури": ["лисица", "кролик", "волчица"],
    "сцена": ["лицом к зрителю", "спиной к зрителю", "вид сверху", "вид снизу", "вид сбоку", "ближе", "дальше"],
}

PROMPT_MAPPING = {
    "горизонтальный шпагат": "girl doing a horizontal split on the floor, legs fully extended to both sides, viewed from front",
    "вертикальный шпагат": "girl doing a standing vertical split, one leg raised straight up, body stretched, viewed clearly",
    "дилдо из ануса выходит изо рта": "a single, realistic dildo entering anus and emerging from mouth, anatomically accurate, same color and texture",
    "вид сверху": "top-down view, camera above the girl",
    "вид снизу": "bottom-up view, as if under the floor, looking up at girl",
    "вид сбоку": "side view, girl facing left or right",
    "ближе": "close-up view of the girl",
    "дальше": "distant full-body view of the girl",
}

NEGATIVE_PROMPT = "clothes, covering, censorship, hands covering, mosaic, blur, watermark, text, extra limbs, poorly drawn"

def build_prompt(tags):
    description = []
    for tag in tags:
        if tag in PROMPT_MAPPING:
            description.append(PROMPT_MAPPING[tag])
        else:
            description.append(tag)
    return ", ".join(description)

def generate_image(prompt):
    headers = {"Authorization": f"Token {REPLICATE_TOKEN}"}
    payload = {
        "version": "4d6740c8a246405d84341b7cbdf8d4c80926700124ba801bfcd5273768bb15a4",
        "input": {
            "prompt": prompt,
            "negative_prompt": NEGATIVE_PROMPT,
            "width": 512,
            "height": 768,
            "num_outputs": 1,
        }
    }
    response = requests.post("https://api.replicate.com/v1/predictions", headers=headers, json=payload)
    prediction = response.json()
    get_url = prediction["urls"]["get"]
    while True:
        result = requests.get(get_url, headers=headers).json()
        if result["status"] == "succeeded":
            return result["output"][0]
        elif result["status"] == "failed":
            return None

@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    user_states[user_id] = "selecting_category"
    user_tags[user_id] = []
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for category in CATEGORIES:
        markup.add(category)
    bot.send_message(message.chat.id, "Выбери категорию тегов:", reply_markup=markup)

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == "selecting_category")
def select_category(message):
    category = message.text
    user_id = message.from_user.id
    if category in CATEGORIES:
        markup = types.InlineKeyboardMarkup(row_width=2)
        for tag in CATEGORIES[category]:
            text = f"✅ {tag}" if tag in user_tags[user_id] else tag
            markup.add(types.InlineKeyboardButton(text, callback_data=f"tag|{tag}"))
        markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="back"))
        markup.add(types.InlineKeyboardButton("✅ Готово", callback_data="done"))
        bot.send_message(message.chat.id, f"Выбери теги из категории: {category}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("tag|"))
def toggle_tag(call):
    tag = call.data.split("|")[1]
    user_id = call.from_user.id
    if tag in user_tags[user_id]:
        user_tags[user_id].remove(tag)
    else:
        user_tags[user_id].append(tag)
    bot.answer_callback_query(call.id)
    select_category(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "back")
def go_back(call):
    user_id = call.from_user.id
    start(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "done")
def done_tag_selection(call):
    user_id = call.from_user.id
    prompt = build_prompt(user_tags[user_id])
    bot.send_message(call.message.chat.id, "Генерирую изображение...")
    image_url = generate_image(prompt)
    if image_url:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔁 Продолжить с этими тегами", callback_data="done"))
        markup.add(types.InlineKeyboardButton("🎯 Изменить теги", callback_data="back"))
        markup.add(types.InlineKeyboardButton("🔄 Начать заново", callback_data="restart"))
        bot.send_photo(call.message.chat.id, image_url, reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, "Ошибка при генерации. Попробуй снова.")

@bot.callback_query_handler(func=lambda call: call.data == "restart")
def restart(call):
    user_id = call.from_user.id
    user_tags[user_id] = []
    start(call.message)

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    bot.process_new_updates([types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "ok", 200

@app.route("/", methods=["GET"])
def index():
    return "Bot is running", 200

if __name__ == "__main__":
    import time
    time.sleep(1)
    bot.remove_webhook()
    bot.set_webhook(url=os.getenv("WEBHOOK_URL") + f"/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
