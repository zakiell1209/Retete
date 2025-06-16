import os
import telebot
from flask import Flask, request
import replicate
from dotenv import load_dotenv

load_dotenv()

REPLICATE_TOKEN = os.getenv("REPLICATE_TOKEN")
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Модель по умолчанию
selected_model = {}

# Пользовательские теги
user_tags = {}

# Модель и версия
MODELS = {
    "anime": "aitechtree/nsfw-novel-generation:db21c9875ff0b...",
    "realism": "aitechtree/nsfw-novel-generation-realistic:f3a...",
    "3d": "aitechtree/nsfw-novel-generation-3d:27bfe7ef8c94..."
}

# Кнопки
model_buttons = ["anime", "realism", "3d"]
pose_tags = ["doggy", "standing", "splits", "squat", "lying"]
hole_tags = ["vagina", "anal", "both"]
toy_tags = ["dildo", "anal_beads", "anal_plug", "gag"]
clothes_tags = ["stockings", "bikini", "mask", "heels", "shibari", "cow_costume", "bikini_tan_lines"]
body_tags = ["big_breasts", "small_breasts", "black_skin", "white_skin", "muscular", "slim", "milf", "teen"]
ethnic_tags = ["femboy", "asian", "european", "futa"]
furry_tags = ["furry_queen", "furry_cat", "furry_dog", "furry_dragon", "furry_sylveon"]

tag_groups = {
    "Позы": pose_tags,
    "Отверстия": hole_tags,
    "Игрушки": toy_tags,
    "Одежда": clothes_tags,
    "Тело": body_tags,
    "Этнос": ethnic_tags,
    "Фури": furry_tags
}

from telebot import types

def build_prompt(base, tags):
    additions = []
    map_tag = {
        "vagina": "vaginal penetration", "anal": "anal penetration", "both": "double penetration",
        "dildo": "dildo", "anal_beads": "anal beads", "anal_plug": "anal plug", "gag": "gag",
        "doggy": "doggy style", "standing": "standing pose", "splits": "splits", "squat": "squatting", "lying": "laying",
        "stockings": "stockings", "bikini": "bikini", "mask": "mask", "heels": "high heels", "shibari": "shibari",
        "cow_costume": "cow costume", "bikini_tan_lines": "bikini tan lines",
        "big_breasts": "large breasts", "small_breasts": "small breasts", "black_skin": "dark skin",
        "white_skin": "pale skin", "muscular": "muscular", "slim": "slim", "milf": "mature woman", "teen": "teen girl",
        "femboy": "femboy", "asian": "asian girl", "european": "european girl", "futa": "futanari",
        "furry_queen": "anthro female with crown", "furry_cat": "cat furry", "furry_dog": "dog furry",
        "furry_dragon": "dragon furry", "furry_sylveon": "sylveon furry"
    }
    for tag in tags:
        if tag in map_tag:
            additions.append(map_tag[tag])
        else:
            additions.append(tag)
    full_prompt = base
    if additions:
        full_prompt += ", " + ", ".join(additions)
    return full_prompt

@bot.message_handler(commands=["start"])
def start(msg):
    cid = msg.chat.id
    user_tags[cid] = []
    selected_model[cid] = "anime"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(*model_buttons)
    for group in tag_groups:
        markup.add(group)
    markup.add("Готово")
    bot.send_message(cid, "Выберите модель и желаемые параметры:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in model_buttons)
def set_model(msg):
    selected_model[msg.chat.id] = msg.text
    bot.send_message(msg.chat.id, f"Модель установлена: {msg.text}")

@bot.message_handler(func=lambda m: m.text in tag_groups)
def choose_tags(msg):
    cid = msg.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = []
    for tag in tag_groups[msg.text]:
        label = f"✅ {tag}" if tag in user_tags.get(cid, []) else tag
        buttons.append(label)
    markup.add(*buttons)
    markup.add("Назад")
    bot.send_message(cid, f"Выберите теги: {msg.text}", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text.startswith("✅ ") or m.text in sum(tag_groups.values(), []))
def toggle_tag(msg):
    cid = msg.chat.id
    tag = msg.text.replace("✅ ", "")
    if cid not in user_tags:
        user_tags[cid] = []
    if tag in user_tags[cid]:
        user_tags[cid].remove(tag)
    else:
        user_tags[cid].append(tag)
    choose_tags(types.SimpleNamespace(chat=msg.chat, text=find_group(tag)))

def find_group(tag):
    for group, tags in tag_groups.items():
        if tag in tags:
            return group
    return ""

@bot.message_handler(func=lambda m: m.text == "Назад")
def back(msg):
    start(msg)

@bot.message_handler(func=lambda m: m.text == "Готово")
def generate_image(msg):
    cid = msg.chat.id
    bot.send_message(cid, "Отправьте описание сцены (пример: '1girl, spread legs, looking back')")
    bot.register_next_step_handler(msg, send_to_replicate)

def send_to_replicate(msg):
    cid = msg.chat.id
    model = selected_model.get(cid, "anime")
    tags = user_tags.get(cid, [])
    prompt = build_prompt(msg.text, tags)
    bot.send_message(cid, "Генерация изображения...")
    try:
        output = replicate.run(
            MODELS[model],
            input={"prompt": prompt, "width": 512, "height": 768}
        )
        bot.send_photo(cid, output)
    except Exception as e:
        bot.send_message(cid, f"Ошибка генерации: {e}")

# Flask webhook
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "ok", 200

@app.route("/", methods=["GET"])
def index():
    return "бот работает"

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))