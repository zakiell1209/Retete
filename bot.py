import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Text
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils import executor
from dotenv import load_dotenv
import replicate
import asyncio

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Кнопки выбора стиля
style_kb = InlineKeyboardBuilder()
style_kb.button(text="Аниме", callback_data="style_anime")
style_kb.button(text="Реализм", callback_data="style_realism")
style_kb.button(text="Фэнтези", callback_data="style_fantasy")
style_kb.button(text="Видео (демо)", callback_data="generate_video")
style_kb.adjust(2)

# Переменная для хранения текущего стиля
user_style = {}

def generate_prompt(text: str, style: str) -> str:
    base_prompt = f"Генерировать {style} изображение с описанием: {text}"
    # Здесь можно улучшить парсер и промты, пока простой шаблон
    return base_prompt

@dp.message(commands=["start", "help"])
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я бот для генерации NSFW изображений.\n"
        "Напиши описание, а я сгенерирую картинку.\n"
        "Выбери стиль:",
        reply_markup=style_kb.as_markup()
    )

@dp.callback_query()
async def cb_handler(callback: types.CallbackQuery):
    data = callback.data
    user_id = callback.from_user.id

    if data.startswith("style_"):
        style = data.split("_")[1]
        user_style[user_id] = style
        await callback.message.answer(f"Выбран стиль: {style.capitalize()}. Теперь отправь описание для генерации.")
        await callback.answer()
    elif data == "generate_video":
        await callback.message.answer("Функция генерации видео пока в разработке.")
        await callback.answer()

@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    style = user_style.get(user_id, "реализм")

    prompt = generate_prompt(message.text, style)

    await message.answer("Генерирую изображение, подождите...")

    try:
        output = replicate.run(
            "aitechtree/nsfw-novel-generation",
            input={"prompt": prompt},
            api_token=REPLICATE_TOKEN
        )
        if isinstance(output, list):
            image_url = output[0]
        else:
            image_url = output
        await message.answer_photo(photo=image_url)
    except Exception as e:
        await message.answer(f"Ошибка генерации: {e}")

if __name__ == "__main__":
    executor.start_polling(dp)