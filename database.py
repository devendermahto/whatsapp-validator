import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "whatsapp_checker.db")


def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER PRIMARY KEY,
            api_url TEXT,
            instance_name TEXT,
            api_key TEXT,
            state TEXT DEFAULT 'IDLE',
            last_activity TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def get_user(chat_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id, api_url, instance_name, api_key, state, last_activity FROM users WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            'chat_id': row[0],
            'api_url': row[1],
            'instance_name': row[2],
            'api_key': row[3],
            'state': row[4],
            'last_activity': row[5]
        }
    return None


def update_user_api(chat_id, url, instance, key):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO users (chat_id, api_url, instance_name, api_key, state, last_activity)
        VALUES (?, ?, ?, ?, 'IDLE', ?)
    """, (chat_id, url, instance, key, datetime.now()))
    conn.commit()
    conn.close()


def update_state(chat_id, state):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET state = ?, last_activity = ? WHERE chat_id = ?", (state, datetime.now(), chat_id))
    conn.commit()
    conn.close()


def user_exists(chat_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM users WHERE chat_id = ?", (chat_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None