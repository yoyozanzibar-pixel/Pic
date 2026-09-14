import os
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile

API_TOKEN = os.getenv("BOT_TOKEN")  # Или вставьте ваш токен строкой: "ВАШ_ТОКЕН"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Инициализация БД
def init_db():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            content_type TEXT,
            content TEXT
        )
    """)
    conn.commit()
    conn.close()

# Сохранение текстовых сообщений
@dp.message(lambda message: message.text and not message.text.startswith('/'))
async def save_text(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "без_ника"
    text = message.text

    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (user_id, username, content_type, content) VALUES (?, ?, ?, ?)",
        (user_id, username, "TEXT", text)
    )
    conn.commit()
    conn.close()

    await message.answer(f"Текст сохранен: {text}")

# Сохранение фото
@dp.message(lambda message: message.photo)
async def save_photo(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "без_ника"
    photo_id = message.photo[-1].file_id  # Берем фото лучшего качества

    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (user_id, username, content_type, content) VALUES (?, ?, ?, ?)",
        (user_id, username, "PHOTO", photo_id)
    )
    conn.commit()
    conn.close()

    await message.answer("Фото сохранено.")

# Вывод всех сохраненных сообщений и фото
@dp.message(Command("get_messages"))
async def get_messages(message: types.Message):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, content_type, content FROM messages")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await message.answer("Сохраненных сообщений пока нет.")
        return

    for user_id, username, content_type, content in rows:
        user_info = f"Пользователь: ID {user_id} (@{username})"
        
        if content_type == "TEXT":
            await message.answer(f"{user_info}\nТекст: {content}")
        elif content_type == "PHOTO":
            # Отправка фото прямо картинкой по file_id
            await message.answer_photo(photo=content, caption=f"{user_info}\nСохраненное фото")

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
