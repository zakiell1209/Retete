import os
import logging
import requests
from flask import Flask, request
from telebot import TeleBot, types

# ✅ Переменные окружения
API_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")
WEBHOOK_URL = "https://retete.onrender.com"
REPLICATE_MODEL = "aitechtree/nsfw-novel-generation"

bot = TeleBot(API_TOKEN)
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# ✅ Категории и теги
CATEGORIES = {
    "персонажи": ["Риас Гремори", "Акено Химедзима", "Кафка", "Еола", "Фу Сюань", "Аясе Сейко"],
    "аниме/реализм/3D": ["аниме", "реализм", "3D"],
    "позы": ["горизонтальный шпагат", "вертикальный шпагат", "на боку с одной ногой вверх", "лёжа на спине с раздвинутыми ногами", "мост", "подвешенная на верёвках"],
    "отверстия": ["вагина", "анус", "рот"],
    "игрушки": ["дилдо", "анальный крюк", "дилдо из ануса выходит изо рта"],
    "одежда": ["голая", "в нижнем белье", "в чулках", "в ошейнике"],
    "кожа/этнос": ["белая кожа", "загар", "тёмная кожа"],
    "голова": ["ахегао", "лицо в боли", "лицо в экстазе", "золотая помада"],
    "фури": ["лисица", "кролик", "волчица"],
    "сцена": ["лицом к зрителю", "спиной к зрителю", "вид снизу", "вид сверху", "вид сбоку", "ближе", "дальше"]
}

user_tags = {}

# ✅ Сборка промпта
def build_prompt(tags):
    base = []
    for tag in tags:
        if tag == "дилдо из ануса выходит изо рта":
            base.append("dildo from anus through mouth, single piece, no x-ray, full object")
        elif tag == "горизонтальный шпагат":
            base.append("full body view, female in horizontal split, legs straight, on floor, realistic anatomy")
        elif tag == "вертикальный шпагат":
            base.append("full body view, female in vertical split, one leg up, perfect form")
        elif tag in CATEGORIES["персонажи"]:
            if tag == "Риас Гремори":
                base.append("Rias Gremory from High School DxD, red long hair, blue eyes, anime style")
            elif tag == "Акено Химедзима":
                base.append("Akeno Himejima from High School DxD, black long hair, purple eyes, anime style")
            elif tag == "Кафка":
                base.append("Kafka from Honkai Star Rail, violet eyes, wavy hair")
            elif tag == "Еола":
                base.append("Eula from Genshin Impact, ice blue hair, warrior outfit")
            elif tag == "Фу Сюань":
                base.append("Fu Xuan from Honkai Star Rail, pink twin tails, elegant outfit")
            elif tag == "Аясе Сейко":
                base.append("Seiko Ayase, straight long black hair, schoolgirl theme")
        else:
            base.append(tag)
    # Строгая фильтрация
    block = ["clothes", "hands covering", "censored", "blur", "shadows over genitals"]
    return ", ".join(base + ["nsfw, uncensored, full detail"] + [f"no {b}" for b in block])

# ✅ Генерация изображения
def generate_image(prompt):
    response = requests.post(
        "https://api.replicate.com/v1/predictions",
        headers={
            "Authorization": f"Token {REPLICATE_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "version": REPLICATE_MODEL,
            "input": {"prompt": prompt}
        }
    )
    output = response.json()
    return output.get("urls", {}).get("get", None)

# ✅ Клавиатура тегов
def build_keyboard(category, selected):
    keyboard = types.InlineKeyboardMarkup()
    for tag in CATEGORIES[category]:
        mark = "✅" if tag in selected else ""
        keyboard.add(types.InlineKeyboardButton(f"{mark} {tag}", callback_data=f"tag:{tag}"))
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back"))
    return keyboard

# ✅ Клавиатура категорий
def category_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    for category in CATEGORIES:
        keyboard.add(types.InlineKeyboardButton(category.title(), callback_data=f"cat:{category}"))
    keyboard.add(types.InlineKeyboardButton("✅ Сгенерировать", callback_data="generate"))
    return keyboard

# ✅ Обработка команд
@bot.message_handler(commands=["start"])
def handle_start(message):
    user_tags[message.chat.id] = set()
    bot.send_message(message.chat.id, "Выбери категорию тегов:", reply_markup=category_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    cid = call.message.chat.id
    data = call.data

    if data.startswith("cat:"):
        category = data.split(":", 1)[1]
        selected = user_tags.get(cid, set())
        bot.edit_message_text(
            f"Выберите теги из категории {category.title()}:",
            chat_id=cid,
            message_id=call.message.message_id,
            reply_markup=build_keyboard(category, selected)
        )

    elif data.startswith("tag:"):
        tag = data.split(":", 1)[1]
        tags = user_tags.setdefault(cid, set())
        if tag in tags:
            tags.remove(tag)
        else:
            tags.add(tag)
        category = next((k for k, v in CATEGORIES.items() if tag in v), "категория")
        bot.edit_message_reply_markup(
            cid,
            call.message.message_id,
            reply_markup=build_keyboard(category, tags)
        )

    elif data == "back":
        bot.edit_message_text("Выбери категорию тегов:", cid, call.message.message_id, reply_markup=category_keyboard())

    elif data == "generate":
        tags = user_tags.get(cid, set())
        prompt = build_prompt(tags)
        bot.edit_message_text("Генерирую изображение…", cid, call.message.message_id)
        image_url = generate_image(prompt)
        if image_url:
            bot.send_photo(cid, image_url, caption="Вот результат!", reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("🔁 Изменить теги", callback_data="back"),
                types.InlineKeyboardButton("🎲 Сгенерировать заново", callback_data="generate")
            ))
        else:
            bot.send_message(cid, "Ошибка генерации. Попробуйте снова.")

# ✅ Webhook
@app.route("/", methods=["POST"])
def webhook():
    bot.process_new_updates([types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "ok", 200

# ✅ Установка webhook
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

# ✅ Запуск Flask
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))