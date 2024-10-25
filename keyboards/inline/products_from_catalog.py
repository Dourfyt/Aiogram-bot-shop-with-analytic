from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from loader import db

product_cb = CallbackData('product', 'id', 'action')
files_cb = CallbackData("product",'id', "action")

def product_markup(idx='', price=0):
    global product_cb

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(f'Добавить в корзину - {price}₽',
                                    callback_data=product_cb.new(id=idx,
                                                                 action='add')))
    files = db.fetchone('''SELECT files FROM products WHERE idx = ?''', (idx,))[0]
    if files:
        markup.add(InlineKeyboardButton(f'Показать файлы',
                                        callback_data=product_cb.new(id=idx,
                                                                    action='show')))

    return markup

def files_markup(idx=''):
    global files_cb

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(f'Показать файлы',
                                    callback_data=files_cb.new(id=idx,
                                                                 action='show')))

    return markup

def confirm_files_markup():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(f'Дальше',
                                    callback_data='confirm_files'))

    return markup
