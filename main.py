import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
TOKEN = "8840599388:AAGzGYdpMz3AriFy9v-QU6X9yrtWnak1C_bQ"
DB_NAME = "bot_data.db"
logging.basicConfig(level=loggin g.INFO)
bot = Bot(token=TOKEN)

dp = Dispatcher()
definit_db):
conn =
sqlite3.connect(DB_NAME)
cursor = conn.cursor()
cursor.execute(
'''''CREATE TABLE IF NOT
EXISTS messages
(id INTEGER PRIMARY
KEY AUTOINCREMENT,
user_id INTEGER,
content_type TEXT,
con
t_ text TEXT''''

)
conn.commit()
conn.close()
def save_message(user_id, content_type, content_text):
conn =
sqlite3.connect(DB_NAME)
cursor = conn.cursor()
cursor.execute("INSERT INTO messages
(user_id, content_type,
content_text) VALUES (?, ?, ?)",
(user_id, content_type,
content_text),
)
conn.commit()
conn.close()
@dp.message(Command('start")
)
async def cmd _start(message:
types.Message):
await message.answer ("Привет! Отправь мне текст, фото или видео, и я сохраню их."
)
@dp.message()
async det
save_content(message: types.Message):
user_id = message.from_user.id
content_type =
message.content_type
content_text = None
if message.text:
content_text = message.text

save_message(user_id,
content_type, content_text)
await
message.answer(f"Tекст
сохранен: (content_text)")
elif message.photo:
content_text = f"Фото (ID:
{message.photo[-1].file_id})"
save_message(user_id,
content_type, content_text)
await message.answer ("Фото
сохранено.")
elif message.video:
content_text = f"Видео (ID: (message.video.file_id})"
save_message(user_id,
content_type, content_text)
await
message.answer('Видео
сохранено.")
else:
await message.answer ("Этот
тип контента не поддерживается.")
async def main ():
init_db(
await dp.start_polling(bot)

if__name__=="_main_.":
asyncio.run(main())
