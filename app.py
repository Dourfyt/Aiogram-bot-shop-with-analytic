from datetime import datetime, timedelta
from aiogram import types
from aiogram.types import ReplyKeyboardMarkup
from aiogram.types import ReplyKeyboardRemove
from aiogram import executor
from logging import basicConfig, INFO

from data.config import ADMINS
from loader import dp, db, bot, session

import handlers

SESSION_TIMEOUT = 900

user_message = 'Пользователь'
admin_message = 'Админ'

def track_session(user_id):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if session.exists(f"session:{user_id}"):
        session.setex(f"session:{user_id}", SESSION_TIMEOUT, now)
    else:
        db.query("INSERT INTO visits (user_id, visit_time) VALUES (?,?)", (user_id, now))
        session.setex(f"session:{user_id}", SESSION_TIMEOUT, now)

@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    user = db.fetchone("SELECT * FROM users WHERE user_id = ?", (message.from_user.id,))
    track_session(message.from_user.id)
    if user:
        db.query("UPDATE users SET last_seen = ? WHERE user_id = ?", (datetime.now(), message.from_user.id))
        db.query("UPDATE users SET is_returning = ? WHERE user_id = ? AND last_seen > ?", (1, message.from_user.id, (datetime.now() - timedelta(days=31)).isoformat()))
    else:
        db.query("INSERT INTO users (user_id, first_seen, last_seen, is_returning) VALUES (?, ?, ?, 0)", 
                       (message.from_user.id, datetime.now(), datetime.now()))
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(user_message, admin_message)

    await message.answer('''Привет! 👋

🤖 Я бот-магазин по подаже товаров любой категории.

🛍️ Чтобы перейти в каталог и выбрать приглянувшиеся 
товары возпользуйтесь командой /menu.

❓ Возникли вопросы? Не проблема! Команда /sos поможет 
связаться с админами, которые постараются как можно быстрее откликнуться.
    ''', reply_markup=markup)


@dp.message_handler(text=admin_message)
async def admin_mode(message: types.Message):
    cid = message.chat.id
    if cid not in ADMINS:
        ADMINS.append(cid)

    await message.answer('Включен админский режим.',
                         reply_markup=ReplyKeyboardRemove())


@dp.message_handler(text=user_message)
async def user_mode(message: types.Message):
    cid = message.chat.id
    if cid in ADMINS:
        ADMINS.remove(cid)

    await message.answer('Включен пользовательский режим.',
                         reply_markup=ReplyKeyboardRemove())


async def on_startup(dp):
    basicConfig(level=INFO)
    db.create_tables()


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=False)
