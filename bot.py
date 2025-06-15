import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.utils.markdown import hbold
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
import replicate

BOT_TOKEN = os.getenv("BOT_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_TOKEN")

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("👋 Привет! Отправь описание изображения.")

@dp.message()
async def generate_image(message: Message):
    prompt = message.text
    await message.answer("🔄 Генерирую изображение по запросу...")

    try:
        output = replicate.run(
            "aitechtree/nsfw-novel-generation",
            input={"prompt": prompt},
            api_token=REPLICATE_TOKEN
        )
        image_url = output[0] if isinstance(output, list) else output
        await message.answer_photo(image_url)
    except Exception as e:
        await message.answer(f"⚠️ Ошибка генерации: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())