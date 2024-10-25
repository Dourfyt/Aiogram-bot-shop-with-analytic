from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from loader import db
from datetime import datetime

order_cb = CallbackData('order', 'id', 'action')

def delete_order_markup(cid, products,date):
    global order_cb
    markup = InlineKeyboardMarkup()
    for rowid in db.fetchone('SELECT rowid FROM orders WHERE cid = ? and products = ? and order_time = ?', (int(cid), str(products), date)):
        markup.add(InlineKeyboardButton("Удалить заказ",
                                        callback_data=order_cb.new(id=rowid,
                                                                      action='delete')))
        print(rowid)
    return markup

