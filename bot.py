import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor

API_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Модель аниме (твоя версия)
REPLICATE_MODEL_VERSION = "c1d5b02687df6081c7953c74bcc527858702e8c153c9382012ccc3906752d3ec"

# Секции и их кнопки с промтами
SECTIONS = {
    "holes": {
        "label": "Отверстие",
        "options": {
            "vagina": "vagina, visible vulva, detailed vagina",
            "anal": "anal, detailed anal penetration",
            "both": "vagina and anal, dual penetration"
        }
    },
    "toys": {
        "label": "Игрушки",
        "options": {
            "dildo": "large dildo, realistic dildo, inserted dildo",
            "anal_beads": "anal beads, detailed beads",
            "anal_plug": "anal plug, silicone plug",
            "gag": "gag, ball gag, bondage gag"
        }
    },
    "poses": {
        "label": "Поза",
        "options": {
            "doggy": "doggy style, on all fours, from behind",
            "standing": "standing pose",
            "splits": "splits, horizontal splits, flexible legs",
            "vertical_splits": "vertical splits, upright splits",
            "lying": "lying down pose, relaxed"
        }
    },
    "clothing": {
        "label": "Одежда",
        "options": {
            "stockings": "lace stockings, thigh-high stockings",
            "bikini": "bikini, revealing swimsuit",
            "mask": "mask, face mask, mysterious",
            "high_heels": "high heels, stilettos, sexy shoes"
        }
    }
}

# Хранение выбора пользователя (chat_id -> dict)
user_choices = {}

# Клавиатура главного меню
def main_menu_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    for key, section in SECTIONS.items():
        kb.insert(InlineKeyboardButton(section["label"], callback_data=f"section:{key}"))
    return kb

# Клавиатура с опциями секции + кнопка "Готово"
def section_options_kb(section_key, selected_options):
    kb = InlineKeyboardMarkup(row_width=2)
    options = SECTIONS[section_key]["options"]
    for opt_key, opt_text in options.items():
        prefix = "✅ " if opt_key in selected_options else ""
        kb.insert(InlineKeyboardButton(f"{prefix}{opt_text.split(',')[0]}", callback_data=f"toggle:{section_key}:{opt_key}"))
    kb.add(InlineKeyboardButton("✅ Готово", callback_data="done"))
    return kb

# Формируем итоговый промт из всех выбранных опций
def build_final_prompt(choices: dict):
    prompt_parts = []
    for section_key, selected_opts in choices.items():
        opts = SECTIONS[section_key]["options"]
        for opt_key in selected_opts:
            if opt_key in opts:
                prompt_parts.append(opts[opt_key])
    # Добавим базовые усилители
    prompt_parts.append("anime style, detailed, high quality, NSFW")
    return ", ".join(prompt_parts)

@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    user_choices[message.chat.id] = {k: set() for k in SECTIONS.keys()}
    await message.answer(
        "Выберите категорию для настройки генерации изображения:",
        reply_markup=main_menu_kb()
    )

@dp.callback_query_handler(lambda c: c.data.startswith("section:"))
async def process_section(callback_query: types.CallbackQuery):
    section_key = callback_query.data.split(":")[1]
    selected = user_choices.get(callback_query.from_user.id, {}).get(section_key, set())
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=f"Выберите опции для раздела «{SECTIONS[section_key]['label']}»:",
        reply_markup=section_options_kb(section_key, selected)
    )
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("toggle:"))
async def toggle_option(callback_query: types.CallbackQuery):
    _, section_key, option_key = callback_query.data.split(":")
    user_id = callback_query.from_user.id
    if user_id not in user_choices:
        user_choices[user_id] = {k: set() for k in SECTIONS.keys()}
    selected = user_choices[user_id][section_key]
    if option_key in selected:
        selected.remove(option_key)
    else:
        selected.add(option_key)
    await bot.edit_message_reply_markup(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=section_options_kb(section_key, selected)
    )
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == "done")
async def done_selection(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in user_choices:
        user_choices[user_id] = {k: set() for k in SECTIONS.keys()}
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text="Вы вернулись в главное меню. Выберите категорию:",
        reply_markup=main_menu_kb()
    )
    await callback_query.answer()

@dp.message_handler(commands=["generate"])
async def generate_handler(message: types.Message):
    choices = user_choices.get(message.chat.id)
    if not choices:
        await message.answer("Сначала выберите параметры в меню через /start.")
        return
    prompt = build_final_prompt(choices)
    await message.answer(f"Генерирую изображение с промтом:\n\n{prompt}")
    # Тут вставь вызов генерации через Replicate по API с prompt
    # и отправку фото пользователю.
    # Для примера:
    # url, error = generate_image_via_replicate(prompt)
    # if url:
    #   await bot.send_photo(message.chat.id, url)
    # else:
    #   await message.answer(f"Ошибка генерации: {error}")

@dp.message_handler()
async def fallback(message: types.Message):
    await message.answer("Используйте /start для начала и /generate для генерации.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)