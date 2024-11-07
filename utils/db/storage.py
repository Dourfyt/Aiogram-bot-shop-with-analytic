from datetime import datetime
from sqlite3 import connect

import redis

session = redis.StrictRedis(host='redis', port=6379, db=0, decode_responses=True)

class DatabaseManager:

    def __init__(self, path):
        self.conn = connect(path)
        self.conn.execute('pragma foreign_keys = on')
        self.conn.commit()
        self.cur = self.conn.cursor()

    def create_tables(self):
        self.query(
            'CREATE TABLE IF NOT EXISTS products (idx text primary key, title text, '
            'body text, photo blob null, price int null, tag text, files text, FOREIGN KEY(tag) REFERENCES categories(idx) ON DELETE CASCADE)')
        self.query(
            'CREATE TABLE IF NOT EXISTS orders (cid int, usr_name text, '
            'usr_address text, products text, order_time timestamp, wish text, razdel text)')
        self.query(
            'CREATE TABLE IF NOT EXISTS cart (cid int, idx text, '
            'quantity int, razdel text)')
        self.query(
            'CREATE TABLE IF NOT EXISTS categories (idx text primary key, title text, tag text, FOREIGN KEY(tag) REFERENCES razdels(idx) ON DELETE CASCADE)')
        self.query(
            'CREATE TABLE IF NOT EXISTS razdels (idx text primary key, title text)')
        self.query(
            'CREATE TABLE IF NOT EXISTS questions (cid int, question text)')
        self.query('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_seen TIMESTAMP,
            last_seen TIMESTAMP,
            is_returning BOOLEAN
        )
        ''')
        self.query('''
        CREATE TABLE IF NOT EXISTS visits (
            visit_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            visit_time TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
        ''')

        self.query('''
        CREATE TABLE IF NOT EXISTS product_buys (
            view_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id TEXT,
            view_time TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY(product_id) REFERENCES products(idx) ON DELETE CASCADE
        )
        ''')
        
        self.query('''
        CREATE TABLE IF NOT EXISTS categories_views (
            view_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            categorie_id TEXT,
            view_time TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY(categorie_id) REFERENCES categories(idx) ON DELETE CASCADE
        )
        ''')
        self.query(
            'CREATE TABLE IF NOT EXISTS sessions (session_id integer PRIMARY KEY AUTOINCREMENT, session_key text, pages_visited int)')
        
        self.query(
            'CREATE TABLE IF NOT EXISTS abandoned_carts (user_id integer, time_checked timestamp)'
        )

    def query(self, arg, values=None):
        if values is None:
            self.cur.execute(arg)
        else:
            self.cur.execute(arg, values)
        self.conn.commit()

    def fetchone(self, arg, values=None):
        if values is None:
            self.cur.execute(arg)
        else:
            self.cur.execute(arg, values)
        return self.cur.fetchone()

    def fetchall(self, arg, values=None):
        if values is None:
            self.cur.execute(arg)
        else:
            self.cur.execute(arg, values)
        return self.cur.fetchall()
            
    def track_product_buy(self, user_id,product_id):
        product_exists = self.fetchone("SELECT * FROM products WHERE idx = ?", (product_id,))
        user_exists = self.fetchone("SELECT * FROM users WHERE user_id = ?", (user_id,))
        if not product_exists or not user_exists:
            raise ValueError("Product or User does not exist")
        else:
            self.query("INSERT INTO product_buys (user_id, product_id, view_time) VALUES (?, ?, ?)", 
                (user_id, product_id, datetime.now()))

    def __del__(self):
        self.conn.close()
