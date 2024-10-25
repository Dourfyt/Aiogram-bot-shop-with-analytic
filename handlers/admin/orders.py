from aiogram.types import Message, CallbackQuery
from loader import dp, db
from handlers.user.menu import orders
from filters import IsAdmin
from keyboards.inline.orders import *


@dp.message_handler(IsAdmin(), text=orders)
async def process_orders(message: Message):
    orders = db.fetchall('SELECT * FROM orders')

    if len(orders) == 0:
        await message.answer('У вас нет заказов.')
    else:
        await order_answer(message, orders)

@dp.callback_query_handler(IsAdmin(), order_cb.filter(action='delete'))
async def delete_order(query: CallbackQuery, callback_data: dict):
    db.query("DELETE FROM orders WHERE rowid = ?", (callback_data["id"],))
    await query.message.delete()


async def order_answer(message, orders):

    res = ''

    for order in orders:
        razdel = db.fetchone("SELECT title from razdels WHERE idx = ?", (order[6].split(' ')[0],))
        cid = order[0]
        products = order[3]
        date = order[4]
        zakaz = ''
        for title in order[3].split(' '):
            zakaz = zakaz + str(db.fetchone("SELECT title FROM products WHERE idx = ?", (str(title.strip().split("=")[0]),))[0])
            zakaz =  zakaz + " - " + str(title.strip().split("=")[1]) + "; "
        res = f'Заказ: <b>{zakaz}</b>\n\nТип заказа: <b>{razdel[0]}</b>\n\nПожелания: <b>{order[5]}</b>\n\n\n\n'

        await message.answer(res, reply_markup=delete_order_markup(cid,products,date))
