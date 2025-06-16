import os
import telebot
from telebot import types
import requests
import time
from flask import Flask, request

API_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # например https://yourdomain.com

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

PROMPT_PARTS = {
    "Типы": {
        "Футанари": "futanari, female with male characteristics, explicit",
        "Фембой": "femboy, slender male with feminine features",
    },
    "Атрибуты": {
        "Дилдо": "dildo, sex toy, realistic",
        "Пирсинг": "piercing, body jewelry",
        "Чулки": "stockings, lace, sheer",
        "Анальные шарики": "anal beads, sex toy",
    },
    "Позы": {
        "Шибари": "shibari, japanese rope bondage, intricate knots",
        "Ахегао": "ahegao, exaggerated facial expression",
        "Все виды поз": "various erotic poses, dynamic posture",
    },
    "Темы": {
        "Голая": "nude, bare skin, no clothes",
        "Изменения размера груди": "breast size manipulation, realistic anatomy",
        "Выбор типа загара": "tan lines, bikini tan lines, sun-kissed skin",
        "Анал": "anal sex, explicit, penetration",
    }
}

user_data = {}

def init_user(chat_id):
    if chat_id not in user_data:
        user_data[chat_id] = {
            "base_prompt": "",
            "components": []
        }

def build_prompt(chat_id):
    data = user_data.get(chat_id, {})
    base = data.get("base_prompt", "")
    components = data.get("components", [])
    parts = [base] if base else []
    parts.extend(components)
    return ", ".join(parts).strip()

# Хэндлеры бота (без изменений)

@bot.message_handler(commands=['start'])
def cmd_start(message):
    init_user(message.chat.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Выбрать компоненты", "Очистить выбор", "Удалить компонент", "Сгенерировать")
    bot.send_message(message.chat.id,
                     "Привет! Напиши базовое описание изображения.\n"
                     "Потом можешь выбрать дополнительные компоненты кнопкой 'Выбрать компоненты'.",
                     reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def set_base_prompt(message):
    init_user(message.chat.id)
    user_data[message.chat.id]["base_prompt"] = message.text
    bot.send_message(message.chat.id, f"Базовый промт установлен:\n{message.text}")

@bot.message_handler(func=lambda m: m.text == "Очистить выбор")
def clear_components(message):
    init_user(message.chat.id)
    user_data[message.chat.id]["components"] = []
    bot.send_message(message.chat.id, "Выбор компонентов очищен.")

@bot.message_handler(func=lambda m: m.text == "Выбрать компоненты")
def show_categories(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for category in PROMPT_PARTS.keys():
        markup.add(types.InlineKeyboardButton(text=category, callback_data=f"cat_{category}"))
    bot.send_message(message.chat.id, "Выберите категорию компонентов:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("cat_"))
def show_components(call):
    category = call.data[4:]
    markup = types.InlineKeyboardMarkup(row_width=2)
    for comp in PROMPT_PARTS[category]:
        markup.add(types.InlineKeyboardButton(text=comp, callback_data=f"comp_{comp}"))
    markup.add(types.InlineKeyboardButton(text="Назад", callback_data="back_to_cat"))
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text=f"Выберите компоненты категории '{category}':",
                          reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "back_to_cat")
def back_to_categories(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for category in PROMPT_PARTS.keys():
        markup.add(types.InlineKeyboardButton(text=category, callback_data=f"cat_{category}"))
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text="Выберите категорию компонентов:",
                          reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("comp_"))
def add_component(call):
    comp = call.data[5:]
    chat_id = call.message.chat.id
    init_user(chat_id)
    comp_prompt = None
    for cat in PROMPT_PARTS.values():
        if comp in cat:
            comp_prompt = cat[comp]
            break
    if not comp_prompt:
        bot.answer_callback_query(call.id, "Компонент не найден.")
        return
    if comp_prompt in user_data[chat_id]["components"]:
        bot.answer_callback_query(call.id, f"'{comp}' уже добавлен.")
    else:
        user_data[chat_id]["components"].append(comp_prompt)
        bot.answer_callback_query(call.id, f"Добавлено: {comp}")

@bot.message_handler(func=lambda m: m.text == "Удалить компонент")
def show_components_to_delete(message):
    chat_id = message.chat.id
    init_user(chat_id)
    comps = user_data[chat_id]["components"]
    if not comps:
        bot.send_message(chat_id, "Список компонентов пуст.")
        return
    markup = types.InlineKeyboardMarkup(row_width=2)
    reverse_map = {}
    for cat in PROMPT_PARTS.values():
        for k, v in cat.items():
            reverse_map[v] = k
    for comp_prompt in comps:
        name = reverse_map.get(comp_prompt, comp_prompt)
        markup.add(types.InlineKeyboardButton(text=name, callback_data=f"del_{name}"))
    bot.send_message(chat_id, "Выберите компонент для удаления:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("del_"))
def delete_component(call):
    comp_name = call.data[4:]
    chat_id = call.message.chat.id
    init_user(chat_id)
    full_prompt = None
    for cat in PROMPT_PARTS.values():
        if comp_name in cat:
            full_prompt = cat[comp_name]
            break
    if full_prompt and full_prompt in user_data[chat_id]["components"]:
        user_data[chat_id]["components"].remove(full_prompt)
        bot.answer_callback_query(call.id, f"Удалено: {comp_name}")
        comps = user_data[chat_id]["components"]
        if comps:
            markup = types.InlineKeyboardMarkup(row_width=2)
            reverse_map = {}
            for cat in PROMPT_PARTS.values():
                for k, v in cat.items():
                    reverse_map[v] = k
            for comp_prompt in comps:
                name = reverse_map.get(comp_prompt, comp_prompt)
                markup.add(types.InlineKeyboardButton(text=name, callback_data=f"del_{name}"))
            bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=markup)
        else:
            bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="Список компонентов пуст.")
    else:
        bot.answer_callback_query(call.id, "Компонент не найден в списке.")

@bot.message_handler(func=lambda m: m.text == "Сгенерировать")
def generate_image_handler(message):
    chat_id = message.chat.id
    init_user(chat_id)
    prompt = build_prompt(chat_id)
    if not prompt.strip():
        bot.send_message(chat_id, "Промт пустой. Напишите базовое описание или выберите компоненты.")
        return
    bot.send_message(chat_id, f"Генерирую изображение с промтом:\n{prompt}")
    status_url, error = generate_image(prompt)
    if error:
        bot.send_message(chat_id, f"Ошибка генерации: {error}")
        return
    for i in range(20):
        res = requests.get(status_url, headers={"Authorization": f"Token {REPLICATE_TOKEN}"})
        if res.status_code != 200:
            bot.send_message(chat_id, f"Ошибка получения статуса: {res.status_code} {res.text}")
            break
        status = res.json()
        if status.get("status") == "succeeded":
            image_url = status["output"][0]
            bot.send_photo(chat_id, image_url)
            return
        elif status.get("status") == "failed":
            bot.send_message(chat_id, "Генерация не удалась.")
            return
        else:
            bot.send_message(chat_id, f"Статус: {status.get('status')}, попытка {i+1}/20...")
        time.sleep(2)
    bot.send_message(chat_id, "❌ Не удалось сгенерировать изображение за отведённое время.")

def generate_image(prompt):
    url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {REPLICATE_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "version": "8625175575af3df665d665d2108a9e4e06cacf5c98295297502b52cc9c820b1c",
        "input": {"prompt": prompt}
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        prediction = response.json()
        return prediction["urls"]["get"], None
    else:
        return None, f"{response.status_code} {response.text}"

# Flask webhook route
@app.route(f"/{API_TOKEN}", methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return '', 200

@app.route("/", methods=['GET'])
def index():
    return "Bot is running"

if __name__ == "__main__":
    print("Bot started")

    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{API_TOKEN}")

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)