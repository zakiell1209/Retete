import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from fastapi import FastAPI, Request
import uvicorn

# Настройки из переменных окружения
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "supersecret")  # просто строка
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL", "https://your-url.onrender.com") + f"/webhook/{WEBHOOK_SECRET}"

# Создание бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
app = FastAPI()

# Обработка команды /start
@dp.message(F.text == "/start")
async def start_cmd(message: Message):
    await message.answer("Привет! Я бот с поддержкой webhook.")

# Добавь здесь генерацию через Replicate, если хочешь
# @dp.message(F.text.startswith("сгенерируй "))
# async def generate_image(message: Message):
#     prompt = message.text[10:]
#     await message.answer(f"Генерирую по описанию: {prompt} (реализация не вставлена)")

# Webhook обработчик
@app.post(f"/webhook/{WEBHOOK_SECRET}")
async def telegram_webhook(req: Request):
    body = await req.body()
    await bot.feed_webhook_update(body, req.headers)
    return "ok"

# Установка webhook при запуске
@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)
    print(f"Webhook установлен на {WEBHOOK_URL}")

# Удаление webhook при выключении
@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook()
    await bot.session.close()

# Запуск локального сервера (не нужен в Render)
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))