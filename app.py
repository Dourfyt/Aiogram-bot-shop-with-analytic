from datetime import datetime, timedelta
from aiogram import types
from aiogram.types import ReplyKeyboardMarkup
from aiogram.types import ReplyKeyboardRemove
from aiogram import executor
from logging import basicConfig, INFO
import configparser

from data.config import ADMINS
from loader import dp, db, bot, session
from utils.tasks.tasks import check_cart_sessions
from handlers.user.menu import user_menu

import random
import handlers

SESSION_TIMEOUT = 100

user_message = 'Пользователь'
admin_message = 'Админ'

def track_session(user_id):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if session.exists(f"session:{user_id}"):
        session.setex(f"session:{user_id}", SESSION_TIMEOUT, session.get(f"session:{user_id}"))
    else:
        session.setex(f"session:{user_id}", SESSION_TIMEOUT, int(str(random.getrandbits(128))[:16]))
        db.query("INSERT INTO visits (user_id, visit_time) VALUES (?,?)", (user_id, now))
        db.query("INSERT INTO sessions (session_key, pages_visited) VALUES (?,?)",(session.get(f"session:{user_id}"),0,))
        check_cart_sessions.apply_async((user_id,), countdown=1 * 60)

@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    if message.from_user.id in ADMINS:
        ADMINS.discard(message.from_user.id)
    user = db.fetchone("SELECT * FROM users WHERE user_id = ?", (message.from_user.id,))
    if user:
        db.query("UPDATE users SET last_seen = ? WHERE user_id = ?", (datetime.now(), message.from_user.id))
        db.query("UPDATE users SET is_returning = ? WHERE user_id = ? AND last_seen > ?", (1, message.from_user.id, (datetime.now() - timedelta(days=31)).isoformat()))
    else:
        db.query("INSERT INTO users (user_id, first_seen, last_seen, is_returning) VALUES (?, ?, ?, 0)", 
                       (message.from_user.id, datetime.now(), datetime.now()))
    track_session(message.from_user.id)
    await message.answer('''Страховой бот приветствует Вас!
    ''')
    await user_menu(message)



async def on_startup(dp):
    basicConfig(level=INFO)
    db.create_tables()


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=False)
