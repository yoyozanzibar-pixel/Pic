
if __name__ == "__main__": app.run()

import logging from aiogram import Bot, Dispatcher, types from aiogram.filters import Command
TOKEN = "8840599388:AAFbCBD6KmfzTs_XvXfdfhmMMwfDxp7SXYo" logging.basicConfig(level=logging.INFO) bot = Bot(token=8840599388:AAFbCBD6KmfzTs_XvXfdfhmMMwfDxp7SXYo) dp = Dispatcher()
@dp.message(Command("start")) async def cmd_start(message: types.Message): await message.answer("Привет! Отправь мне текст, фото или видео, и я сохраню их.")
@dp.message() async def save_content(message: types.Message): if message.text: await message.answer(f"Текст сохранен: {message.text}") elif message.photo: await message.answer("Фото сохранено.") elif message.video: await message.answer("Видео сохранено.")
async def main(): await dp.start_polling(bot)
if name == "main": import asyncio asyncio.run(main())
