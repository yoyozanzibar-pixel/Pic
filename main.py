import os
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, BotCommand

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
    # Таблица для сообщений
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            content_type TEXT,
            content TEXT
        )
    """)
    # Таблица для банов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS banned_users (
            user_id INTEGER PRIMARY KEY
        )
    """)
    conn.commit()
    conn.close()

# Проверка: забанен ли пользователь
def is_banned(user_id: int) -> bool:
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM banned_users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row is not None

# Inline-кнопка под сообщениями
def get_delete_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="☁️ Удалить из облака", callback_data="delete_chat_msg")]
    ])

# Reply-клавиатура (кнопки возле поля ввода)
def get_main_keyboard(user_id: int):
    buttons = [
        [KeyboardButton(text="🧹 Очистить облако"), KeyboardButton(text="ℹ️ О боте")]
    ]
    if user_id in ADMIN_IDS:
        buttons.append([KeyboardButton(text="🔐 Сохранённые данные")])
        
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# Регистрация стандартных команд Telegram
async def setup_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Перезапустить бота / Показать меню"),
        BotCommand(command="clear", description="Очистить облако"),
        BotCommand(command="info", description="О боте")
    ]
    await bot.set_my_commands(commands)

# Удаление сообщения по Inline-кнопке (в БД всё остается)
@dp.callback_query(F.data == "delete_chat_msg")
async def process_delete_chat_msg(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.answer("Удалено из вашего облака!")

# Команда /start
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    if is_banned(message.from_user.id):
        await message.answer("⛔ Вы заблокированы и не можете использовать бота.")
        return

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
    await message.answer(start_text, parse_mode="Markdown", reply_markup=get_main_keyboard(user_id))

# Команда /admin или сообщение "admin commands"
@dp.message(Command("admin"))
@dp.message(F.text.lower() == "admin commands")
async def admin_commands_handler(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("У вас нет доступа к командам администратора.")
        return

    admin_text = (
        "⚙️ **Панель администратора**\n\n"
        "Доступные команды:\n"
        "▫️ `/get_messages` — Посмотреть все сохранённые данные пользователей\n"
        "▫️ `/ban <ID>` — Заблокировать пользователя (например: `/ban 123456789`)\n"
        "▫️ `/unban <ID>` — Разблокировать пользователя (например: `/unban 123456789`)\n"
        "▫️ `/admin` — Показать это меню"
    )
    await message.answer(admin_text, parse_mode="Markdown")

# Команда /ban ID
@dp.message(Command("ban"))
async def ban_user_handler(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("⚠️ Укажите ID пользователя. Пример: `/ban 123456789`", parse_mode="Markdown")
        return

    target_id = int(args[1])
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO banned_users (user_id) VALUES (?)", (target_id,))
    conn.commit()
    conn.close()

    await message.answer(f"✅ Пользователь с ID `{target_id}` успешно заблокирован.", parse_mode="Markdown")

# Команда /unban ID
@dp.message(Command("unban"))
async def unban_user_handler(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("⚠️ Укажите ID пользователя. Пример: `/unban 123456789`", parse_mode="Markdown")
        return

    target_id = int(args[1])
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM banned_users WHERE user_id = ?", (target_id,))
    conn.commit()
    conn.close()

    await message.answer(f"✅ Пользователь с ID `{target_id}` успешно разблокирован.", parse_mode="Markdown")

# Кнопка "🧹 Очистить облако" или команда /clear
@dp.message(F.text == "🧹 Очистить облако")
@dp.message(Command("clear"))
async def clear_chat_handler(message: types.Message):
    if is_banned(message.from_user.id):
        return
    await message.delete()
    sent_msg = await message.answer("🧹 Ваше облако очищено.")
    await asyncio.sleep(3)
    await sent_msg.delete()

# Кнопка "ℹ️ О боте" или команда /info
@dp.message(F.text == "ℹ️ О боте")
@dp.message(Command("info"))
async def info_handler(message: types.Message):
    if is_banned(message.from_user.id):
        return
    info_text = (
        "🤖 **Облачный накопитель**\n\n"
        "Отправляйте любые файлы, тексты или медиа в этот чат — всё будет надежно сохранено!"
    )
    await message.answer(info_text, parse_mode="Markdown")

# Сохранение в SQLite
def save_to_db(user_id: int, username: str, content_type: str, content: str):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (user_id, username, content_type, content) VALUES (?, ?, ?, ?)",
        (user_id, username or "без_ника", content_type, content)
    )
    conn.commit()
    conn.close()

# Текст
@dp.message(lambda m: m.text and not m.text.startswith('/') and m.text not in ["🧹 Очистить облако", "ℹ️ О боте", "🔐 Сохранённые данные", "admin commands"])
async def save_text(message: types.Message):
    if is_banned(message.from_user.id):
        await message.answer("⛔ Вы заблокированы.")
        return
    save_to_db(message.from_user.id, message.from_user.username, "TEXT", message.text)
    await message.answer(f"Текст сохранен: {message.text}", reply_markup=get_delete_keyboard())

# Фото
@dp.message(F.photo)
async def save_photo(message: types.Message):
    if is_banned(message.from_user.id):
        await message.answer("⛔ Вы заблокированы.")
        return
    save_to_db(message.from_user.id, message.from_user.username, "PHOTO", message.photo[-1].file_id)
    await message.answer("Фото сохранено.", reply_markup=get_delete_keyboard())

# Голосовые
@dp.message(F.voice)
async def save_voice(message: types.Message):
    if is_banned(message.from_user.id):
        await message.answer("⛔ Вы заблокированы.")
        return
    save_to_db(message.from_user.id, message.from_user.username, "VOICE", message.voice.file_id)
    await message.answer("Голосовое сообщение сохранено 🎙", reply_markup=get_delete_keyboard())

# Кружочки
@dp.message(F.video_note)
async def save_video_note(message: types.Message):
    if is_banned(message.from_user.id):
        await message.answer("⛔ Вы заблокированы.")
        return
    save_to_db(message.from_user.id, message.from_user.username, "VIDEO_NOTE", message.video_note.file_id)
    await message.answer("Видеосообщение сохранено 🎥", reply_markup=get_delete_keyboard())

# Документы
@dp.message(F.document)
async def save_document(message: types.Message):
    if is_banned(message.from_user.id):
        await message.answer("⛔ Вы заблокированы.")
        return
    save_to_db(message.from_user.id, message.from_user.username, "DOCUMENT", message.document.file_id)
    await message.answer(f"Файл '{message.document.file_name}' сохранен 📁", reply_markup=get_delete_keyboard())

# Просмотр базы для админа
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
    await setup_bot_commands(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
