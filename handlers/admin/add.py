import random
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from aiogram.types import CallbackQuery
from hashlib import md5
from aiogram.dispatcher import FSMContext
from aiogram.types.chat import ChatActions
from aiogram.types import ReplyKeyboardMarkup
from aiogram.types import ReplyKeyboardRemove
from aiogram.types import ContentType

from handlers.user.menu import settings
from states import CategoryState, ProductState, RazdelState
from loader import bot
from loader import dp, db
from filters import IsAdmin
from keyboards.default.markups import *
from keyboards.inline.products_from_catalog import confirm_files_markup

razdel_cb = CallbackData('razdel', 'id', 'action')
category_cb = CallbackData('category', 'id', 'action')
product_cb = CallbackData('product', 'id', 'action')

files = []
file_names = []

delete_category = '🗑️ Удалить категорию'
rename_category = "Изменить название категории"
delete_razdel = "🗑️ Удалить раздел"
rename_razdel = "Изменить название раздела"
add_product = '➕ Добавить товар'
add_category_to_razdels = '➕ Добавить категорию'

#ПОКАЗЫВАЕТ СПИСОК РАЗДЕЛОВ
@dp.message_handler(IsAdmin(), text=settings)
async def process_settings(message: Message):

    markup = InlineKeyboardMarkup()

    for idx, title in db.fetchall('SELECT * FROM razdels'):

        markup.add(InlineKeyboardButton(
            title, callback_data=razdel_cb.new(id=idx, action='view')))

    markup.add(InlineKeyboardButton(
        '+ Добавить раздел', callback_data='add_razdel'))

    await message.answer('Настройка разделов:', reply_markup=markup)

#НАЗВАНИЕ РАЗДЕЛА
@dp.callback_query_handler(IsAdmin(), text='add_razdel')
async def add_razdel_callback_handler(query: CallbackQuery):
    await query.message.delete()
    await query.message.answer('Название раздела?')
    await RazdelState.title.set()

#ДОБАВЛЕНИЕ РАЗДЕЛА
@dp.message_handler(IsAdmin(), state=RazdelState.title)
async def set_razdel_title_handler(message: Message, state: FSMContext):

    razdel = message.text
    idx = random.getrandbits(16)
    db.query('INSERT INTO razdels VALUES (?, ?)', (idx, razdel))

    await state.finish()
    await process_settings(message)

# ПОКАЗЫВАЕТ КАТЕГОРИИ РАЗДЕЛА
@dp.callback_query_handler(IsAdmin(), razdel_cb.filter(action='view'))
async def category_callback_handler(query: CallbackQuery, callback_data: dict,
                                    state: FSMContext):
    razdel_idx = callback_data['id']
    async with state.proxy() as data:
        data["razdel_id"] = razdel_idx

    products = db.fetchall('''SELECT categories.idx, categories.title 
                        FROM categories 
                        WHERE categories.tag = ?;
                        ''',
                           (razdel_idx,))
    markup = InlineKeyboardMarkup()

    for idx, title in products:

        markup.add(InlineKeyboardButton(
            title, callback_data=category_cb.new(id=idx, action='view')))

    markup.add(InlineKeyboardButton(
        '+ Добавить категорию', callback_data='add_category_to_razdels'))
    
    reply =  ReplyKeyboardMarkup()
    reply.add(delete_razdel)
    reply.add(rename_razdel)

    await query.message.delete()
    await query.message.answer('Все категории этого раздела.', reply_markup=markup)
    await query.message.answer('Хотите что-нибудь добавить или удалить?', reply_markup=reply)
    await state.update_data(razdel_index=razdel_idx)

#ПОКАЗЫВАЕТ ТОВАРЫ
@dp.callback_query_handler(IsAdmin(), category_cb.filter(action='view'))
async def category_callback_handler(query: CallbackQuery, callback_data: dict,
                                    state: FSMContext):
    category_idx = callback_data['id']

    products = db.fetchall('''SELECT * FROM products
    WHERE tag = ?''',
                           (category_idx,))

    await query.message.delete()
    await query.answer('Все добавленные товары в эту категорию.')
    await state.update_data(category_index=category_idx)
    await show_products(query.message, products, category_idx)


#ПОКАЗЫВАЕТ ТОВАРЫ
async def show_products(m, products, category_idx):
    await bot.send_chat_action(m.chat.id, ChatActions.TYPING)
    try:
        for idx, title, body, image, price, tag, files, file_names in products:
            text = f'<b>{title}</b>\n\n{body}\n\nЦена: {price} рублей.'

            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(
                '🗑️ Удалить',
                callback_data=product_cb.new(id=idx, action='delete')))

            await m.answer_photo(photo=image,
                                caption=text,
                                reply_markup=markup)
            files = files.strip().rstrip('|||||').split("|||||")
            file_names = file_names.strip().rstrip(',').split(",")
            for file in files:
                await m.answer_document(file)
    except:
        pass

    markup = ReplyKeyboardMarkup()
    markup.add(add_product)
    markup.add(delete_category)
    markup.add(rename_category)

    await m.answer('Хотите что-нибудь добавить или удалить?',
                   reply_markup=markup)


#УДАЛЯЕТ РАЗДЕЛ
@dp.message_handler(IsAdmin(), text=delete_razdel)
async def delete_razdel_handler(message: Message, state: FSMContext):
    async with state.proxy() as data:
        if 'razdel_index' in data.keys():
            idx = data['razdel_index']

            db.query(
                'DELETE FROM categories WHERE tag IN (SELECT '
                'title FROM razdels WHERE idx=?)',
                (idx,))
            db.query('DELETE FROM razdels WHERE idx=?', (idx,))

            await message.answer('Готово!', reply_markup=ReplyKeyboardRemove())
            await process_settings(message)

#МЕНЯЕТ НАЗВАНИЕ РАЗДЕЛА
@dp.message_handler(IsAdmin(), text=rename_razdel)
async def rename_category_handler(message: Message, state: FSMContext):
    await message.answer('Введите новое название для раздела')
    await RazdelState.rename_razdel.set()

#МЕНЯЕТ НАЗВАНИЕ РАЗДЕЛА
@dp.message_handler(IsAdmin(), state=RazdelState.rename_razdel)
async def rename_category_handler(message: Message, state: FSMContext):
    async with state.proxy() as data:
        if 'razdel_index' in data.keys():
            idx = data['razdel_index']
            db.query("UPDATE razdels SET title = ? WHERE idx = ?", (message.text,idx,))
            await message.answer('Готово!', reply_markup=ReplyKeyboardRemove())
            await process_settings(message)
            await state.finish()


#УДАЛЯЕТ КАТЕГОРИЮ
@dp.message_handler(IsAdmin(), text=delete_category)
async def delete_category_handler(message: Message, state: FSMContext):
    async with state.proxy() as data:
        if 'category_index' in data.keys():
            idx = data['category_index']

            # Удаление связанных записей из таблиц, которые зависят от products и categories
            db.query('DELETE FROM product_buys WHERE product_id IN (SELECT idx FROM products WHERE tag=?)', (idx,))
            db.query('DELETE FROM products WHERE tag=?', (idx,))
            db.query('DELETE FROM categories_views WHERE categorie_id=?', (idx,))

            # Удаление категории
            db.query('DELETE FROM categories WHERE idx=?', (idx,))

            await message.answer('Готово!', reply_markup=ReplyKeyboardRemove())
            await process_settings(message)

#МЕНЯЕТ НАЗВАНИЕ КАТЕГОРИИ
@dp.message_handler(IsAdmin(), text=rename_category)
async def rename_category_handler(message: Message, state: FSMContext):
    await message.answer('Введите новое название для категории')
    await CategoryState.rename_category.set()

#МЕНЯЕТ НАЗВАНИЕ КАТЕГОРИИ
@dp.message_handler(IsAdmin(), state=CategoryState.rename_category)
async def rename_category_handler(message: Message, state: FSMContext):
    async with state.proxy() as data:
        if 'category_index' in data.keys():
            idx = data['category_index']
            db.query("UPDATE categories SET title = ? WHERE idx = ?", (message.text,idx,))
            await message.answer('Готово!', reply_markup=ReplyKeyboardRemove())
            await process_settings(message)
            await state.finish()


#ДОБАВИТЬ КАТЕГОРИЮ
@dp.callback_query_handler(IsAdmin(), lambda call: call.data == "add_category_to_razdels")
async def process_add_category(query: CallbackQuery):
    await CategoryState.add_category.set()

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(cancel_message)

    await query.message.answer('Название?', reply_markup=markup)

#ОТМЕНА СОЗДАНИЯ КАТЕГОРИИ
@dp.message_handler(IsAdmin(), text=cancel_message, state=CategoryState.add_category)
async def process_cancel(message: Message, state: FSMContext):
    await message.answer('Ок, отменено!', reply_markup=ReplyKeyboardRemove())
    await state.finish()

    await process_settings(message)

#СОХРАНЕНИЕ КАТЕГОРИИ
@dp.message_handler(IsAdmin(), state=CategoryState.add_category)
async def process_title(message: Message, state: FSMContext):
    async with state.proxy() as data:
        razdel_id = data.get('razdel_id')
    idx = str(random.getrandbits(64))
    db.query("INSERT INTO categories VALUES (?,?,?)", (idx,message.text,razdel_id,))
    await message.answer('Успешно добавлено!', reply_markup=ReplyKeyboardRemove())
    await state.finish()

    await process_settings(message)


#НАЧАЛО ДОБАВЛЕНИЕ ПРОДУКТА
@dp.message_handler(IsAdmin(), text=add_product)
async def process_add_product(message: Message, state: FSMContext):
    await message.answer('Введите название', reply_markup=ReplyKeyboardRemove())
    await ProductState.title.set()

#ОТМЕНА
@dp.message_handler(IsAdmin(), text=cancel_message, state=ProductState.title)
async def process_cancel(message: Message, state: FSMContext):
    await message.answer('Ок, отменено!', reply_markup=ReplyKeyboardRemove())
    await state.finish()

    await process_settings(message)

#СОХРАНЯЕТ НАЗВАНИЕ, ПРОСИТ ОПИСАНИЕ
@dp.message_handler(IsAdmin(), state=ProductState.title)
async def process_title(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['title'] = message.text

    await ProductState.next()
    await message.answer('Описание?', reply_markup=back_markup())


@dp.message_handler(IsAdmin(), text=back_message, state=ProductState.title)
async def process_title_back(message: Message, state: FSMContext):
    await process_add_product(message)


@dp.message_handler(IsAdmin(), text=back_message, state=ProductState.body)
async def process_body_back(message: Message, state: FSMContext):
    await ProductState.title.set()

    async with state.proxy() as data:
        await message.answer(f"Изменить название с <b>{data['title']}</b>?",
                             reply_markup=back_markup())

#СОХРАНЯЕТ ОПИСАНИЕ, ПРОСИТ ФОТО
@dp.message_handler(IsAdmin(), state=ProductState.body)
async def process_body(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['body'] = message.text

    await ProductState.next()
    await message.answer('Фото?', reply_markup=back_markup())

#ПОЛУЧАЕТ ФОТО, ПРОСИТ ФАЙЛ
@dp.message_handler(IsAdmin(), content_types=ContentType.PHOTO,
                    state=ProductState.image)
async def process_image_photo(message: Message, state: FSMContext):
    fileID = message.photo[-1].file_id
    file_info = await bot.get_file(fileID)
    downloaded_file = (await bot.download_file(file_info.file_path)).read()

    async with state.proxy() as data:
        data['image'] = downloaded_file

    await ProductState.next()
    await message.answer('Пришлите по одному файлу для прикрепления или нажмите кнопку "Дальше"', reply_markup=confirm_files_markup())

#ПОЛУЧАЕТ ФАЙЛ И ПРОСИТ ЕЩЕ
@dp.message_handler(IsAdmin(), content_types=ContentType.DOCUMENT,
                    state=ProductState.files)
async def process_files(message: Message, state: FSMContext):
    fileID = message.document.file_id
    fileNAME = message.document.file_name
    file_info = await bot.get_file(fileID)
    downloaded_file = (await bot.download_file(file_info.file_path)).read()
    files.append(fileID)
    file_names.append(fileNAME)
    await message.answer('Это все файлы? Если нет, пришлите еще', reply_markup=confirm_files_markup())

#СОХРАНЯЕТ ФАЙЛ И ПРОСИТ ЦЕНУ
@dp.callback_query_handler(IsAdmin(), text='confirm_files', state=ProductState.files)
async def confirm_process_files(query : CallbackQuery,  state: FSMContext):
    await ProductState.next()
    async with state.proxy() as data:
        data['files'] = files
        data['file_names'] = file_names
    await query.message.answer("Цена?")

#СОХРАНЯЕТ ЦЕНУ И ВЫВОДИТ ПРЕДПРОСМОТР ТОВАРА
@dp.message_handler(IsAdmin(), lambda message: message.text.isdigit(),
                    state=ProductState.price)
async def process_price(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['price'] = message.text

        title = data['title']
        body = data['body']
        price = data['price']
        files = data['files']
        file_names = data['file_names']

        await ProductState.next()
        text = f'<b>{title}</b>\n\n{body}\n\nЦена: {price} рублей.'

        markup = check_markup()

        await message.answer_photo(photo=data['image'],
                                   caption=text,
                                   reply_markup=markup)
        for file in files:
            for name in file_names:
                await message.answer_document(file, caption=name)

#СОХРАНЯЕТ ТОВАР В БД
@dp.message_handler(IsAdmin(), text=all_right_message,
                    state=ProductState.confirm)
async def process_confirm(message: Message, state: FSMContext):
    async with state.proxy() as data:
        title = data['title']
        body = data['body']
        image = data['image']
        price = data['price']
        files = ''.join([f"{file}|||||" for file in data['files']])
        file_names = ''.join([f"{file}," for file in data['file_names']])

        tag = db.fetchone(
            'SELECT idx FROM categories WHERE idx=?',
            (data['category_index'],))[0]
        idx = md5(' '.join([title, body, price, tag]
                           ).encode('utf-8')).hexdigest()
        print(tag)
        db.query('INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                 (idx, title, body, image, int(price), str(tag).strip(), files, file_names))

    await state.finish()
    await message.answer('Готово!', reply_markup=ReplyKeyboardRemove())
    await process_settings(message)


#УДАЛЯЕТ ПРОДУКТ
@dp.callback_query_handler(IsAdmin(), product_cb.filter(action='delete'))
async def delete_product_callback_handler(query: CallbackQuery,
                                          callback_data: dict):
    product_idx = callback_data['id']
    db.query('DELETE FROM products WHERE idx=?', (product_idx,))
    await query.answer('Удалено!')
    await query.message.delete()


@dp.message_handler(IsAdmin(), text=back_message, state=ProductState.confirm)
async def process_confirm_back(message: Message, state: FSMContext):
    await ProductState.price.set()

    async with state.proxy() as data:
        await message.answer(f"Изменить цену с <b>{data['price']}</b>?",
                             reply_markup=back_markup())


@dp.message_handler(IsAdmin(), content_types=ContentType.TEXT,
                    state=ProductState.image)
async def process_image_url(message: Message, state: FSMContext):
    if message.text == back_message:

        await ProductState.body.set()

        async with state.proxy() as data:

            await message.answer(f"Изменить описание с <b>{data['body']}</b>?",
                                 reply_markup=back_markup())

    else:

        await message.answer('Вам нужно прислать фото товара.')


@dp.message_handler(IsAdmin(), lambda message: not message.text.isdigit(),
                    state=ProductState.price)
async def process_price_invalid(message: Message, state: FSMContext):
    if message.text == back_message:

        await ProductState.image.set()

        async with state.proxy() as data:

            await message.answer("Другое изображение?",
                                 reply_markup=back_markup())

    else:

        await message.answer('Укажите цену в виде числа!')


@dp.message_handler(IsAdmin(),
                    lambda message: message.text not in [back_message,
                                                         all_right_message],
                    state=ProductState.confirm)
async def process_confirm_invalid(message: Message, state: FSMContext):
    await message.answer('Такого варианта не было.')

