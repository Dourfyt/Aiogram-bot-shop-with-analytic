from datetime import datetime, timedelta
import logging
from aiogram.types import Message
from loader import dp, db
from handlers.user.menu import orders
import pandas as pd
from filters import IsAdmin
import matplotlib.pyplot as plt

month = (datetime.now() - timedelta(days=31)).isoformat()
week = (datetime.now() - timedelta(days=7)).isoformat()
day = (datetime.now() - timedelta(days=1)).isoformat()

@dp.message_handler(IsAdmin(), text='Статистика')
async def report(message: Message):
    msg = await message.answer("Генерация отчета...")
    msg

    users = db.fetchone("SELECT COUNT(*) FROM users")
    categories = db.fetchall("SELECT idx,title from categories")
    abandoned_carts = get_abandoned_carts()
    abandonment_rate = get_abandoned_rate()

    visits = get_visits()
    active_users = get_active_users()
    new_users = get_new_users()
    orders = get_orders()
 
    try:
        await msg.edit_text(
                            f"ПОСЕТИТЕЛИ 🧍‍♀🧍‍♂\n\n" \
                            f'КОЛИЧЕСТВО ПОЛЬЗОВАТЕЛЕЙ - {users[0]}\n\n' \
                            f'НОВЫЕ Д / Н / М - {new_users[0]} / {new_users[1]} / {new_users[2]}\n\n' \
                            f'АКТИВНЫЕ Д / Н / М - {active_users[0]} / {active_users[1]} / {active_users[2]}\n\n' \
                            f'ВЕРНУВШИЕСЯ ЗА МЕСЯЦ - {get_back()}\n\n' \
                            f'ПОСЕЩЕНИЙ Д / Н / М - {visits[0]} / {visits[1]} / {visits[2]}\n\n' \
                            f'ПРОСМОТРОВ ЗА СЕССИЮ СРЕДНЕЕ - {get_pages_visited_for_session()}\n\n' \
                            "==================\n\n" \
                            'КОРЗИНА 🗑\n\n' \
                            f'НЕ ОТПРАВЛЕНО Д / Н / М  - {abandoned_carts[0]} / {abandoned_carts[1]} / {abandoned_carts[2]}\n\n' \
                            f'НЕ ОТПРАВЛЕНО ОТ ОБЩЕГО КОЛ-ВА ПОСЕТИТЕЛЕЙ Д / Н / М - {abandonment_rate[0]}% / {abandonment_rate[1]}% / {abandonment_rate[2]}%\n\n'
                            f'ОТПРАВЛЕНО Д / Н / М - {orders[0]} / {orders[1]} / {orders[2]}\n\n'
                            f'КОНВЕРСИЯ Д / Н / М - {round((orders[0]/visits[0]), 2)*100}% / {round((orders[1]/visits[1]),2)*100}% / {round((orders[2]/visits[2]),2)*100}%\n\n'
                            )
        msg = '==================\n\nСТАТИСТИКА ПО ТОВАРАМ: \n\n'


        for categorie in categories:
            views_cat = get_views_cat(categorie)
            products = db.fetchall("SELECT idx,title from products WHERE tag = ?", (categorie[1],))
            msg = msg + f"------------------\n\n{categorie[1]}:\nПРОСМОТРОВ КАТЕГОРИИ Д / Н / М - {views_cat[0]} / {views_cat[1]} / {views_cat[2]}\n" + "\n"
            for product in products:
                cart_adds = get_cart_adds(product)
                msg = msg + f"- ТОВАР {product[1]}\nДОБАВЛЕНО Д / Н / М - {cart_adds[0]} / {cart_adds[1]} / {cart_adds[2]}\n\n"
        await message.answer(msg)
    except:
        logging.error('Ошибка при создании отчета')

    try:
        make_graph_visits()
        with open('graphs/attendance.png', 'rb') as photo:
            await message.answer_photo(photo)
    except:
        logging.error('Ошибка при создании графика посещаемости')
    try:
        make_graph_categories_views()
        with open('graphs/daily_category_visits.png', 'rb') as photo:
            await message.answer_photo(photo)
    except:
        logging.error('Ошибка при создании графика посещаемости категорий')

def get_visits() -> tuple: 
    visits_for_month = db.fetchone("SELECT COUNT(*) FROM visits WHERE visit_time > ?", (month,))[0]
    visits_for_week = db.fetchone("SELECT COUNT(*) FROM visits WHERE visit_time > ?", (week,))[0]
    visits_for_day = db.fetchone("SELECT COUNT(*) FROM visits WHERE visit_time > ?", (day,))[0]
    return (visits_for_day, visits_for_week, visits_for_month)

def get_active_users() -> tuple:
    active_users_for_month = db.fetchone("SELECT COUNT(*) from users WHERE last_seen > ?", (month,))[0]
    active_users_for_week = db.fetchone("SELECT COUNT(*) from users WHERE last_seen > ?", (week,))[0]
    active_users_for_day = db.fetchone("SELECT COUNT(*) from users WHERE last_seen > ?", (day,))[0]
    return (active_users_for_day, active_users_for_week, active_users_for_month)

def get_new_users() -> tuple:
    new_users_for_month = db.fetchone("SELECT COUNT(*) from users WHERE first_seen > ?", (month,))[0]
    new_users_for_week= db.fetchone("SELECT COUNT(*) from users WHERE first_seen > ?", (week,))[0]
    new_users_for_day = db.fetchone("SELECT COUNT(*) from users WHERE first_seen > ?", (day,))[0]
    return (new_users_for_day, new_users_for_week, new_users_for_month)

def get_cart_adds(product) -> tuple:
    cart_for_month = db.fetchone("SELECT COUNT(*) FROM product_buys WHERE product_id = ? AND view_time > ?", (product[0], month,))[0]
    cart_for_week = db.fetchone("SELECT COUNT(*) FROM product_buys WHERE product_id = ? AND view_time > ?", (product[0], week,))[0]
    cart_for_day = db.fetchone("SELECT COUNT(*) FROM product_buys WHERE product_id = ? AND view_time > ?", (product[0], day,))[0]
    return (cart_for_day,cart_for_week, cart_for_month)

def get_views_cat(categorie) -> tuple:
    views_cat_for_month = db.fetchone("SELECT COUNT(*) FROM categories_views WHERE categorie_id = ? AND view_time > ?", (categorie[0], month,))[0]
    views_cat_for_week = db.fetchone("SELECT COUNT(*) FROM categories_views WHERE categorie_id = ? AND view_time > ?", (categorie[0], week,))[0]
    views_cat_for_day = db.fetchone("SELECT COUNT(*) FROM categories_views WHERE categorie_id = ? AND view_time > ?", (categorie[0], day,))[0]
    return (views_cat_for_day, views_cat_for_week, views_cat_for_month)

def get_abandoned_rate() -> tuple:
    visits = get_visits()
    abandoned_carts = get_abandoned_carts()
    if visits[0] > 0:
        abandonment_rate_for_day = (abandoned_carts[0] / visits[0]) * 10
    else:
        abandonment_rate_for_day = 'НЕТ ДАННЫХ'

    if visits[1] > 0:
        abandonment_rate_for_week = (abandoned_carts[1] / visits[1]) * 100
    else:
        abandonment_rate_for_week = 'НЕТ ДАННЫХ'

    if visits[2] > 0:
        abandonment_rate_for_month = (abandoned_carts[2] / visits[2]) * 100
    else:
        abandonment_rate_for_month = 'НЕТ ДАННЫХ'

    return (round(float(abandonment_rate_for_day),2), round(float(abandonment_rate_for_week),2), round(float(abandonment_rate_for_month),2))
    
def get_abandoned_carts():
    for_day = db.fetchone("SELECT COUNT(*) FROM abandoned_carts WHERE time_checked > ?", (day,))[0]
    for_week = db.fetchone("SELECT COUNT(*) FROM abandoned_carts WHERE time_checked > ?", (week,))[0]
    for_month = db.fetchone("SELECT COUNT(*) FROM abandoned_carts WHERE time_checked > ?", (month,))[0]
    return (for_day, for_week, for_month)

def get_orders():
    for_day = db.fetchone("SELECT COUNT(*) FROM orders WHERE order_time > ?", ((datetime.now()-timedelta(days=1)).isoformat(),))[0]
    for_week = db.fetchone("SELECT COUNT(*) FROM orders WHERE order_time > ?", ((datetime.now()-timedelta(days=7)).isoformat(),))[0]
    for_month = db.fetchone("SELECT COUNT(*) FROM orders WHERE order_time > ?", ((datetime.now()-timedelta(days=31)).isoformat(),))[0]
    return (for_day, for_week, for_month)

def get_pages_visited_for_session():
    return round(db.fetchone("SELECT AVG(pages_visited) FROM sessions")[0],2)

def get_back():
    return db.fetchone("SELECT COUNT(*) FROM users WHERE is_returning = 1 AND last_seen > ?", (month,))[0]

def make_graph_visits():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    query = """
        SELECT visit_time 
        FROM visits
        WHERE visit_time BETWEEN ? AND ?
    """
    # Выполняем запрос к базе данных
    data = db.fetchall(query, (start_date.isoformat(), end_date.isoformat()))
    # Преобразуем данные в DataFrame
    df = pd.DataFrame(data, columns=['visit_time'])
    df['visit_time'] = pd.to_datetime(df['visit_time'])

    # Группируем данные по дням и считаем количество посещений
    df['day'] = df['visit_time'].dt.date
    daily_counts = df.groupby('day').size()

    # Построение графика
    plt.figure(figsize=(10, 5))
    daily_counts.plot(kind='bar', color='skyblue')
    plt.title('Ежедневные посещения за последний месяц')
    plt.xlabel('Дата')
    plt.ylabel('Количество посещений')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("graphs/attendance.png", bbox_inches='tight')

def make_graph_categories_views():
    # Устанавливаем временные рамки
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    # Запрос к базе данных
    query = """
        SELECT c.title AS category_title, r.title AS section_title, cv.view_time 
        FROM categories_views AS cv
        JOIN categories AS c ON cv.categorie_id = c.idx 
        JOIN razdels AS r ON c.tag = r.idx 
        WHERE cv.view_time BETWEEN ? AND ?
    """
    # Выполняем запрос к базе данных
    data = db.fetchall(query, (start_date.isoformat(), end_date.isoformat()))

    # Преобразуем данные в DataFrame
    df = pd.DataFrame(data, columns=['category_title', 'section_title', 'view_time'])
    df['view_time'] = pd.to_datetime(df['view_time'])

    # Создаем полный заголовок, комбинируя названия разделов и категорий
    df['full_title'] = df['section_title'] + ' - ' + df['category_title']

    # Группируем данные по дате и полному заголовку, считаем количество посещений
    df['day'] = df['view_time'].dt.date
    daily_counts = df.groupby(['day', 'full_title']).size().unstack(fill_value=0)

    # Построение графика
    plt.figure(figsize=(12, 6))
    daily_counts.plot(kind='line', marker='o', figsize=(12, 6))
    plt.title('Посещения категорий за последний месяц')
    plt.xlabel('Дата')
    plt.ylabel('Количество посещений')
    plt.xticks(rotation=45)
    plt.legend(title='Категория', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig("graphs/daily_category_visits.png")
    plt.close()  # Закрываем текущее окно графика