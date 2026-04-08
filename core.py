import re
import time
import random
import sqlite3
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS web_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_url TEXT,
            instance_name TEXT,
            api_key TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def get_api_credentials(user_id=1):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT api_url, instance_name, api_key FROM web_users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {'api_url': row[0], 'instance_name': row[1], 'api_key': row[2]}
    return None


def save_api_credentials(api_url, instance_name, api_key, user_id=1):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO web_users (id, api_url, instance_name, api_key)
        VALUES (?, ?, ?, ?)
    """, (user_id, api_url, instance_name, api_key))
    conn.commit()
    conn.close()


def chunk_list(lst, size=50):
    for i in range(0, len(lst), size):
        yield lst[i:i+size]


def check_number(api_url, instance_name, api_key, phone_number):
    import requests
    url = f"{api_url.rstrip('/')}/chat/whatsappNumbers/{instance_name}"
    headers = {'apikey': api_key, 'Content-Type': 'application/json'}
    payload = {"numbers": [phone_number]}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            results = data.get('response', [])
            if results and len(results) > 0:
                exists = results[0].get('exists', False)
                if exists:
                    return {'number': phone_number, 'status': 'valid', 'emoji': '✅'}
                else:
                    return {'number': phone_number, 'status': 'invalid', 'emoji': '⛔️'}
        return {'number': phone_number, 'status': 'error', 'emoji': '⏳'}
    except Exception as e:
        return {'number': phone_number, 'status': 'error', 'emoji': '⏳', 'error': str(e)}


def check_connection(api_url, instance_name, api_key):
    import requests
    url = f"{api_url.rstrip('/')}/instance/connectionState/{instance_name}"
    headers = {'apikey': api_key}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        return response.status_code == 200
    except:
        return False


def process_numbers(numbers, api_url, instance_name, api_key, progress_callback=None):
    results = {'valid': [], 'invalid': [], 'error': []}
    
    numbers = list(set(numbers))
    batches = list(chunk_list(numbers, 50))
    
    for batch_idx, batch in enumerate(batches):
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {executor.submit(check_number, api_url, instance_name, api_key, num): num for num in batch}
            
            for future in as_completed(futures):
                result = future.result()
                results[result['status']].append(result['number'])
                
                if progress_callback:
                    progress_callback(result)
                
                time.sleep(random.uniform(2.5, 5.5))
        
        if batch_idx < len(batches) - 1:
            time.sleep(180)
            if progress_callback:
                progress_callback({'type': 'batch_complete', 'batch': batch_idx + 1, 'total': len(batches)})
    
    return results