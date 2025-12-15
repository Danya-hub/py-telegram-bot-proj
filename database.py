import sqlite3
from config import DB_NAME

def get_db():
    return sqlite3.connect(DB_NAME)

def init_db():
    db = get_db()
    cur = db.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER UNIQUE,
        phone TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS bot_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER UNIQUE,
        name TEXT,
        role TEXT CHECK(role IN ('manager','admin'))
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price REAL,
        description TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_chat INTEGER,
        product_id INTEGER,
        status TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_chat INTEGER,
        text TEXT
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        user_chat INTEGER NOT NULL,
        total_amount INTEGER NOT NULL,  -- в мінімальних одиницях валюти (копійки)
        currency TEXT NOT NULL,
        provider_payment_charge_id TEXT,
        telegram_payment_charge_id TEXT,
        status TEXT NOT NULL DEFAULT 'paid',
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """)

    db.commit()
    db.close()
