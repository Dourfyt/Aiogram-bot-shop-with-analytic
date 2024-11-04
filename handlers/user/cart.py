from datetime import datetime
from filters import IsUser
from aiogram.types import Message
from aiogram.dispatcher import FSMContext
from aiogram.types.chat import ChatActions
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.types import CallbackQuery
import logging
from utils.tasks.mail import *

from loader import db, dp, bot
from .menu import cart, user_menu
from keyboards.inline.products_from_cart import product_markup
from keyboards.inline.products_from_catalog import product_cb
from states import CheckoutState
from keyboards.default.markups import *

@dp.message_handler(IsUser(), text=cart)
async def process_cart(message: Message, state: FSMContext):

    cart_data = db.fetchall(
        'SELECT * FROM cart WHERE cid=?', (message.chat.id,))

    if len(cart_data) == 0:

        await message.answer('Ваша корзина пуста.')

    else:

        await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
        async with state.proxy() as data:
            data['products'] = {}

        order_cost = 0

        for _, idx, count_in_cart, _ in cart_data:

            product = db.fetchone('SELECT * FROM products WHERE idx=?', (idx,))

            if product == None:

                db.query('DELETE FROM cart WHERE idx=?', (idx,))

            else:
                _, title, body, image, price, _, _ = product
                order_cost += price

                async with state.proxy() as data:
                    data['products'][idx] = [title, price, count_in_cart]

                markup = product_markup(idx, count_in_cart)
                if price != 0:
                    text = f'<b>{title}</b>\n\n{body}\n\nЦена: {price} ₽'
                else:
                    text = f'<b>{title}</b>\n\n{body}\n\n'

                if image != "":
                    await message.answer_photo(photo=image,
                                        caption=text,
                                        reply_markup=markup)
                else:
                    await message.answer(text, reply_markup=markup) 

            markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
            markup.add('📦 Оформить заказ')

            await message.answer('Перейти к оформлению?',
                                 reply_markup=markup)


@dp.callback_query_handler(IsUser(), product_cb.filter(action='count'))
@dp.callback_query_handler(IsUser(), product_cb.filter(action='increase'))
@dp.callback_query_handler(IsUser(), product_cb.filter(action='decrease'))
async def product_callback_handler(query: CallbackQuery, callback_data: dict,
                                   state: FSMContext):
    idx = callback_data['id']
    action = callback_data['action']

    if 'count' == action:

        async with state.proxy() as data:

            if 'products' not in data.keys():

                await process_cart(query.message, state)

            else:

                await query.answer('Количество - ' + data['products'][idx][2])

    else:

        async with state.proxy() as data:

            if 'products' not in data.keys():

                await process_cart(query.message, state)

            else:

                data['products'][idx][2] += 1 if 'increase' == action else -1
                count_in_cart = data['products'][idx][2]

                if count_in_cart == 0:

                    db.query('''DELETE FROM cart
                    WHERE cid = ? AND idx = ?''', (query.message.chat.id, idx))

                    await query.message.delete()
                else:

                    db.query('''UPDATE cart 
                    SET quantity = ? 
                    WHERE cid = ? AND idx = ?''',
                             (count_in_cart, query.message.chat.id, idx))

                    await query.message.edit_reply_markup(
                        product_markup(idx, count_in_cart))


@dp.message_handler(IsUser(), text='📦 Оформить заказ')
async def process_checkout(message: Message, state: FSMContext):
    await CheckoutState.check_cart.set()
    await checkout(message, state)


async def checkout(message, state):
    answer = ''
    total_price = 0

    async with state.proxy() as data:

        for title, price, count_in_cart in data['products'].values():

            tp = count_in_cart * price
            answer += f'<b>{title}</b> * {count_in_cart}шт. = {tp}₽\n'
            total_price += tp
        data['total_price'] = total_price

    await message.answer(f'{answer}\nОбщая сумма заказа: {total_price}₽.',
                         reply_markup=check_markup())


@dp.message_handler(IsUser(),
                    lambda message: message.text not in [all_right_message,
                                                         back_message],
                    state=CheckoutState.check_cart)
async def process_check_cart_invalid(message: Message):
    await message.reply('Такого варианта не было.')


@dp.message_handler(IsUser(), text=back_message,
                    state=CheckoutState.check_cart)
async def process_check_cart_back(message: Message, state: FSMContext):
    await state.finish()
    await process_cart(message, state)


@dp.message_handler(IsUser(), text=all_right_message,
                    state=CheckoutState.check_cart)
async def process_check_cart_all_right(message: Message, state: FSMContext):
    await CheckoutState.next()
    await message.answer('Укажите свое имя.',
                         reply_markup=back_markup())


@dp.message_handler(IsUser(), text=back_message, state=CheckoutState.name)
async def process_name_back(message: Message, state: FSMContext):
    await CheckoutState.check_cart.set()
    await checkout(message, state)


@dp.message_handler(IsUser(), state=CheckoutState.name)
async def process_name(message: Message, state: FSMContext):

    async with state.proxy() as data:

        data['name'] = message.text

        if 'address' in data.keys():

            await confirm(message)
            await CheckoutState.confirm.set()

        else:

            await CheckoutState.next()
            await message.answer('Пожалуйста, укажите Ваши контактные данные.',
                                 reply_markup=back_markup())


@dp.message_handler(IsUser(), text=back_message, state=CheckoutState.address)
async def process_address_back(message: Message, state: FSMContext):

    async with state.proxy() as data:

        await message.answer('Изменить имя с <b>' + data['name'] + '</b>?',
                             reply_markup=back_markup())

    await CheckoutState.name.set()


@dp.message_handler(IsUser(), state=CheckoutState.address)
async def process_address(message: Message, state: FSMContext):

    async with state.proxy() as data:
        data['address'] = message.text

    await message.answer("Введите пожелания по заказу", reply_markup=wish_markup())
    await CheckoutState.next()

@dp.message_handler(IsUser(), state=CheckoutState.wish)
async def process_address(message: Message, state: FSMContext):

    async with state.proxy() as data:
        data['wish'] = message.text

    await confirm(message)
    await CheckoutState.next()


async def confirm(message):
    await message.answer(
        'Убедитесь, что все правильно оформлено и подтвердите заказ.',
        reply_markup=confirm_markup())


@dp.message_handler(IsUser(),
                    lambda message: message.text not in [confirm_message,
                                                         back_message],
                    state=CheckoutState.confirm)
async def process_confirm_invalid(message: Message):
    await message.reply('Такого варианта не было.')


@dp.message_handler(IsUser(), text=back_message, state=CheckoutState.confirm)
async def process_confirm(message: Message, state: FSMContext):

    await CheckoutState.address.set()

    async with state.proxy() as data:
        await message.answer('Изменить контактные данные с <b>' + data['address'] + '</b>?',
                             reply_markup=back_markup())


@dp.message_handler(IsUser(), text=confirm_message,
                    state=CheckoutState.confirm)
async def process_confirm(message: Message, state: FSMContext):

    markup = ReplyKeyboardRemove()


    logging.info('Совершен заказ.')

    async with state.proxy() as data:
        cid = message.chat.id
        username = message.from_user.username
        products = [idx + '=' + str(quantity)
                    for idx, quantity in db.fetchall('''SELECT idx, quantity FROM cart
        WHERE cid=?''', (cid,))]
        razdel = [str(razdel[0]) for razdel in db.fetchall('''SELECT razdel FROM cart WHERE cid=?''', (cid,))]

        db.query('INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?)',
                 (cid, data['name'], data['address'], ' '.join(products), datetime.now().isoformat(), data["wish"], ' '.join(razdel),))

        db.query('DELETE FROM cart WHERE cid=?', (cid,))

        await message.answer(
            'Ок! Ваш заказ уже выполняется  🚀\nИмя: <b>' + data['name'] + '</b>\nКонтактные данные: <b>' + data['address'] + '</b>\nПожелания: <b>' + data['wish'] + '</b>',
            reply_markup=markup
        )
        Bot = await bot.get_me()
        bot_name, bot_username = Bot.first_name, Bot.username
        send_msg(username, cid, data['name'], data['address'],razdel,products, data['wish'], data["total_price"], bot_name, bot_username)
        
    await state.finish()
    await user_menu(message)
