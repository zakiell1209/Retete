import os
import time
import requests
from flask import Flask, request
import telebot
from telebot import types

API_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")
REPLICATE_MODEL = "057e2276ac5dcd8d1575dc37b131f903df9c10c41aed53d47cd7d4f068c19fa5"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 5000))

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
user_settings = {}

CATEGORY_NAMES = {
    "poses": "Позы", "clothes": "Одежда", "body": "Тело", "ethnos": "Этнос",
    "holes": "Отверстия", "toys": "Игрушки", "furry": "Фури", "characters": "Персонажи",
    "head": "Голова", "view": "Обзор"
}

TAGS = {
    "poses": {
        "doggy": "Наездница", "standing": "Стоя", "splits": "Шпагат",
        "squat": "Присед", "lying": "Лежа", "hor_split": "Горизонтальный шпагат",
        "ver_split": "Вертикальный шпагат", "side_up_leg": "Нога вверх", "bridge": "Мост",
        "suspended": "Подвешена", "front_facing": "Лицом к зрителю", "back_facing": "Спиной",
        "lying_knees_up": "Лежа, колени вверх"
    },
    "clothes": {
        "stockings": "Чулки", "heels": "Каблуки", "mask": "Маска",
        "shibari": "Шибари", "bikini_tan_lines": "Загар от бикини"
    },
    "body": {
        "big_breasts": "Большая грудь", "small_breasts": "Маленькая грудь",
        "body_thin": "Худое", "body_fit": "Подтянутое", "body_fat": "Пышное",
        "body_normal": "Нормальное", "skin_white": "Белая кожа", "skin_black": "Чёрная кожа",
        "body_muscular": "Мускулистое", "age_loli": "Лоли", "age_milf": "Милфа", "age_21": "Возраст 21",
        "cum": "Вся в сперме", "belly_bloat": "Вздутие живота", "succubus_tattoo": "Тату на животе"
    },
    "ethnos": {
        "ethnicity_asian": "Азиатка", "ethnicity_european": "Европейка",
        "futanari": "Футанари", "femboy": "Фембой"
    },
    "holes": {
        "vagina": "Вагина", "anal": "Анус", "both": "Вагина и анус"
    },
    "toys": {
        "dildo": "Дилдо", "huge_dildo": "Большое дилдо", "horse_dildo": "Лошадиное дилдо",
        "anal_beads": "Анальные бусы", "anal_plug": "Анальная пробка", "anal_expander": "Анальный расширитель",
        "gag": "Кляп", "piercing": "Пирсинг", "long_dildo_path": "Дилдо через рот"
    },
    "furry": {
        "furry_cow": "Фури корова", "furry_cat": "Фури кошка", "furry_dog": "Фури собака",
        "furry_dragon": "Фури дракон", "furry_fox": "Фури лисица", "furry_bunny": "Фури кролик",
        "furry_wolf": "Фури волчица", "furry_sylveon": "Фури сильвеон"
    },
    "characters": {
        "rias": "Риас Гремори", "akeno": "Акено", "kafka": "Кафка",
        "eula": "Еола", "fu_xuan": "Фу Сюань", "ayase": "Аясе Сейко", "2b": "2B", "yor": "Йор Форжер"
    },
    "head": {
        "ahegao": "Ахегао", "ecstasy_face": "Экстаз", "pain_face": "Боль", "gold_lipstick": "Золотая помада"
    },
    "view": {
        "view_top": "Сверху", "view_bottom": "Снизу", "view_side": "Сбоку", "view_close": "Близко", "view_full": "Полный рост"
    }
}

# Промпты и NEGATIVE будут продолжены ниже, из-за лимита символов.

def replicate_generate(prompt, negative_prompt, count):
    url = "https://api.replicate.com/v1/predictions"
    headers = {"Authorization": f"Token {REPLICATE_TOKEN}", "Content-Type": "application/json"}
    json_data = {
        "version": REPLICATE_MODEL,
        "input": {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "num_outputs": count
        }
    }
    r = requests.post(url, headers=headers, json=json_data)
    if r.status_code != 201:
        return []
    status_url = r.json()["urls"]["get"]
    for _ in range(60):
        time.sleep(2)
        r = requests.get(status_url, headers=headers)
        if r.status_code != 200:
            return []
        data = r.json()
        if data["status"] == "succeeded":
            return data["output"] if isinstance(data["output"], list) else [data["output"]]
        elif data["status"] == "failed":
            return []
    return []

@app.route("/", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "ok", 200

@app.route("/", methods=["GET"])
def home():
    return "бот работает", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=PORT)
