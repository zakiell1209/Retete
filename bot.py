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

REPLICATE_MODELS = {
    "anime": "c1d5b02687df6081c7953c74bcc527858702e8c153c9382012ccc3906752d3ec",
    "realism": "stability-ai/stable-diffusion:ac732df8",
    "3d": "stability-ai/stable-diffusion-3-medium"
}

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
user_settings = {}

# Теги по категориям
TAGS = {
    "poses": ["doggy", "standing", "splits", "squat", "lying", "vert_sp", "horiz_sp", "legs_apart", "side_leg", "face", "back", "bridge", "rope"],
    "holes": ["vagina", "anal", "both"],
    "toys": ["dildo", "beads", "plug", "gag", "piercing"],
    "clothes": ["stockings", "bikini", "mask", "heels", "shibari", "cow_costume", "tan_lines"],
    "body": ["loli", "milf", "age21", "thin", "muscular", "curvy", "normal", "big_breasts", "small_breasts", "black_skin", "white_skin"],
    "ethnicity": ["femboy", "asian", "european"],
    "furry": ["cow", "cat", "dog", "dragon", "silveon"]
}

CATEGORY_NAMES = {
    "poses": "Позиции",
    "holes": "Отверстия",
    "toys": "Игрушки",
    "clothes": "Одежда",
    "body": "Тело",
    "ethnicity": "Этнос",
    "furry": "Фури"
}

# Названия тегов
TAG_RN = {
    "doggy": "Догги",
    "standing": "Стоя",
    "splits": "Шпагат",
    "squat": "Присед",
    "lying": "Лежа",
    "vert_sp": "Вертик.",
    "horiz_sp": "Горизонт.",
    "legs_apart": "Ноги в стороны",
    "side_leg": "На боку",
    "face": "К зрителю",
    "back": "Спиной",
    "bridge": "Мост",
    "rope": "На верёвках",
    "vagina": "Вагина",
    "anal": "Анал",
    "both": "Обоє",
    "dildo": "Дилдо",
    "beads": "Бусы",
    "plug": "Пробка",
    "gag": "Кляп",
    "piercing": "Пирсинг",
    "stockings": "Чулки",
    "bikini": "Бикини",
    "mask": "Маска",
    "heels": "Туфли",
    "shibari": "Шибари",
    "cow_costume": "Коровий костюм",
    "tan_lines": "Загар",
    "loli": "Лоли",
    "milf": "Милфа",
    "age21": "21 год",
    "thin": "Худая",
    "muscular": "Мускулы",
    "curvy": "Пышная",
    "normal": "Норма",
    "big_breasts": "Большие груди",
    "small_breasts": "Маленькие",
    "black_skin": "Чёрная кожа",
    "white_skin": "Белая кожа",
    "femboy": "Фембой",
    "asian": "Азиатка",
    "european": "Европейка",
    "cow": "Фури‑корова",
    "cat": "Фури‑кошка",
    "dog": "Фури‑собака",
    "dragon": "Фури‑дракон",
    "silveon": "Сильвеон"
}

def chunk_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

def main_menu():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🧩 Теги", callback_data="choose_cat"))
    kb.add(types.InlineKeyboardButton("✏ Опис", callback_data="enter_desc"))
    return kb

def category_kb():
    kb = types.InlineKeyboardMarkup(row_width=2)
    for k, n in CATEGORY_NAMES.items():
        kb.add(types.InlineKeyboardButton(n, callback_data=f"cat_{k}"))
    kb.add(types.InlineKeyboardButton("✅ Готово", callback_data="tags_done"))
    return kb

def tag_page_kb(cat, page, sel):
    tags = TAGS[cat]
    pages = list(chunk_list(tags, 6))
    page = max(0, min(page, len(pages)-1))
    items = pages[page]
    kb = types.InlineKeyboardMarkup(row_width=2)
    for t in items:
        mark = "✅" if t in sel else ""
        kb.add(types.InlineKeyboardButton(f"{mark} {TAG_RN[t]}", callback_data=f"tag_{t}_{cat}_{page}"))
    nav = []
    if page>0: nav.append(types.InlineKeyboardButton("⬅", callback_data=f"page_{cat}_{page-1}"))
    if page< len(pages)-1: nav.append(types.InlineKeyboardButton("➡", callback_data=f"page_{cat}_{page+1}"))
    if nav: kb.add(*nav)
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="choose_cat"))
    return kb

# Генерация через Replicate
def replicate_generate(prompt, model_id):
    resp = requests.post("https://api.replicate.com/v1/predictions",
                         json={"version": model_id, "input":{"prompt":prompt}},
                         headers={"Authorization":f"Token {REPLICATE_TOKEN}"})
    if resp.status_code==201:
        return resp.json()["urls"]["get"]
    return None

def replicate_wait(status_url):
    for _ in range(40):
        time.sleep(2)
        r = requests.get(status_url, headers={"Authorization":f"Token {REPLICATE_TOKEN}"})
        j = r.json()
        if j.get("status")=="succeeded":
            out = j["output"]
            return out[0] if isinstance(out, list) else out
        if j.get("status")=="failed": break
    return None

@bot.message_handler(commands=["start"])
def start(m):
    cid = m.chat.id
    user_settings[cid] = {"sel": [], "last": [], "wait": False}
    bot.send_message(cid, "Привет! Что сделать:", reply_markup=main_menu())

@bot.callback_query_handler(lambda c: True)
def cb(c):
    cid = c.message.chat.id
    data = c.data
    u = user_settings.setdefault(cid,{"sel":[],"last":[],"wait":False})

    if data=="choose_cat":
        bot.edit_message_text("Выберите категорию:", cid, c.message.message_id, reply_markup=category_kb())
    elif data.startswith("cat_"):
        cat=data.split("_",1)[1]
        bot.edit_message_text(f"{CATEGORY_NAMES[cat]}:", cid, c.message.message_id, reply_markup=tag_page_kb(cat,0,u["sel"]))
    elif data.startswith("page_"):
        _,cat,p = data.split("_"); p=int(p)
        bot.edit_message_text(f"{CATEGORY_NAMES[cat]}:", cid, c.message.chat.id, call_id:=c.message.message_id, reply_markup=tag_page_kb(cat,p,u["sel"]))
    elif data.startswith("tag_"):
        _,t,cat,p = c.data.split("_")
        p=int(p)
        if t in u["sel"]: u["sel"].remove(t)
        else: u["sel"].append(t)
        bot.edit_message_reply_markup(cid, c.message.message_id, reply_markup=tag_page_kb(cat,p,u["sel"]))
    elif data=="tags_done":
        u["last"]=u["sel"][:]
        bot.edit_message_text("Теги сохранены. Теперь введите описание.", cid, c.message.chat.id, reply_markup=main_menu())
    elif data=="enter_desc":
        u["wait"]=True
        bot.send_message(cid, "Введите описание:")
    elif data=="continue_gen":
        u["wait"]=True
        bot.send_message(cid, "Допишите описание:")
    elif data=="edit_tags":
        u["sel"]=u["last"][:]
        bot.send_message(cid, "Редактируйте теги:", reply_markup=category_kb())
    elif data=="main_menu":
        bot.edit_message_text("Что сделать:", cid, c.message.message_id, reply_markup=main_menu())

@bot.message_handler(lambda m: user_settings.get(m.chat.id,{}).get("wait"))
def desc(m):
    cid=m.chat.id; u=user_settings[cid]
    u["wait"]=False
    desc_text=m.text.strip()
    full = desc_text + ", " + ", ".join(u["sel"])
    bot.send_message(cid, f"Генерация: `{full}`", parse_mode="Markdown")
    status=replicate_generate(full, REPLICATE_MODELS["anime"])
    if not status:
        bot.send_message(cid, "Ошибка генерации.")
        return
    img_url=replicate_wait(status)
    if img_url:
        u["last"]=u["sel"][:]
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("▶ Продолжить", callback_data="continue_gen"))
        kb.add(types.InlineKeyboardButton("🧩 Теги", callback_data="edit_tags"))
        kb.add(types.InlineKeyboardButton("🏠 Меню", callback_data="main_menu"))
        bot.send_photo(cid, img_url, caption="Результат:", reply_markup=kb)
    else:
        bot.send_message(cid,"Ошибка генерации изображения.")

@app.route("/", methods=["POST"])
def wh():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "ok",200

@app.route("/", methods=["GET"])
def index():
    return "OK",200

if __name__=="__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=PORT)