from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from loader import db

category_cb = CallbackData('category', 'id', 'action')
razdel_cb = CallbackData('razdel', 'id', 'action')

def categories_markup(razdel_id):
    global category_cb

    markup = InlineKeyboardMarkup()
    for idx, title in db.fetchall('SELECT idx,title FROM categories WHERE tag = ?', (razdel_id,)):
        markup.add(InlineKeyboardButton(title,
                                        callback_data=category_cb.new(id=idx,
                                                                      action='view')))

    return markup

def razdel_markup(*args, **kwargs):
    global razdel_cb

    markup = InlineKeyboardMarkup()
    for idx, title in db.fetchall('''SELECT * FROM razdels'''):
        markup.add(InlineKeyboardButton(title,
                                        callback_data=razdel_cb.new(id=idx,
                                                                      action='view')))
    return markup