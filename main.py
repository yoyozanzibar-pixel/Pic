import asyncio
import logging
import os
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import BotCommand, BotCommandScopeDefault
from aiohttp import web

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = "8949058159:AAGd6WcDw8Z7rEQKS79oioazJpQtaygOLHw"  # Токен вашего бота
ADMIN_PASSWORD = "VAYG7YLNEM"    # Пароль для доступа в админку
ADMIN_ID = 1661921635            # <-- ЗАМЕНИТЕ НА СВОЙ ТЕЛЕГРАМ ID (только цифры)

# ==================== БАЗА ДАННЫХ ====================
def init_db():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            full_name TEXT,
            content_type TEXT,
            content_preview TEXT,
            file_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS banned_users (
            user_id INTEGER PRIMARY KEY
        )
    """)
    conn.commit()
    conn.close()

def log_activity(user_id: int, username: str, full_name: str, content_type: str, preview: str, file_id: str = None):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO user_activity (user_id, username, full_name, content_type, content_preview, file_id) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, username or "Без username", full_name, content_type, preview, file_id)
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
def get_main_keyboard(user_id: int):
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="ℹ️ О боте"))
    
    if user_id == ADMIN_ID:
        builder.add(types.KeyboardButton(text="🔐 Админка"))
        builder.adjust(1, 1)
    else:
        builder.adjust(1)
        
    return builder.as_markup(resize_keyboard=True)

def get_admin_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="📊 Сохранённые данные"))
    builder.add(types.KeyboardButton(text="⛔ Забанить"))
    builder.add(types.KeyboardButton(text="✅ Разбанить"))
    builder.add(types.KeyboardButton(text="🚪 ВЫКЛ Админка"))
    builder.add(types.KeyboardButton(text="⬅️ Назад"))
    builder.adjust(2, 2, 1)
    return builder.as_markup(resize_keyboard=True)

def get_user_media_inline_keyboard(user_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="📸 Фотографии", callback_data=f"get_media:{user_id}:photo")
    builder.button(text="🎥 Видео", callback_data=f"get_media:{user_id}:video")
    builder.button(text="🎤 Голосовые", callback_data=f"get_media:{user_id}:voice")
    builder.adjust(3)
    return builder.as_markup()

# ==================== БОТ И ДИСПАТЧЕР ====================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

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
    user_name = message.from_user.first_name or message.from_user.username or "друг"
    
    start_text = (
        f"Здравствуйте, {user_name}! 👋✨\n\n"
        "Спасибо большое, что выбрали именно нас! 🤍\n\n"
        "🔒 У нас всё абсолютно конфиденциально и надежно. "
        "В этом боте вы можете свободно хранить свои мысли, "
        "аудиосообщения и видео. Вы можете создавать, редактировать "
        "и удалять любые записи в любое время — всё под вашим полным контролем! 📝🎙️🎥\n\n"
        "ℹ️ Также вы можете узнать подробнее о боте через меню.\n\n"
        "👇 Выберите действие в меню ниже или просто отправьте мне данные для сохранения:"
    )
    await message.answer(start_text, parse_mode="Markdown", reply_markup=get_main_keyboard(message.from_user.id))

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

@dp.message(F.text == "🔐 Админка")
async def process_admin_button(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.set_state(AdminStates.waiting_for_password)
    await message.answer("Отправьте пароль администратора:")

@dp.message(AdminStates.is_admin, F.text == "✅ Админка")
async def process_return_to_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("Панель администратора:", reply_markup=get_admin_keyboard())

@dp.message(AdminStates.waiting_for_password)
async def process_password(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    if message.text == ADMIN_PASSWORD:
        await state.set_state(AdminStates.is_admin)
        await message.answer(
            "🔓 Доступ разрешён! Вы авторизованы как администратор.",
            reply_markup=get_admin_keyboard()
        )
    else:
        await message.answer("❌ Неверный пароль! Попробуйте ещё раз или нажмите /start для отмены.")

@dp.message(AdminStates.is_admin, F.text == "⬅️ Назад")
async def process_admin_back(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("Вы вернулись в главное меню. Админ-доступ сохранён.", reply_markup=get_main_keyboard(message.from_user.id))

@dp.message(F.text == "⬅️ Назад")
async def process_substate_back(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state in {AdminStates.waiting_for_ban_id.state, AdminStates.waiting_for_unban_id.state}:
        await state.set_state(AdminStates.is_admin)
        await message.answer("Панель администратора:", reply_markup=get_admin_keyboard())

@dp.message(AdminStates.is_admin, F.text == "🚪 ВЫКЛ Админка")
async def process_logout(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.clear()
    await message.answer("Вы вышли из админ-панели.", reply_markup=get_main_keyboard(message.from_user.id))

@dp.message(AdminStates.is_admin, F.text == "📊 Сохранённые данные")
async def process_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT user_id, username, full_name FROM user_activity")
    users = cursor.fetchall()

    if not users:
        await message.answer("📂 В базе данных пока нет сохранённых записей.")
        conn.close()
        return

    await message.answer(f"📊 **Всего пользователей в базе:** {len(users)}\nФормирую итоговые отчеты...")

    for user_id, username, full_name in users:
        cursor.execute(
            "SELECT content_type, COUNT(*) FROM user_activity WHERE user_id = ? GROUP BY content_type",
            (user_id,)
        )
        stats = dict(cursor.fetchall())

        cursor.execute(
            "SELECT content_type, content_preview, created_at FROM user_activity WHERE user_id = ? ORDER BY id DESC LIMIT 5",
            (user_id,)
        )
        recent_items = cursor.fetchall()

        text_count = stats.get("text", 0)
        photo_count = stats.get("photo", 0)
        video_count = stats.get("video", 0)
        voice_count = stats.get("voice", 0)
        other_count = sum(count for c_type, count in stats.items() if c_type not in ["text", "photo", "video", "voice"])

        report = (
            f"👤 **Пользователь:** {full_name} (@{username})\n"
            f"🆔 **ID:** `{user_id}`\n\n"
            f"📈 **Активность:**\n"
            f" 📝 Текстов: {text_count}\n"
            f" 🖼 Фото: {photo_count}\n"
            f" 🎥 Видео: {video_count}\n"
            f" 🎙 Голосовых: {voice_count}\n"
            f" 📦 Прочее: {other_count}\n\n"
            f"🕒 **Последние записи:**\n"
        )

        for c_type, preview, created_at in recent_items:
            report += f"• [{created_at}] ({c_type}): {preview}\n"

        await message.answer(
            report, 
            parse_mode="Markdown", 
            reply_markup=get_user_media_inline_keyboard(user_id)
        )
    conn.close()

@dp.callback_query(F.data.startswith("get_media:"))
async def process_get_media_callback(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("У вас нет прав.", show_alert=True)
        return
    _, target_user_id, media_type = callback.data.split(":")
    target_user_id = int(target_user_id)

    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT file_id, content_preview FROM user_activity WHERE user_id = ? AND content_type = ? AND file_id IS NOT NULL",
        (target_user_id, media_type)
    )
    media_records = cursor.fetchall()
    conn.close()

    if not media_records:
        await callback.answer("У этого пользователя нет сохраненных файлов данного типа.", show_alert=True)
        return

    await callback.answer("Отправляю файлы...")

    for file_id, caption in media_records:
        try:
            if media_type == "photo":
                await bot.send_photo(callback.from_user.id, photo=file_id, caption=caption)
            elif media_type == "video":
                await bot.send_video(callback.from_user.id, video=file_id, caption=caption)
            elif media_type == "voice":
                await bot.send_voice(callback.from_user.id, voice=file_id)
        except Exception as e:
            logging.error(f"Ошибка при отправке медиафайла: {e}")

@dp.message(AdminStates.is_admin, F.text == "⛔ Забанить")
async def ban_instruction(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.set_state(AdminStates.waiting_for_ban_id)
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="⬅️ Назад"))
    await message.answer("Отправьте Telegram ID пользователя, которого хотите забанить:", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(AdminStates.waiting_for_ban_id)
async def process_ban_id(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    if not message.text.isdigit():
        await message.answer("❌ ID должен состоять только из цифр. Попробуйте снова.")
        return
    user_id = int(message.text)
    ban_user(user_id)
    await state.set_state(AdminStates.is_admin)
    await message.answer(f"⛔ Пользователь с ID `{user_id}` успешно забанен!", parse_mode="Markdown", reply_markup=get_admin_keyboard())

@dp.message(AdminStates.is_admin, F.text == "✅ Разбанить")
async def unban_instruction(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.set_state(AdminStates.waiting_for_unban_id)
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="⬅️ Назад"))
    await message.answer("Отправьте Telegram ID пользователя, которого хотите разбанить:", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(AdminStates.waiting_for_unban_id)
async def process_unban_id(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    if not message.text.isdigit():
        await message.answer("❌ ID должен состоять только из цифр. Попробуйте снова.")
        return
    user_id = int(message.text)
    unban_user(user_id)
    await state.set_state(AdminStates.is_admin)
    await message.answer(f"✅ Пользователь с ID `{user_id}` успешно разбанен!", parse_mode="Markdown", reply_markup=get_admin_keyboard())

@dp.message()
async def handle_user_content(message: types.Message):
    user = message.from_user
    content_type = "unknown"
    preview = ""
    file_id = None

    if message.text:
        content_type = "text"
        preview = message.text[:50]
    elif message.photo:
        content_type = "photo"
        file_id = message.photo[-1].file_id
        preview = message.caption[:55] if message.caption else "[Фотография]"
    elif message.video:
        content_type = "video"
        file_id = message.video.file_id
        preview = message.caption[:50] if message.caption else "[Видео]"
    elif message.voice:
        content_type = "voice"
        file_id = message.voice.file_id
        preview = f"[Голосовое {message.voice.duration} сек.]"
    elif message.document:
        content_type = "document"
        file_id = message.document.file_id
        preview = f"[Документ: {message.document.file_name}]"

    log_activity(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
        content_type=content_type,
        preview=preview,
        file_id=file_id
    )

    await message.answer("Ваши данные успешно сохранены!")

# ==================== ВЕБ-СЕРВЕР ДЛЯ RENDER ====================
async def handle_web(request):
    return web.Response(text="Bot is running!")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle_web)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Веб-сервер запущен на порту {port}")

# ==================== ЗАПУСК ====================
async def main():
    logging.basicConfig(level=logging.INFO)
    init_db()
    
    await bot.set_my_commands([], scope=BotCommandScopeDefault())
    
    print("Бот успешно запущен!")
    
    await asyncio.gather(
        web_server(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    asyncio.run(main())
