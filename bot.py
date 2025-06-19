# --- bot.py ---
import os
import time
import requests
from flask import Flask, request
import telebot
from telebot import types

API_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 5000))

REPLICATE_MODEL = "c1d5b02687df6081c7953c74bcc527858702e8c153c9382012ccc3906752d3ec"

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
user_settings = {}

CATEGORY_NAMES = {
    "holes": "Отверстия",
    "toys": "Игрушки",
    "poses": "Позы",
    "clothes": "Одежда",
    "body": "Тело",
    "ethnos": "Этнос",
    "furry": "Фури",
    "characters": "Персонажи",
    "head": "Голова",
    "view": "Обзор"
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
        "hor_split": "Горизонтальный шпагат",
        "ver_split": "Вертикальный шпагат"
    },
    "clothes": {
        "stockings": "Чулки",
        "shibari": "Шибари"
    },
    "body": {
        "big_breasts": "Большая грудь"
    },
    "ethnos": {
        "futanari": "Футанари"
    },
    "furry": {
        "furry_cat": "Фури кошка"
    },
    "characters": {
        "rias": "Риас Гремори"
    },
    "head": {
        "ahegao": "Ахегао",
        "gold_lipstick": "Золотая помада"
    },
    "view": {
        "bottom_view": "Снизу",
        "top_view": "Сверху",
        "side_view": "Сбоку",
        "far_view": "Дальше",
        "close_view": "Ближе"
    }
}

CHARACTER_EXTRA = {
    "rias": (
        "1girl, solo, red long hair, blue eyes, pale skin, large breasts, rias gremory, highschool dxd, "
        "exact face, consistent character, no other girls"
    )
}

TAG_PROMPTS = {
    **CHARACTER_EXTRA,
    "vagina": "spread pussy",
    "anal": "spread anus, anus focus",
    "both": "spread pussy and anus",
    "dildo": "dildo inserted in anus, penetration, sex toy interaction",
    "huge_dildo": "huge dildo inserted, stretching effect",
    "horse_dildo": "horse dildo, visible penetration",
    "anal_beads": "anal beads inserted, anus stretching",
    "anal_plug": "anal plug, visible insertion",
    "anal_expander": "anal expander in anus",
    "gag": "ball gag in mouth",
    "piercing": "nipple and clit piercings",
    "long_dildo_path": (
        "very long dildo inserted into anus and exiting mouth, smooth continuous shape, belly bulge visible"
    ),
    "hor_split": (
        "horizontal split on floor, one girl, pelvis touching ground, legs flat to sides, thighs spread, "
        "natural pose, high detail, full body visible"
    ),
    "ver_split": (
        "vertical split pose, one girl, leg lifted straight, standing or upright, balance, full body"
    ),
    "stockings": "wearing thigh-high stockings, visible",
    "shibari": "shibari rope bondage, rope on body",
    "big_breasts": "very large breasts, visible nipples, chest fully exposed",
    "futanari": "futanari girl, visible erect penis, solo, breasts visible, feminine body",
    "furry_cat": "furry cat girl, fur on body, tail, cat ears",
    "ahegao": "ahegao expression, tongue out, eyes rolled",
    "gold_lipstick": "gold lipstick on lips",
    "bottom_view": "low angle view, camera below subject, body pressing down",
    "top_view": "top view, camera above girl",
    "side_view": "side view angle",
    "far_view": "full body in frame, far shot, wide angle",
    "close_view": "close-up, parts of body outside frame",
}

def build_prompt(tags):
    base = (
        "nsfw, masterpiece, anime style, best quality, solo, 1girl, fully nude, "
        "no clothes, no censorship, no hands on chest, no arms covering breasts, "
        "visible nipples, full body, avoid extra characters"
    )
    prompts = [TAG_PROMPTS.get(tag, tag) for tag in tags]
    return base + ", " + ", ".join(prompts)
