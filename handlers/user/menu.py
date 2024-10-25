import configparser
from aiogram.types import Message, ReplyKeyboardMarkup
from loader import dp
from filters import IsAdmin, IsUser
from aiogram.types import ContentType, MediaGroup, InputMediaDocument
from data.config import ADMINS
from loader import bot

catalog = '🛍️ Каталог'
cart = '🛒 Корзина'
delivery_status = '🚚 Статус заказа'

settings = '⚙️ Настройка разделов'
orders = '🚚 Заказы'
questions = '❓ Вопросы'
stat = "Статистика"

config = configparser.ConfigParser()
config.read("data/config.ini")

@dp.message_handler(commands='admin')
async def admin_menu(message: Message):
    print(config['BOT']["Admins"])
    admins = config['BOT']["Admins"].strip().split(",")
    if str(message.from_user.id) in admins:
        ADMINS.add(message.from_user.id)
        markup = ReplyKeyboardMarkup(selective=True)
        markup.add(settings)
        markup.add(questions, orders)
        markup.add(stat)

        await message.answer('Меню', reply_markup=markup)


@dp.message_handler(IsUser(), commands='menu')
async def user_menu(message: Message):
    markup = ReplyKeyboardMarkup(selective=True)
    markup.add(catalog)
    markup.add(cart)
    markup.add(delivery_status)

    await message.answer('Меню', reply_markup=markup)
