from datetime import datetime, timedelta

from aiogram.dispatcher import FSMContext
import redis
from filters import IsUser
from aiogram.types import Message
from aiogram.types import CallbackQuery
from aiogram.types.chat import ChatActions

from keyboards.inline.categories import categories_markup, razdel_markup
from .menu import catalog
from loader import dp, db, bot
from keyboards.inline.categories import category_cb, razdel_cb
from keyboards.inline.products_from_catalog import product_markup
from keyboards.inline.products_from_catalog import product_cb, files_cb

session = redis.StrictRedis(host='redis-db', port=6379, db=0, decode_responses=True)

@dp.callback_query_handler(IsUser(), razdel_cb.filter(action="view"))
async def process_catalog(query: CallbackQuery, callback_data: dict, state: FSMContext):
    async with state.proxy() as data:
        data["razdel"] = callback_data["id"]
    await query.message.delete()
    await query.message.answer('Выберите категорию, чтобы вывести список услуг:',
                         reply_markup=categories_markup(callback_data["id"]))

@dp.message_handler(IsUser(), text=catalog)
async def razdel_callback_handler(message: Message):
    razdels = db.fetchall('''SELECT razdels.idx,razdels.title FROM razdels''')
    await message.delete()
    await message.answer('Пожалуйста, выберите страховое направление',
                         reply_markup=razdel_markup(razdels))

@dp.callback_query_handler(IsUser(), category_cb.filter(action='view'))
async def category_callback_handler(query: CallbackQuery, callback_data: dict):
    db.query("INSERT INTO categories_views (user_id,categorie_id,view_time) VALUES (?,?,?)",(query.from_user.id, callback_data['id'], (datetime.now()-timedelta(days=4)).isoformat(),))
    if session.exists(f"session:{query.from_user.id}"):
        try:
            pages_visited = db.fetchone("SELECT pages_visited FROM sessions WHERE session_key = ?",(session.get(f"session:{query.from_user.id}"),))[0]
        except Exception as e:
            pages_visited = 0
        db.query("UPDATE sessions SET pages_visited = ? WHERE session_key = ?",(pages_visited+1,session.get(f"session:{query.from_user.id}"),))
    products = db.fetchall('''SELECT * FROM products WHERE tag = ?
    AND idx NOT IN (SELECT idx FROM cart WHERE cid = ?)''',
                           (callback_data['id'], query.message.chat.id))
    await query.message.delete()
    await query.message.answer('Для того, чтобы сделать заказ: выберите страховой продукт, положите в корзину и нажмите отправить. Страховой агент свяжется с Вами')
    await show_products(query.message, products)


#ПОКАЗАТЬ ТОВАРЫ КАТЕГОРИИ
async def show_products(m, products):

    if len(products) == 0:

        await m.answer('Здесь ничего нет 😢')

    else:

        await bot.send_chat_action(m.chat.id, ChatActions.TYPING)

        for idx, title, body, image, price, _, files in products:

            markup = product_markup(idx, price)
            text = f'<b>{title}</b>\n\n{body}'
            if image != "":
                await m.answer_photo(photo=image,
                                    caption=text,
                                    reply_markup=markup)
            else:
                await m.answer(text, reply_markup=markup) 

#ДОБАВИТЬ ПРОДУКТ В КОРЗИНУ
@dp.callback_query_handler(IsUser(), product_cb.filter(action='add'))
async def add_product_callback_handler(query: CallbackQuery,
                                       callback_data: dict, state: FSMContext):
    async with state.proxy() as data:
        razdel = data.get('razdel')
    await query.message.edit_reply_markup()
    db.query('INSERT INTO cart VALUES (?, ?, 1, ?)',
             (query.message.chat.id, callback_data['id'], razdel))
    db.track_product_buy(query.from_user.id, callback_data['id'])

    await query.answer('Товар добавлен в корзину!')

#ПОКАЗАТЬ ФАЙЛЫ
@dp.callback_query_handler(IsUser(), files_cb.filter(action='show'))
async def file_show_callback_handler(query: CallbackQuery,
                                       callback_data: dict, state: FSMContext):
        files = db.fetchone('''SELECT files FROM products WHERE idx = ?''', (callback_data['id'],))[0]
        prod_name = db.fetchone('''SELECT title FROM products WHERE idx = ?''', (callback_data['id'],))[0]
        files = files.strip().rstrip('|').split("|")
        await query.message.answer(f"{prod_name}:")
        for file in files:
            await query.message.answer_document(file)