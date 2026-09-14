import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = "8949058159:AAGd6WcDw8Z7rEQKS79oioazJpQtaygOLHw"  # Вставьте сюда токен вашего бота
ADMIN_PASSWORD = "VAYG7YLNEM"    # Пароль для доступа в админку

# ==================== БАЗА ДАННЫХ ====================
def init_db():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    # Таблица активности пользователей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            full_name TEXT,
            content_type TEXT,
            content_preview TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Таблица забаненных пользователей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS banned_users (
            user_id INTEGER PRIMARY KEY
        )
    """)
    conn.commit()
    conn.close()

def log_activity(user_id: int, username: str, full_name: str, content_type: str, preview: str):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO user_activity (user_id, username, full_name, content_type, content_preview) VALUES (?, ?, ?, ?, ?)",
        (user_id, username or "Без username", full_name, content_type, preview)
    )
    conn.commit()
    conn.close()

def is_banned(user_id: int) -> bool:
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM banned_users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def ban_user(user_id: int):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO banned_users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def unban_user(user_id: int):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM banned_users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# ==================== FSM (СОСТОЯНИЯ) ====================
class AdminStates(StatesGroup):
    waiting_for_password = State()
    is_admin = State()
    waiting_for_ban_id = State()
    waiting_for_unban_id = State()

# ==================== КЛАВИАТУРЫ ====================
def get_main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="☁️ Удалить из облака"))
    builder.add(types.KeyboardButton(text="ℹ️ О боте"))
    builder.add(types.KeyboardButton(text="🔐 Админка"))
    builder.adjust(2, 1)
    return builder.as_markup(resize_keyboard=True)

def get_admin_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="📊 Сохранённые данные"))
    builder.add(types.KeyboardButton(text="⛔ Забанить (Инструкция)"))
    builder.add(types.KeyboardButton(text="✅ Разбанить (Инструкция)"))
    builder.add(types.KeyboardButton(text="🚪 Выйти из админки"))
    builder.adjust(2, 2)
    return builder.as_markup(resize_keyboard=True)

# ==================== БОТ И ДИСПАТЧЕР ====================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Middleware для проверки бана
@dp.message.outer_middleware()
async def check_ban_middleware(handler, event: types.Message, data):
    if event.from_user and is_banned(event.from_user.id):
        await event.answer("⛔ Вы забанены и не можете использовать этого бота.")
        return
    return await handler(event, data)

# ==================== ОБРАБОТЧИКИ ====================

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Привет! Выберите действие в меню ниже или отправьте мне данные для сохранения.",
        reply_markup=get_main_keyboard()
    )

# --- Пользовательская кнопка "ℹ️ О боте" ---
@dp.message(F.text == "ℹ️ О боте")
async def process_about_bot(message: types.Message):
    about_text = (
        "🤖 **О нашем сервисе**\n\n"
        "Мы успешно работаем и обеспечиваем стабильный сервис с **24 сентября 2021 года**.\n\n"
        "🛡 **Безопасность и надежность:**\n"
        "— Все данные передаются по защищенным протоколам шифрования.\n"
        "— Полная конфиденциальность и отсутствие передачи данных третьим лицам.\n"
        "— Многолетний стаж работы и тысячи доверенных операций.\n\n"
        "Спасибо, что выбираете нас!"
    )
    await message.answer(about_text, parse_mode="Markdown")

# --- Пользовательская кнопка "☁️ Удалить из облака" ---
@dp.message(F.text == "☁️ Удалить из облака")
async def process_fake_cloud_delete(message: types.Message):
    # Имитация работы с облачным хранилищем
    status_msg = await message.answer("🔄 Подключение к облачному хранилищу...")
    await asyncio.sleep(1)
    
    await status_msg.edit_text("⏳ Синхронизация и очистка облачных данных...")
    await asyncio.sleep(1.5)
    
    await status_msg.edit_text("✅ Все данные успешно и безвозвратно удалены из облака!")
    await asyncio.sleep(1.5)

    # Реальное поверхностное удаление истории сообщений из чата
    current_msg_id = message.message_id
    
    # Очищаем последние сообщения (до 20 штук назад)
    for msg_id in range(current_msg_id + 1, current_msg_id - 25, -1):
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
        except Exception:
            pass

# --- 1. Главная кнопка "🔐 Админка" ---
@dp.message(F.text == "🔐 Админка")
async def process_admin_button(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == AdminStates.is_admin.state:
        await message.answer("Вы уже находитесь в режиме администратора.", reply_markup=get_admin_keyboard())
    else:
        await state.set_state(AdminStates.waiting_for_password)
        await message.answer("Отправьте пароль администратора:")

# --- 2. Проверка пароля ---
@dp.message(AdminStates.waiting_for_password)
async def process_password(message: types.Message, state: FSMContext):
    if message.text == ADMIN_PASSWORD:
        await state.set_state(AdminStates.is_admin)
        await message.answer(
            "🔓 Доступ разрешён! Вы авторизованы как администратор.",
            reply_markup=get_admin_keyboard()
        )
    else:
        await message.answer("❌ Неверный пароль! Попробуйте ещё раз или нажмите /start для отмены.")

# --- 3. Выход из админки ---
@dp.message(AdminStates.is_admin, F.text == "🚪 Выйти из админки")
async def process_logout(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Вы вышли из админ-панели.", reply_markup=get_main_keyboard())

# --- 4. Группированная статистика ---
@dp.message(AdminStates.is_admin, F.text == "📊 Сохранённые данные")
async def process_stats(message: types.Message):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()

    # Получаем список уникальных пользователей
    cursor.execute("SELECT DISTINCT user_id, username, full_name FROM user_activity")
    users = cursor.fetchall()

    if not users:
        await message.answer("📂 В базе данных пока нет сохранённых записей.")
        conn.close()
        return

    await message.answer(f"📊 **Всего пользователей в базе:** {len(users)}\nФормирую итоговые отчеты...")

    for user_id, username, full_name in users:
        # Считаем количество контента по типам
        cursor.execute(
            "SELECT content_type, COUNT(*) FROM user_activity WHERE user_id = ? GROUP BY content_type",
            (user_id,)
        )
        stats = dict(cursor.fetchall())

        # Получаем 5 последних записей пользователя
        cursor.execute(
            "SELECT content_type, content_preview, created_at FROM user_activity WHERE user_id = ? ORDER BY id DESC LIMIT 5",
            (user_id,)
        )
        recent_items = cursor.fetchall()

        # Формируем текст сообщения
        text_count = stats.get("text", 0)
        photo_count = stats.get("photo", 0)
        voice_count = stats.get("voice", 0)
        other_count = sum(count for c_type, count in stats.items() if c_type not in ["text", "photo", "voice"])

        report = (
            f"👤 **Пользователь:** {full_name} (@{username})\n"
            f"🆔 **ID:** `{user_id}`\n\n"
            f"📈 **Активность:**\n"
            f" 📝 Текстов: {text_count}\n"
            f" 🖼 Фото: {photo_count}\n"
            f" 🎙 Голосовых: {voice_count}\n"
            f" 📦 Прочее: {other_count}\n\n"
            f"🕒 **Последние записи:**\n"
        )

        for c_type, preview, created_at in recent_items:
            report += f"• [{created_at}] ({c_type}): {preview}\n"

        await message.answer(report, parse_mode="Markdown")

    conn.close()

# --- 5. Бан и разбан ---
@dp.message(AdminStates.is_admin, F.text == "⛔ Забанить (Инструкция)")
async def ban_instruction(message: types.Message, state: FSMContext):
    await state.set_state(AdminStates.waiting_for_ban_id)
    await message.answer("Отправьте Telegram ID пользователя, которого хотите забанить:")

@dp.message(AdminStates.waiting_for_ban_id)
async def process_ban_id(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ ID должен состоять только из цифр. Попробуйте снова.")
        return
    user_id = int(message.text)
    ban_user(user_id)
    await state.set_state(AdminStates.is_admin)
    await message.answer(f"⛔ Пользователь с ID `{user_id}` успешно забанен!", parse_mode="Markdown")

@dp.message(AdminStates.is_admin, F.text == "✅ Разбанить (Инструкция)")
async def unban_instruction(message: types.Message, state: FSMContext):
    await state.set_state(AdminStates.waiting_for_unban_id)
    await message.answer("Отправьте Telegram ID пользователя, которого хотите разбанить:")

@dp.message(AdminStates.waiting_for_unban_id)
async def process_unban_id(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ ID должен состоять только из цифр. Попробуйте снова.")
        return
    user_id = int(message.text)
    unban_user(user_id)
    await state.set_state(AdminStates.is_admin)
    await message.answer(f"✅ Пользователь с ID `{user_id}` успешно разбанен!", parse_mode="Markdown")

# --- 6. Сохранение пользовательского контента ---
@dp.message()
async def handle_user_content(message: types.Message):
    user = message.from_user
    content_type = "unknown"
    preview = ""

    if message.text:
        content_type = "text"
        preview = message.text[:50]
    elif message.photo:
        content_type = "photo"
        preview = message.caption[:50] if message.caption else "[Фотография]"
    elif message.voice:
        content_type = "voice"
        preview = f"[Голосовое {message.voice.duration} сек.]"
    elif message.document:
        content_type = "document"
        preview = f"[Документ: {message.document.file_name}]"

    log_activity(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
        content_type=content_type,
        preview=preview
    )

    await message.answer("Ваши данные успешно сохранены!")

# ==================== ЗАПУСК ====================
async def main():
    logging.basicConfig(level=logging.INFO)
    init_db()
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
