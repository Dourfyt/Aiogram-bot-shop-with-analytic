from celery import Celery
from datetime import datetime, timedelta
from loader import session, db
import logging

app = Celery('tasks', broker='redis://redis-db:6379/0')



@app.task(bind=True)
def check_cart_sessions(self, user_id):
    sess = session.get(f"session:{user_id}")
    logging.info("Проверка запущена!")
    if sess:
        order_exists = db.fetchone("SELECT 1 FROM orders WHERE cid = ? AND order_time > ?", (user_id,(datetime.now()-timedelta(hours=1)).isoformat()))
        if not order_exists:
            print(f"Корзина пользователя {user_id} не отправлена. Сессия не завершена Продолжаем проверку.")
            self.apply_async((user_id,), countdown= 5 * 59)  # Перезапуск через 20 минут
    else:
        print(f"Корзина пользователя {user_id} пуста. Сессия завершена.")
        db.query("INSERT INTO abandoned_carts (user_id, time_checked) VALUES (?, ?)",
                     (user_id, datetime.now().isoformat(),))
        session.delete(f"session:{user_id}")
