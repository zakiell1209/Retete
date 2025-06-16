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

# Структура user_settings теперь:
# {
#   cid: {
#     "drafts": [  # список драфтов (промтов)
#        {"base": str, "tags": list, "model": str}
#     ],
#     "current_draft": int,  # индекс активного драфта
#     "waiting_for_prompt": bool,
#     "waiting_for_edit_prompt": bool,
#     "waiting_for_edit_tags": bool,
#     "waiting_for_edit_model": bool,
#     "history": [ { "prompt": str, "image_url": str } ] # для истории
#   }
# }

user_settings = {}

# === Теги и клавиатуры (без изменений) ===
# ... здесь вставь твои словари TAGS, CATEGORY_NAMES_EMOJI, CLOTHES_NAMES_EMOJI, TAG_NAMES_EMOJI, как у тебя сейчас ...

# Добавим флаг выбора для тегов (галочки)
def tags_keyboard_with_selection(category, selected_tags):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for tag in TAGS.get(category, []):
        if category == "clothes":
            name = CLOTHES_NAMES_EMOJI.get(tag, tag)
        else:
            name = TAG_NAMES_EMOJI.get(category, {}).get(tag, tag)
        # Добавляем галочку если выбран
        if tag in selected_tags:
            name = "✅ " + name
        markup.add(types.InlineKeyboardButton(name, callback_data=f"tag_{tag}"))
    markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="tags_back"))
    return markup

# === Основное меню ===
def main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🎨 Выбрать модель", callback_data="model"),
        types.InlineKeyboardButton("🧩 Выбрать теги", callback_data="tags"),
        types.InlineKeyboardButton("📝 Редактировать описание", callback_data="edit_base"),
        types.InlineKeyboardButton("✅ Генерировать", callback_data="generate"),
        types.InlineKeyboardButton("🗂 Управление драфтами", callback_data="manage_drafts"),
        types.InlineKeyboardButton("📜 История генераций", callback_data="history")
    )
    return markup

def model_keyboard(selected_model=None):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for key, name in [("anime", "🖌 Аниме"), ("realism", "📷 Реализм"), ("3d", "🧱 3D")]:
        display_name = name
        if selected_model == key:
            display_name = "✅ " + name
        markup.add(types.InlineKeyboardButton(display_name, callback_data=f"model_{key}"))
    markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="main_menu"))
    return markup

def category_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    for cat in CATEGORY_NAMES_EMOJI:
        markup.add(types.InlineKeyboardButton(CATEGORY_NAMES_EMOJI[cat], callback_data=f"cat_{cat}"))
    markup.add(types.InlineKeyboardButton("✅ Готово", callback_data="tags_done"))
    return markup

def tags_keyboard(category, selected_tags):
    # Используем обновленную функцию с галочками
    return tags_keyboard_with_selection(category, selected_tags)

def drafts_keyboard(drafts, current_index):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, draft in enumerate(drafts):
        base_short = draft["base"][:20] + ("..." if len(draft["base"]) > 20 else "")
        name = f"#{i+1} {'(активный)' if i == current_index else ''} - {base_short}"
        markup.add(types.InlineKeyboardButton(name, callback_data=f"draft_select_{i}"))
    markup.add(types.InlineKeyboardButton("➕ Создать новый драфт", callback_data="draft_new"))
    markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="main_menu"))
    return markup

def draft_actions_keyboard(draft_index):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✏️ Редактировать описание", callback_data=f"draft_edit_base_{draft_index}"),
        types.InlineKeyboardButton("🧩 Редактировать теги", callback_data=f"draft_edit_tags_{draft_index}"),
        types.InlineKeyboardButton("🎨 Выбрать модель", callback_data=f"draft_edit_model_{draft_index}"),
        types.InlineKeyboardButton("🗑 Удалить драфт", callback_data=f"draft_delete_{draft_index}"),
        types.InlineKeyboardButton("⬅ Назад", callback_data="manage_drafts")
    )
    return markup

def history_keyboard(history):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, item in enumerate(history[-10:][::-1]):  # последние 10
        base_short = item["prompt"][:30] + ("..." if len(item["prompt"]) > 30 else "")
        markup.add(types.InlineKeyboardButton(f"#{len(history)-i} {base_short}", callback_data=f"history_{len(history)-1 - i}"))
    markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="main_menu"))
    return markup

# ==== Обработка команд ====

@bot.message_handler(commands=["start"])
def start(message):
    cid = message.chat.id
    if cid not in user_settings:
        user_settings[cid] = {
            "drafts": [{"base": "", "tags": [], "model": "anime"}],
            "current_draft": 0,
            "waiting_for_prompt": False,
            "waiting_for_edit_prompt": False,
            "waiting_for_edit_tags": False,
            "waiting_for_edit_model": False,
            "history": []
        }
    bot.send_message(cid, "Привет! Выбери действие:", reply_markup=main_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    cid = call.message.chat.id
    data = call.data
    user = user_settings.setdefault(cid, {
        "drafts": [{"base": "", "tags": [], "model": "anime"}],
        "current_draft": 0,
        "waiting_for_prompt": False,
        "waiting_for_edit_prompt": False,
        "waiting_for_edit_tags": False,
        "waiting_for_edit_model": False,
        "history": []
    })

    def current_draft():
        return user["drafts"][user["current_draft"]]

    if data == "main_menu":
        bot.edit_message_text("Главное меню:", cid, call.message.message_id, reply_markup=main_keyboard())
        reset_waiting_flags(user)

    elif data == "model":
        bot.edit_message_text("Выбери модель:", cid, call.message.message_id, reply_markup=model_keyboard(current_draft()["model"]))

    elif data.startswith("model_"):
        model = data.split("_")[1]
        current_draft()["model"] = model
        bot.edit_message_text(f"Модель установлена: {model}", cid, call.message.message_id, reply_markup=main_keyboard())
        reset_waiting_flags(user)

    elif data == "tags":
        bot.edit_message_text("Выбери категорию:", cid, call.message.message_id, reply_markup=category_keyboard())

    elif data.startswith("cat_"):
        cat = data.split("_")[1]
        bot.edit_message_text(f"Выбери теги категории {CATEGORY_NAMES_EMOJI[cat]}:", cid, call.message.message_id,
                              reply_markup=tags_keyboard(cat, current_draft()["tags"]))

    elif data.startswith("tag_"):
        tag = data.split("_")[1]
        tags = current_draft()["tags"]
        if tag in tags:
            tags.remove(tag)
            bot.answer_callback_query(call.id, f"Тег '{tag}' удалён")
        else:
            tags.append(tag)
            bot.answer_callback_query(call.id, f"Тег '{tag}' добавлен")
        # Обновляем клавиатуру с выделением
        cat = find_category_of_tag(tag)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id,
                                      reply_markup=tags_keyboard(cat, tags))

    elif data == "tags_done":
        bot.edit_message_text("Теги сохранены.", cid, call.message.message_id, reply_markup=main_keyboard())
        reset_waiting_flags(user)

    elif data == "tags_back":
        bot.edit_message_text("Выбери категорию:", cid, call.message.message_id, reply_markup=category_keyboard())

    elif data == "edit_base":
        user["waiting_for_edit_prompt"] = True
        bot.send_message(cid, "Введи новое описание:")

    elif data == "generate":
        bot.send_message(cid, "Выбери действие:", reply_markup=types.InlineKeyboardMarkup(row_width=1).add(
            types.InlineKeyboardButton("▶️ Продолжить с текущим промтом", callback_data="gen_continue"),
            types.InlineKeyboardButton("🔄 Начать заново", callback_data="gen_restart"),
            types.InlineKeyboardButton("⬅ Отмена", callback_data="main_menu")
        ))

    elif data == "gen_continue":
        user["waiting_for_prompt"] = True
        bot.send_message(cid, f"Текущий промт:\n{current_draft()['base']}\n\n✏️ Введи дополнение к описанию:")

    elif data == "gen_restart":
        current_draft()["base"] = ""
        current_draft()["tags"] = []
        bot.send_message(cid, "Начни ввод нового описания:")
        user["waiting_for_prompt"] = True

    elif data == "manage_drafts":
        bot.edit_message_text("Выбери драфт:", cid, call.message.message_id,
                              reply_markup=drafts_keyboard(user["drafts"], user["current_draft"]))

    elif data.startswith("draft_select_"):
        idx = int(data.split("_")[2])
        user["current_draft"] = idx
        bot.edit_message_text(f"Активный драфт #{idx + 1}", cid, call.message.message_id,
                              reply_markup=draft_actions_keyboard(idx))

    elif data == "draft_new":
        user["drafts"].append({"base": "", "tags": [], "model": "anime"})
        user["current_draft"] = len(user["drafts"]) - 1
        bot.edit_message_text(f"Создан новый драфт #{user['current_draft'] + 1}", cid, call.message.message_id,
                              reply_markup=draft_actions_keyboard(user["current_draft"]))

    elif data.startswith("draft_edit_base_"):
        idx = int(data.split("_")[3])
        if idx == user["current_draft"]:
            user["waiting_for_edit_prompt"] = True
            bot.send_message(cid, "Введи новое описание:")
        else:
            bot.answer_callback_query(call.id, "Можно редактировать только активный драфт")

    elif data.startswith("draft_edit_tags_"):
        idx = int(data.split("_")[3])
        if idx == user["current_draft"]:
            user["waiting_for_edit_tags"] = True
            bot.send_message(cid, "Выбери категорию:", reply_markup=category_keyboard())
        else:
            bot.answer_callback_query(call.id, "Можно редактировать только активный драфт")

    elif data.startswith("draft_edit_model_"):
        idx = int(data.split("_")[3])
        if idx == user["current_draft"]:
            bot.edit_message_text("Выбери модель:", cid, call.message.message_id,
                                  reply_markup=model_keyboard(current_draft()["model"]))
            user["waiting_for_edit_model"] = True
        else:
            bot.answer_callback_query(call.id, "Можно редактировать только активный драфт")

    elif data.startswith("draft_delete_"):
        idx = int(data.split("_")[2])
        if len(user["drafts"]) == 1:
            bot.answer_callback_query(call.id, "Нельзя удалить последний драфт")
            return
        user["drafts"].pop(idx)
        if user["current_draft"] >= len(user["drafts"]):
            user["current_draft"] = len(user["drafts"]) - 1
        bot.edit_message_text("Драфт удалён.", cid, call.message.message_id,
                              reply_markup=drafts_keyboard(user["drafts"], user["current_draft"]))

    elif data == "history":
        if not user["history"]:
            bot.edit_message_text("История пуста.", cid, call.message.message_id,
                                  reply_markup=main_keyboard())
        else:
            bot.edit_message_text("История последних генераций:", cid, call.message.message_id,
                                  reply_markup=history_keyboard(user["history"]))

    elif data.startswith("history_"):
        idx = int(data.split("_")[1])
        if idx >= 0 and idx < len(user["history"]):
            hist = user["history"][idx]
            bot.send_photo(cid, hist["image_url"], caption=f"Промт:\n{hist['prompt']}", reply_markup=main_keyboard())
        else:
            bot.answer_callback_query(call.id, "Неверный индекс истории")

    else:
        bot.answer_callback_query(call.id, "Неизвестная команда")

def reset_waiting_flags(user):
    user["waiting_for_prompt"] = False
    user["waiting_for_edit_prompt"] = False
    user["waiting_for_edit_tags"] = False
    user["waiting_for_edit_model"] = False

def find_category_of_tag(tag):
    for cat, tags in TAGS.items():
        if tag in tags:
            return cat
    return None

@bot.message_handler(func=lambda m: True)
def handle_messages(message):
    cid = message.chat.id
    if cid not in user_settings:
        bot.send_message(cid, "Напиши /start для начала работы.")
        return

    user = user_settings[cid]

    if user.get("waiting_for_edit_prompt"):
        # Редактируем описание драфта
        current = user["drafts"][user["current_draft"]]
        current["base"] = message.text.strip()
        user["waiting_for_edit_prompt"] = False
        bot.send_message(cid, "Описание сохранено.", reply_markup=main_keyboard())

    elif user.get("waiting_for_prompt"):
        # Генерация, добавляем или дополняем описание
        current = user["drafts"][user["current_draft"]]
        if current["base"]:
            # Дополняем описание, если продолжение
            current["base"] += ", " + message.text.strip()
        else:
            current["base"] = message.text.strip()
        user["waiting_for_prompt"] = False

        bot.send_message(cid, "⏳ Генерация изображения...")
        model_id = REPLICATE_MODELS.get(current["model"], REPLICATE_MODELS["anime"])
        full_prompt = build_prompt(current["base"], current["tags"])
        status_url, err = generate_image(full_prompt, model_id)
        if err:
            bot.send_message(cid, err)
            return

        image_url = wait_for_image(status_url)
        if image_url:
            bot.send_photo(cid, image_url, caption="Вот результат!", reply_markup=main_keyboard())
            # Сохраняем в историю
            user["history"].append({"prompt": full_prompt, "image_url": image_url})
        else:
            bot.send_message(cid, "❌ Ошибка генерации изображения.")

    elif user.get("waiting_for_edit_tags"):
        # Во время редактирования тегов ждем выбор категорий и тегов, но обработка тут не нужна
        bot.send_message(cid, "Пожалуйста, выбери теги через кнопки.")

    elif user.get("waiting_for_edit_model"):
        bot.send_message(cid, "Пожалуйста, выбери модель через кнопки.")

    else:
        bot.send_message(cid, "Неверная команда. Используй меню.", reply_markup=main_keyboard())

# === Промт сборка и генерация ===

def build_prompt(base, tags):
    additions = []
    map_tag = {
        "vagina": "vaginal penetration", "anal": "anal penetration", "both": "double penetration",
        "dildo": "dildo", "anal_beads": "anal beads", "anal_plug": "anal plug", "gag": "gag",
        "doggy": "doggy style", "standing": "standing pose", "splits": "splits", "squat": "squatting", "lying": "laying",
        "stockings": "stockings", "bikini": "bikini", "mask": "mask", "heels": "high heels", "shibari": "shibari",
        "cow_costume": "cow costume", "bikini_tan_lines": "bikini tan lines",
        "big_breasts": "large breasts", "small_breasts": "small breasts", "