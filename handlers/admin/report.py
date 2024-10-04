from datetime import datetime, timedelta
from aiogram.types import Message
from loader import dp, db
from handlers.user.menu import orders
from filters import IsAdmin


@dp.message_handler(IsAdmin(), commands=['report'])
async def report(message: Message):
    visits = db.fetchone("SELECT COUNT(*) FROM visits")
    users = db.fetchone("SELECT COUNT(*) FROM users")
    active_users = db.fetchone("SELECT COUNT(*) from users WHERE last_seen > ?", ((datetime.now() - timedelta(days=31)).isoformat(),))
    categories = db.fetchall("SELECT idx,title from categories")
  
    await message.answer(f'Количество пользователей - {users[0]}\nКоличество активных пользователей за месяц - {active_users[0]}\nКоличество посещений - {visits[0]}')
    msg = 'Статистика по товарам: \n'
    print(categories)
    for categorie in categories:
        products = db.fetchall("SELECT idx,title from products WHERE tag = ?", (categorie[1],))
        msg = msg + f"Категория - {categorie[1]}: \n" + "\n"
        print(products)
        print(categorie[1])
        for product in products:
            print(product)
            cart = db.fetchone("SELECT COUNT(*) FROM product_buys WHERE product_id = ?", (product[0],))
            msg = msg + f"   Товар {product[1]}\n      Добавлений в корзину - {cart[0]}\n\n"
    await message.answer(msg)