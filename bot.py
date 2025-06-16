import os
import json
import telebot
import requests
from flask import Flask, request

BOT_TOKEN = os.getenv("BOT_TOKEN")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
REPLICATE_MODEL = "aitechtree/nsfw-novel-generation"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

TAGS = {
    "позы": ["Шпагат", "Сбоку", "Мост", "На спине", "Сзади", "Верёвки"],
    "отверстия": ["Вагина", "Анус", "Рот"],
    "игрушки": ["Дилдо", "Анальные бусы", "Пробка"],
    "одежда": ["Голая", "Купальник", "Костюм коровы", "Без трусов"],
    "тело": ["Большая грудь", "Лоли", "Милфа", "Смуглая", "Пышная"],
    "этнос": ["Фембой", "Азиатка", "Футанари", "Европейка"],
    "фури": ["Сильвеон", "Кошка", "Собака", "Дракон"]
}

PROMPTS = {
    "Шпагат": "full split pose", "Сбоку": "side view", "Мост": "bridge pose", "На спине": "lying on back, spread legs",
    "Сзади": "from behind", "Верёвки": "shibari rope suspension", "Вагина": "vaginal penetration", "Анус": "anal penetration",
    "Рот": "oral sex", "Дилдо": "dildo", "Анальные бусы": "anal beads", "Пробка": "buttplug", "Голая": "naked",
    "Купальник": "bikini", "Костюм коровы": "cow pattern stockings, horns, tail, no panties",
    "Без трусов": "no panties", "Большая грудь": "large breasts", "Лоли": "petite, young", "Милфа": "mature woman",
    "Смуглая": "dark skin, bikini tan lines", "Пышная": "curvy body", "Фембой": "femboy", "Азиатка": "asian girl",
    "Футанари": "futanari", "Европейка": "european girl", "Сильвеон": "female anthro sylveon", "Кошка": "cat girl",
    "Собака": "dog girl", "Дракон": "dragon girl"
}

user_tags = {}
PAGE_SIZE = 6
user_pages = {}

# Генерация кнопок
def make_keyboard(uid, category):
    page = user_pages.get(uid, {}).get(category, 0)
    tags = TAGS[category]
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    buttons = []

    for tag in tags[start:end]:
        check = "✅" if tag in user_tags.get(uid, []) else ""
        buttons.append(telebot.types.InlineKeyboardButton(f"{check}{tag}", callback_data=f"tag|{tag}|{category}"))

    nav = []
    if start > 0:
        nav.append(telebot.types.InlineKeyboardButton("⬅️", callback_data=f"nav|prev|{category}"))
    if end < len(tags):
        nav.append(telebot.types.InlineKeyboardButton("➡️", callback_data=f"nav|next|{category}"))

    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    for i in range(0, len(buttons), 2):
        markup.add(*buttons[i:i+2])
    if nav:
        markup.add(*nav)

    markup.add(
        telebot.types.InlineKeyboardButton("Готово", callback_data="done"),
        telebot.types.InlineKeyboardButton("Назад", callback_data="back")
    )
    return markup

@bot.message_handler(commands=["start"])
def start(m):
    user_tags[m.chat.id] = []
    bot.send_message(m.chat.id, "Выбери категорию:", reply_markup=category_keyboard())

def category_keyboard():
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    for cat in TAGS:
        markup.add(telebot.types.InlineKeyboardButton(cat.capitalize(), callback_data=f"cat|{cat}"))
    return markup

@bot.callback_query_handler(func=lambda c: c.data.startswith("cat|"))
def category_select(call):
    _, category = call.data.split("|")
    uid = call.message.chat.id
    if uid not in user_pages:
        user_pages[uid] = {}
    user_pages[uid][category] = 0
    bot.edit_message_text(f"Выбери теги ({category}):", chat_id=uid, message_id=call.message.message_id,
                          reply_markup=make_keyboard(uid, category))

@bot.callback_query_handler(func=lambda c: c.data.startswith("tag|"))
def tag_toggle(call):
    _, tag, category = call.data.split("|")
    uid = call.message.chat.id
    tags = user_tags.setdefault(uid, [])
    if tag in tags:
        tags.remove(tag)
    else:
        tags.append(tag)
    bot.edit_message_reply_markup(uid, call.message.message_id, reply_markup=make_keyboard(uid, category))

@bot.callback_query_handler(func=lambda c: c.data.startswith("nav|"))
def navigate(call):
    _, direction, category = call.data.split("|")
    uid = call.message.chat.id
    current = user_pages.get(uid, {}).get(category, 0)
    if direction == "next":
        user_pages[uid][category] = current + 1
    elif direction == "prev":
        user_pages[uid][category] = max(0, current - 1)
    bot.edit_message_reply_markup(uid, call.message.message_id, reply_markup=make_keyboard(uid, category))

@bot.callback_query_handler(func=lambda c: c.data == "done")
def generate(call):
    uid = call.message.chat.id
    prompts = [PROMPTS[t] for t in user_tags.get(uid, []) if t in PROMPTS]
    full_prompt = ", ".join(prompts)

    bot.edit_message_text("Генерация изображения...", uid, call.message.message_id)
    image_url = generate_image(full_prompt)
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("🎨 Ещё", callback_data="back"),
        telebot.types.InlineKeyboardButton("✏️ Редактировать", callback_data="edit")
    )
    bot.send_photo(uid, image_url, caption="Вот твоё изображение", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "edit")
def edit_tags(call):
    bot.send_message(call.message.chat.id, "Выбери категорию для редактирования:", reply_markup=category_keyboard())

@bot.callback_query_handler(func=lambda c: c.data == "back")
def back(call):
    bot.edit_message_text("Выбери категорию:", call.message.chat.id, call.message.message_id,
                          reply_markup=category_keyboard())

def generate_image(prompt):
    response = requests.post(
        "https://api.replicate.com/v1/predictions",
        headers={
            "Authorization": f"Token {REPLICATE_API_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "version": "f924bcb8971a45f575a8ba5c13d6f74d53f38b00a09259fa2599c5f4b2e6d25d",
            "input": {"prompt": prompt}
        }
    )
    prediction = response.json()
    return prediction["output"][-1] if "output" in prediction else "https://placehold.co/512x512"

# Flask Webhook
@app.route("/", methods=["GET", "POST"])
def webhook():
    if request.method == "POST":
        bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
        return "", 200
    return "Bot is running!"

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=os.getenv("RENDER_EXTERNAL_URL"))
    app.run(host="0.0.0.0", port=10000)