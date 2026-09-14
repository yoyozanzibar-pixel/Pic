import os
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command

API_TOKEN = "8949058159:AAG6Q0J4_RhvYpns4ipVAEsBThFe4GzKudE"
ADMIN_ID = 1661921635  # Ваш ID администратора

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

# Обработчик команды /start
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    username = message.from_user.username
    if username:
        user_display = f"@{username}"
    else:
        user_display = message.from_user.first_name or "друг"

    start_text = (
        f"✨ **Здравствуйте, {user_display}!** ✨\n\n"
        f"Рады видеть вас в нашем боте! 📝🔥\n\n"
        f"Здесь вы можете удобно и надежно сохранять:\n"
        f"📸 **Фотографии** и памятные кадры\n"
        f"💬 **Тексты**, важные заметки и записи\n"
        f"💡 **Свои мысли**, идеи и вдохновение\n\n"
        f"⭐ Мы работаем абсолютно бесплатно — **без премиумов и без звёздочек ⭐ в Telegram**!\n\n"
        f"Просто отправьте сюда текст или фото, и всё автоматически сохранится 🚀"
    )

    await message.answer(start_text, parse_mode="Markdown")

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
    photo_id = message.photo[-1].file_id

    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (user_id, username, content_type, content) VALUES (?, ?, ?, ?)",
        (user_id, username, "PHOTO", photo_id)
    )
    conn.commit()
    conn.close()

    await message.answer("Фото сохранено.")

# Вывод всех сохраненных сообщений только для администратора
@dp.message(Command("get_messages"))
async def get_messages(message: types.Message):
    # Проверка доступа
    if message.from_user.id != ADMIN_ID:
        await message.answer("У вас нет доступа к этой команде.")
        return

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
            await message.answer_photo(photo=content, caption=f"{user_info}\nСохраненное фото")

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
