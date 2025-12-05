import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "expense.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db():
    if not os.path.exists(DB_PATH):
        conn = get_db_connection()
        c = conn.cursor()

        c.execute("""CREATE TABLE users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT UNIQUE,
                        password TEXT
                    )""")

        c.execute("""CREATE TABLE groups (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        owner INTEGER
                    )""")

        c.execute("""CREATE TABLE group_users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        group_id INTEGER,
                        user_id INTEGER
                    )""")

        c.execute("""CREATE TABLE expenses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        group_id INTEGER,
                        payer INTEGER,
                        amount REAL,
                        description TEXT
                    )""")

        conn.commit()
        conn.close()
