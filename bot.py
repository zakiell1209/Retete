import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
import aiohttp
import os

logging.basicConfig(level=logging.INFO)

API_TOKEN = os.getenv("TELEGRAM_TOKEN")  # Установите токен в переменные окружения
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

HEADERS = {
    "Authorization": f"Token {REPLICATE_API_TOKEN}"
}

# Основной стиль — anime
DEFAULT_MODEL = "aitechtree/nsfw-novel-generation"

# Категории и теги с промтами
CATEGORIES = {
    "игрушки": {
        "anal_beads": "anal beads in the anus, NSFW, high detail",
        "anal_stretcher": "anal stretcher inserted in the anus, highly detailed NSFW",
        "huge_dildo": "huge dildo inserted, ultra realistic NSFW",
        "horse_dildo": "large horse dildo inserted deeply, hyper detailed NSFW",
        "long_dildo": ("dildo entering the anus and exiting through the mouth, "
                       "visible inside organs as bulges on stomach, very detailed, NSFW"),
    },
    "тело": {
        "cum": "fresh sperm splattered on skin and face, realistic texture, NSFW",
        "stomach_bulge": ("swollen belly from large dildo or anal beads inside, "
                          "highly realistic, NSFW"),
    },
    "тату": {
        "succubus_tattoo": ("small heart-shaped tattoo in the style of succubus, "
                           "located on the skin above the womb area of a female, very detailed"),
    },
    "одежда": {
        "cow_costume": ("female wearing stockings with cow pattern, with cow horns and tail, "
                        "no actual cow or full costume, NSFW"),
        "bikini_tan_lines": ("tan lines on body from wearing bikini, no bikini itself, "
                             "visible vagina, anus and nipples, realistic skin, NSFW"),
    },
    "отверстия": {
        "open_anus": "open anus, NSFW, detailed",
        "open_vagina": "open vagina, NSFW, detailed",
        "open_anus_and_vagina": "open anus and vagina both visible, NSFW, very detailed",
    }
}

# Кнопки категорий
category_buttons = {
    "игрушки": InlineKeyboardButton("Игрушки", callback_data="cat_игрушки"),
    "тело": InlineKeyboardButton("Тело", callback_data="cat_тело"),
    "тату": InlineKeyboardButton("Тату", callback_data="cat_тату"),
    "одежда": InlineKeyboardButton("Одежда", callback_data="cat_одежда"),
    "отверстия": InlineKeyboardButton("Отверстия", callback_data="cat_отверстия"),
}

# Хранение сессий пользователя: выбранные теги
user_sessions = {}

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

def build_tags_keyboard(user_id: int, category: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    tags = CATEGORIES[category]
    selected = user_sessions.get(user_id, set())
    buttons = []
    for tag, prompt in tags.items():
        mark = "✅ " if tag in selected else ""
        buttons.append(InlineKeyboardButton(mark + tag, callback_data=f"tag_{tag}"))
    kb.add(*buttons)
    kb.add(InlineKeyboardButton("Готово", callback_data="done"))
    kb.add(*category_buttons.values())
    return kb

@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    user_sessions[message.from_user.id] = set()
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(*category_buttons.values())
    await message.answer("Выберите категорию тегов:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("cat_"))
async def process_category(call: types.CallbackQuery):
    category = call.data[4:]
    if category not in CATEGORIES:
        await call.answer("Неизвестная категория")
        return
    kb = build_tags_keyboard(call.from_user.id, category)
    await call.message.edit_text(f"Выбрана категория: {category}\nВыберите теги:", reply_markup=kb)
    await call.answer()

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("tag_"))
async def process_tag(call: types.CallbackQuery):
    tag = call.data[4:]
    # Определяем категорию для выбранного тега
    found_category = None
    for cat, tags in CATEGORIES.items():
        if tag in tags:
            found_category = cat
            break
    if found_category is None:
        await call.answer("Неизвестный тег")
        return
    user_id = call.from_user.id
    selected = user_sessions.setdefault(user_id, set())
    if tag in selected:
        selected.remove(tag)
    else:
        selected.add(tag)
    kb = build_tags_keyboard(user_id, found_category)
    await call.message.edit_reply_markup(reply_markup=kb)
    await call.answer()

@dp.callback_query_handler(lambda c: c.data == "done")
async def process_done(call: types.CallbackQuery):
    user_id = call.from_user.id
    tags = user_sessions.get(user_id, set())
    if not tags:
        await call.answer("Выберите хотя бы один тег")
        return
    # Формируем промт на основе выбранных тегов
    prompt_parts = []
    for cat_tags in CATEGORIES.values():
        for tag in tags:
            if tag in cat_tags:
                prompt_parts.append(cat_tags[tag])
    prompt = ", ".join(prompt_parts) + ", anime style, high detail, nsfw"

    await call.message.answer("Генерируется изображение, подождите...")
    await call.answer()

    # Вызов Replicate API
    image_url = await generate_image(prompt)
    if image_url:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("Начать заново", callback_data="restart"))
        kb.add(InlineKeyboardButton("Выбрать теги", callback_data="choose_tags"))
        await call.message.answer_photo(photo=image_url, reply_markup=kb)
    else:
        await call.message.answer("Ошибка генерации изображения.")

@dp.callback_query_handler(lambda c: c.data == "restart")
async def process_restart(call: types.CallbackQuery):
    user_sessions[call.from_user.id] = set()
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(*category_buttons.values())
    await call.message.answer("Выберите категорию тегов:", reply_markup=kb)
    await call.answer()

@dp.callback_query_handler(lambda c: c.data == "choose_tags")
async def process_choose_tags(call: types.CallbackQuery):
    user_id = call.from_user.id
    # Если сессия пуста — создаём
    if user_id not in user_sessions:
        user_sessions[user_id] = set()
    # По умолчанию открываем категорию игрушки
    kb = build_tags_keyboard(user_id, "игрушки")
    await call.message.answer("Выберите категорию и теги:", reply_markup=kb)
    await call.answer()

async def generate_image(prompt: str) -> str | None:
    # Отправляем запрос в Replicate, запускаем модель
    # Модель: aitechtree/nsfw-novel-generation
    url = "https://api.replicate.com/v1/predictions"
    json_data = {
        "version": "c01db1547ecf3f88358dd1f5eaff4591180d7ac5e98a85be9e8e7af0ebff9f1d",
        "input": {"prompt": prompt}
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=HEADERS, json=json_data) as resp:
            if resp.status != 201:
                logging.error(f"Replicate API error: {resp.status} {await resp.text()}")
                return None
            data = await resp.json()
            prediction_url = data["urls"]["get"]
            # Ждём завершения генерации
            while True:
                async with session.get(prediction_url, headers=HEADERS) as r:
                    result = await r.json()
                    status = result.get("status")
                    if status == "succeeded":
                        output = result.get("output")
                        if isinstance(output, list) and len(output) > 0:
                            return output[0]
                        else:
                            return None
                    elif status in ("failed", "canceled"):
                        logging.error(f"Generation failed: {result}")
                        return None
                    await asyncio.sleep(2)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)