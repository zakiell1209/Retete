from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
import os
import replicate
from dotenv import load_dotenv

load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

@dp.message(F.text)
async def handle_message(message: Message):
    await message.answer("Генерирую изображение, подождите...")

    prompt = message.text

    output = replicate.run(
        "aitechtree/nsfw-novel-generation",
        input={"prompt": prompt},
        api_token=os.getenv("REPLICATE_TOKEN")
    )

    if isinstance(output, list):
        image_url = output[0]
    else:
        image_url = output

    await message.answer_photo(photo=image_url)