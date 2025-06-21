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
    "holes": "Отверстия", "toys": "Игрушки", "poses": "Позы", "clothes": "Одежда",
    "body": "Тело", "ethnos": "Этнос", "furry": "Фури", "characters": "Персонажи",
    "head": "Голова", "view": "Обзор"
}

TAGS = {
    "holes": {"vagina": "Вагина", "anal": "Анус", "both": "Вагина и анус"},
    "toys": {
        "dildo": "Дилдо", "huge_dildo": "Большое дилдо", "horse_dildo": "Лошадиное дилдо",
        "anal_beads": "Анальные бусы", "anal_plug": "Анальная пробка",
        "anal_expander": "Анальный расширитель", "gag": "Кляп",
        "piercing": "Пирсинг", "long_dildo_path": "Дилдо из ануса выходит изо рта"
    },
    "poses": {
        "doggy": "Наездница", "standing": "Стоя", "splits": "Шпагат",
        "squat": "Приседание", "lying": "Лежа", "hor_split": "Горизонтальный шпагат",
        "ver_split": "Вертикальный шпагат", "side_up_leg": "На боку с ногой вверх",
        "front_facing": "Лицом к зрителю", "back_facing": "Спиной к зрителю",
        "lying_knees_up": "Лежа с коленями вверх", "bridge": "Мост", "suspended": "Подвешена"
    },
    "clothes": {
        "stockings": "Чулки", "bikini_tan_lines": "Загар от бикини", "mask": "Маска",
        "heels": "Каблуки", "shibari": "Шибари"
    },
    "body": {
        "big_breasts": "Большая грудь", "small_breasts": "Маленькая грудь",
        "skin_white": "Белая кожа", "skin_black": "Чёрная кожа",
        "body_fat": "Пышное тело", "body_thin": "Худое тело", "body_normal": "Нормальное тело",
        "body_fit": "Подтянутое тело", "body_muscular": "Мускулистое тело",
        "age_loli": "Лоли", "age_milf": "Милфа", "age_21": "Возраст 21",
        "cum": "Вся в сперме", "belly_bloat": "Вздутие живота",
        "succubus_tattoo": "Тату внизу живота"
    },
    "ethnos": {
        "futanari": "Футанари", "femboy": "Фембой",
        "ethnicity_asian": "Азиатка", "ethnicity_european": "Европейка"
    },
    "furry": {
        "furry_cow": "Фури корова", "furry_cat": "Фури кошка", "furry_dog": "Фури собака",
        "furry_dragon": "Фури дракон", "furry_sylveon": "Фури сильвеон",
        "furry_fox": "Фури лисица", "furry_bunny": "Фури кролик", "furry_wolf": "Фури волчица"
    },
    "characters": {
        "rias": "Риас Гремори", "akeno": "Акено Химедзима", "kafka": "Кафка (Хонкай)",
        "eula": "Еола (Геншин)", "fu_xuan": "Фу Сюань", "ayase": "Аясе Сейко"
    },
    "head": {
        "ahegao": "Ахегао", "pain_face": "Лицо в боли", "ecstasy_face": "Лицо в экстазе",
        "gold_lipstick": "Золотая помада"
    },
    "view": {
        "view_bottom": "Снизу", "view_top": "Сверху",
        "view_side": "Сбоку", "view_close": "Ближе", "view_full": "Дальше"
    }
}

RU_TO_TAG = {}
for cat_tags in TAGS.values():
    for key, ru_name in cat_tags.items():
        RU_TO_TAG[ru_name.lower()] = key

TAG_PROMPTS = {
    "gold_lipstick": "gold lipstick on lips only",
    "ahegao": "ahegao, drooling, tongue out, eyes rolled back",
    "pain_face": "expression of pain, tears",
    "ecstasy_face": "orgasmic expression, flushed, eyes half closed",
    "no_hands_on_chest": "no hands on chest, hands away from breasts",
    "no_covering": "no hands covering genitals",
    "futanari": "futanari, penis, no distortion, full body",
    "suspended": "rope suspension, full body visible, bondage",
    "hor_split": "horizontal split, stretched legs",
    "ver_split": "vertical split, legs apart, balanced",
    "bridge": "body bridge pose, realistic",
    "cum": "covered in cum, dripping, wet",
    "vagina": "spread vagina, visible, realistic",
    "anal": "spread anus, detailed, realistic",
    "both": "spread anus and vagina, visible",
    "view_close": "close-up view",
    "view_full": "full body, uncropped",
    "heels": "high heels, visible",
    "stockings": "thigh high stockings, sheer",
    "shibari": "shibari ropes, tight",
    "gag": "ball gag in mouth",
    "mask": "leather mask"
}

BASE_PROMPT = "nsfw, anime style, high detail, masterpiece, best quality, solo female, nude, detailed face, full body, realistic skin"
NEGATIVE_PROMPT = "lowres, bad anatomy, error, blurry, cropped, extra limbs, mutated hands, disfigured face, deformed, watermark, text, signature, bad proportions, ugly, poorly drawn"

# Функция генерации финального prompt
def build_prompt(tags):
    prompts = [TAG_PROMPTS.get(tag, tag) for tag in tags]
    return BASE_PROMPT + ", " + ", ".join(prompts)

# Отправка запроса в Replicate с учётом negative_prompt
def replicate_generate(prompt):
    url = "https://api.replicate.com/v1/predictions"
    headers = {"Authorization": f"Token {REPLICATE_TOKEN}", "Content-Type": "application/json"}
    json_data = {
        "version": REPLICATE_MODEL,
        "input": {
            "prompt": prompt,
            "negative_prompt": NEGATIVE_PROMPT,
        }
    }
    r = requests.post(url, headers=headers, json=json_data)
    if r.status_code != 201:
        return None
    status_url = r.json()["urls"]["get"]
    for _ in range(60):
        time.sleep(2)
        r = requests.get(status_url, headers=headers)
        if r.status_code != 200:
            return None
        data = r.json()
        if data["status"] == "succeeded":
            output = data["output"]
            return output[0] if isinstance(output, list) else output
        elif data["status"] == "failed":
            return None
    return None