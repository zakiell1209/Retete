import os
import time
import requests
import telebot
from telebot import types
from flask import Flask, request

API_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://retete.onrender.com")

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# Для хранения выбора пользователя (можно заменить на redis/db для мультипользователей)
user_choices = {}

# Промты для каждой опции
PROMPT_PARTS = {
    "anal": "anal sex, anus, detailed anal penetration",
    "dildo": "dildo, large dildo, realistic dildo, inserted dildo",
    "poses": {
        "doggy": "doggy style position, bent over",
        "vertical_splits": "vertical splits pose, flexible legs",
        "squatting": "squatting pose, low stance",
        "missionary": "missionary position, face-to-face",
    },
    "sex_scene": "erotic sex scene, explicit, intimate interaction, realistic anatomy",
    "femboy": (
        "femboy, slender body, feminine face, soft skin, slight makeup, "
        "androgynous features, lingerie, slim waist, cute expression"
    )
}

# Функция сборки итогового промта из выбранных опций
def build_prompt(base_text, selections):
    prompt = base_text.strip() if base_text else ""
    # Добавляем выбранные опции
    if "anal" in selections:
        prompt += ", " + PROMPT_PARTS["anal"]
    if "dildo" in selections:
        prompt += ", " + PROMPT_PARTS["dildo"]
    if "sex_scene" in selections:
        prompt += ", " + PROMPT_PARTS["sex_scene"]
    if "femboy" in selections:
        prompt += ", " + PROMPT_PARTS["femboy"]

    # Позиции — их может быть несколько
    poses_selected = [p for p in selections if p.startswith("pose_")]
    for pose_key in poses_selected:
        pose_name = pose_key.replace("pose_", "")
        pose_prompt = PROMPT_PARTS["poses"].get(pose_name)
        if pose_prompt:
            prompt += ", " + pose_prompt

    # Базовые усилители NSFW (можно менять под запрос)
    prompt += ", masterpiece, ultra detailed, 4k, realistic, NSFW"
    return prompt.strip()

# Усилители (на всякий случай оставил)
def enhance_nsfw_female(p): return p + ", nude, erotic, sensual, solo, young female, seductive, large breasts, soft skin"
def enhance_futanari(p): return p + ", futanari, shemale, dickgirl, big breasts, penis, dildo, dildo anal, anal, nude, erotic pose, solo, highly detailed"
def enhance_femboy(p): return p + ", " + PROMPT_PARTS["femboy"]
def enhance_shibari(p): return p + ", shibari, rope bondage, tied up, detailed knots, erotic ropes, submissive pose, cinematic"

# Генерация через Replicate
def generate_image(prompt):
    url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {REPLICATE_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "version": "fb4f086702d6a301ca32c170d926239324a7b7b2f0afc3d232a9c4be382dc3fa",
        "input": {"prompt": prompt}
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        prediction = response.json()
        return prediction["urls"]["get"], None
    return None, f"❌ Ошибка генерации: {response.status_code} {response.text}"

# Кнопки выбора — кнопки-комбинации
def build_selection_keyboard(user_id):
    selections = user_choices.get(user_id, set())

    def button_text(name, key):
        return ("✅ " if key in selections else "☑️ ") + name

    markup = types.InlineKeyboardMarkup(row_width=2)

    # Анал и Дилдо
    markup.add(
        types.InlineKeyboardButton(button_text("Анал", "anal"), callback_data="toggle_anal"),
        types.InlineKeyboardButton(button_text("Дилдо", "dildo"), callback_data="toggle_dildo")
    )
    # Позиции (по 2 на ряд)
    markup.add(
        types.InlineKeyboardButton(button_text("Поза: Раком", "pose_doggy"), callback_data="toggle_pose_doggy"),
        types.InlineKeyboardButton(button_text("Поза: Вертикальный шпагат", "pose_vertical_splits"), callback_data="toggle_pose_vertical_splits")
    )
    markup.add(
        types.InlineKeyboardButton(button_text("Поза: На корточках", "pose_squatting"), callback_data="toggle_pose_squatting"),
        types.InlineKeyboardButton(button_text("Поза: Миссионерская", "pose_missionary"), callback_data="toggle_pose_missionary")
    )
    # Остальные опции
    markup.add(
        types.InlineKeyboardButton(button_text("Сцена секса", "sex_scene"), callback_data="toggle_sex_scene"),
        types.InlineKeyboardButton(button_text("Фембой", "femboy"), callback_data="toggle_femboy")
    )
    # Кнопка генерации
    markup.add(types.InlineKeyboardButton("🚀 Генерировать", callback_data="generate"))

    return markup

# Обработка callback - переключение опций
@bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_") or call.data == "generate")
def callback_handler(call):
    user_id = call.from_user.id
    if user_id not in user_choices:
        user_choices[user_id] = set()

    if call.data.startswith("toggle_"):
        key = call.data[len("toggle_"):]
        if key in user_choices[user_id]:
            user_choices[user_id].remove(key)
        else:
            user_choices[user_id].add(key)
        # Обновляем клавиатуру с новым состоянием
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=build_selection_keyboard(user_id))
        bot.answer_callback_query(call.id, text=f"{key} {'выбрано' if key in user_choices[user_id] else 'снято'}")
    elif call.data == "generate":
        # Запрашиваем у пользователя базовое описание
        msg = bot.send_message(call.message.chat.id, "📝 Введи описание (например, 'голая девушка, видны губы, светлая кожа'):")
        # Сохраняем текущее состояние выбора для этого пользователя
        user_choices[user_id] = user_choices[user_id]  # просто чтобы быть уверенным
        bot.register_next_step_handler(msg, generate_with_selection, user_id)
        bot.answer_callback_query(call.id)

def generate_with_selection(message, user_id):
    selections = user_choices.get(user_id, set())
    base_text = message.text

    prompt = build_prompt(base_text, selections)

    msg_wait = bot.send_message(message.chat.id, "🔞 Генерирую изображение, подожди...")

    status_url, error = generate_image(prompt)
    if error:
        bot.edit_message_text(error, chat_id=message.chat.id, message_id=msg_wait.message_id)
        return

    max_attempts = 45
    delay_seconds = 3

    for attempt in range(max_attempts):
        res = requests.get(status_url, headers={"Authorization": f"Token {REPLICATE_TOKEN}"})
        if res.status_code != 200:
            bot.edit_message_text(f"❌ Ошибка статуса: {res.status_code} {res.text}",
                                  chat_id=message.chat.id, message_id=msg_wait.message_id)
            return
        status = res.json()
        if status.get("status") == "succeeded":
            img = status["output"][0]
            bot.delete_message(message.chat.id, msg_wait.message_id)
            bot.send_photo(message.chat.id, img)
            # После генерации сбрасываем выбор
            user_choices[user_id] = set()
            bot.send_message(message.chat.id, "✅ Генерация завершена! Выбери режимы заново или напиши новое описание.", reply_markup=build_selection_keyboard(user_id))
            return
        elif status.get("status") == "failed":
            bot.edit_message_text("❌ Генерация не удалась.",
                                  chat_id=message.chat.id, message_id=msg_wait.message_id)
            return
        if attempt % 5 == 0:
            bot.edit_message_text(f"🔞 Генерирую изображение, подожди... ({attempt * delay_seconds}s прошло)",
                                  chat_id=message.chat.id, message_id=msg_wait.message_id)
        time.sleep(delay_seconds)

    bot.edit_message_text("❌ Не удалось сгенерировать изображение за отведённое время.",
                          chat_id=message.chat.id, message_id=msg_wait.message_id)

@bot.message_handler(commands=['start'])
def start(message):
    user_choices[message.from_user.id] = set()
    bot.send_message(message.chat.id, "Выбери нужные параметры (можно комбинировать):", reply_markup=build_selection_keyboard(message.from_user.id))

@bot.message_handler(func=lambda m: True)
def handle_any_message(message):
    user_choices[message.from_user.id] = set()
    bot.send_message(message.chat.id, "Пожалуйста, начни с команды /start, чтобы выбрать параметры и сгенерировать изображение.")

# Flask Webhook
@app.route('/', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.data.decode("utf-8"))
    bot.process_new_updates([update])
    return '', 200

@app.route('/', methods=['GET'])
def index():
    return '🤖 Бот работает'

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))