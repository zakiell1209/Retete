import os, time, requests
from flask import Flask, request
import telebot
from telebot import types

API_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")
REPLICATE_MODEL = "057e2276ac5dcd8d1575dc37b131f903df9c10c41aed53d47cd7d4f068c19fa5"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 5000))

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
user_settings = {}

NEG_PROMPT = (
    "male, man, penis, testicles, muscular male, hands on chest, hands covering nipples, "
    "hand on breast, censored clothes, bra, panties, blur, lowres, watermark, text"
)

CATEGORY_NAMES = {
 "holes": "Отверстия", "toys": "Игрушки", "poses": "Позы", "clothes": "Одежда",
 "body": "Тело", "ethnos": "Этнос", "furry": "Фури", "characters": "Персонажи",
 "head": "Голова", "view": "Обзор"
}

TAGS = {
 "holes": {
     "vagina": "Вагина", "anal": "Анус", "both": "Вагина+Анал"
 },
 "toys": {
     "dildo": "Дилдо", "huge_dildo": "Большое дилдо", "horse_dildo": "Лошадиное дилдо",
     "anal_beads": "Анальные бусы", "anal_plug": "Анальная пробка",
     "anal_expander": "Анальный расширитель", "gag": "Кляп", "piercing": "Пирсинг",
     "long_dildo_path": "Дилдо сквозь тело"
 },
 "poses": {
     "doggy": "Поз. Догги", "standing": "Стоя", "squat": "Присед",
     "lying": "Лежа", "ver_split": "Вертикальный шпагат", "hor_split": "Гориз. шпагат",
     "bridge": "Мост", "suspended": "Подвешена", "side_up_leg": "На боку+ногу"
 },
 "clothes": {
     "stockings": "Чулки", "shibari": "Шибари", "heels": "Каблуки",
     "bikini_tan_lines": "Загар от бикини"
 },
 "body": {
     "big_breasts": "Большая грудь", "small_breasts": "Маленькая грудь",
     "body_thin": "Худое тело", "body_fat": "Пышное тело",
     "skin_white": "Белая кожа", "skin_black": "Чёрная кожа",
     "cum": "В сперме", "belly_bloat": "Вздутие живота",
     "succubus_tattoo": "Тату на животе"
 },
 "ethnos": {
     "futanari": "Футанари", "femboy": "Фембой",
     "ethnicity_asian": "Азиатка", "ethnicity_european": "Европейка"
 },
 "furry": {
     "furry_cow": "Фури‑корова", "furry_fox": "Фури‑лисица",
     "furry_wolf": "Фури‑волчица"
 },
 "characters": {
     "rias": "Риас Гремори", "akeno": "Акено Химэдзима",
     "kafka": "Кафка (Хонкай)", "eula": "Еола (Геншин)",
     "fu_xuan": "Фу Сюань", "ayase": "Аясе Сейко",
     "kiana": "Киана (LoL)", "yor_forger": "Йор Форжер",
     "esdeath": "Эсдес", "asia_argento": "Асия",
     "koneko": "Конеко", "chun_li": "Чун Ли", "2b": "2B (NieR)"
 },
 "head": {
     "ahegao": "Ахегао", "pain_face": "Лицо в боли",
     "ecstasy_face": "Лицо в экстазе", "gold_lipstick": "Золотая помада"
 },
 "view": {
     "view_top": "Сверху", "view_bottom": "Снизу",
     "view_side": "Сбоку", "view_close": "Крупный план",
     "view_full": "Полный рост"
 }
}

def start(msg):
    cid = msg.chat.id
    user_settings[cid] = {"tags": [], "count": 1}
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🧩 Теги", callback_data="tags"))
    markup.add(types.InlineKeyboardButton("🎨 Генерировать", callback_data="generate"))
    bot.send_message(cid, "Привет! Что делаем?", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: True)
def callback(call):
    cid, data = call.message.chat.id, call.data
    user = user_settings.setdefault(cid, {"tags": [], "count": 1})

    if data == "tags": show_categories(call)
    elif data.startswith("cat_"): show_tags(call, data[4:])
    elif data.startswith("tag_"):
        _, cat, tag = data.split("_",2)
        tags = user["tags"]
        tags.append(tag) if tag not in tags else tags.remove(tag)
        show_tags(call, cat)
    elif data == "done_tags": bot.edit_message_text("Теги сохранены!", cid, call.message.message_id, reply_markup=main_markup())
    elif data == "generate": do_generate(cid)
    elif data == "start_over": start(call.message)
    elif data == "edit_tags": show_categories(call)

def show_categories(call):
    cid, mid = call.message.chat.id, call.message.message_id
    kb=types.InlineKeyboardMarkup(row_width=2)
    for k,v in CATEGORY_NAMES.items():
        kb.add(types.InlineKeyboardButton(v, callback_data=f"cat_{k}"))
    kb.add(types.InlineKeyboardButton("✅ Сохранить", callback_data="done_tags"))
    bot.edit_message_text("Выбери категорию:", cid, mid, reply_markup=kb)

def show_tags(call, cat):
    cid, mid = call.message.chat.id, call.message.message_id
    sel = user_settings[cid]["tags"]
    kb=types.InlineKeyboardMarkup(row_width=2)
    for tk, lbl in TAGS[cat].items():
        pre = "✅ " if tk in sel else ""
        kb.add(types.InlineKeyboardButton(pre+lbl, callback_data=f"tag_{cat}_{tk}"))
    kb.add(types.InlineKeyboardButton("⬅ Назад", callback_data="tags"))
    bot.edit_message_text(CATEGORY_NAMES[cat], cid, mid, reply_markup=kb)

def main_markup():
    kb=types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🧩 Теги", callback_data="tags"))
    kb.add(types.InlineKeyboardButton("🎨 Генерировать", callback_data="generate"))
    return kb

def do_generate(cid):
    user = user_settings[cid]
    if not user["tags"]:
        return bot.send_message(cid, "❌ Сначала выбери теги!")
    count = max(1, min(user.get("count",1), 4))
    prompt = build_prompt(user["tags"])
    urls = replicate_generate(prompt,count)
    if not urls:
        return bot.send_message(cid, "❌ Ошибка генерации.")
    media=[types.InputMediaPhoto(u) for u in urls]
    bot.send_media_group(cid, media)
    kb=types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔁 Начать заново", callback_data="start_over"))
    kb.add(types.InlineKeyboardButton("🔧 Изменить теги", callback_data="edit_tags"))
    kb.add(types.InlineKeyboardButton("➡ Повторить", callback_data="generate"))
    bot.send_message(cid, "✅ Готово!", reply_markup=kb)

def build_prompt(tags):
    base = "nsfw, masterpiece, best quality, fully nude, solo female, anime style"
    for t in tags:
        base += ", " + TAGS[next(cat for cat in CATEGORY_NAMES if t in TAGS[cat])][t]
    return base

def replicate_generate(prompt, n):
    url = "https://api.replicate.com/v1/predictions"
    headers={"Authorization":f"Token {REPLICATE_TOKEN}","Content-Type":"application/json"}
    j={"version":REPLICATE_MODEL,"input":{"prompt":prompt,"negative_prompt":NEG_PROMPT,"num_outputs":n}}
    r=requests.post(url,headers=headers,json=j)
    if r.status_code!=201: return []
    su = r.json()["urls"]["get"]
    for _ in range(40):
        time.sleep(2)
        r=requests.get(su,headers=headers)
        if r.status_code!=200: return []
        d=r.json()
        if d["status"]=="succeeded": return d["output"] if isinstance(d["output"],list) else [d["output"]]
        if d["status"]=="failed": return []
    return []

@app.route("/",methods=["POST"])
def webhook():
    update=telebot.types.Update.de_json(request.stream.read().decode(),bot)
    bot.process_new_updates([update])
    return "ok",200

@app.route("/",methods=["GET"])
def home():
    return "бот работает",200

if __name__=="__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0",port=PORT)