import re
import time
import random
import sqlite3
import os
import uuid
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
            password TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            status TEXT DEFAULT 'pending',
            total_numbers INTEGER DEFAULT 0,
            valid_count INTEGER DEFAULT 0,
            invalid_count INTEGER DEFAULT 0,
            error_count INTEGER DEFAULT 0,
            processed_count INTEGER DEFAULT 0,
            valid_numbers TEXT,
            invalid_numbers TEXT,
            error_numbers TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
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


def save_user_auth(username, password):
    import hashlib
    hashed = hashlib.sha256(password.encode()).hexdigest()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO web_users (id, username, password)
        VALUES (1, ?, ?)
    """, (username, hashed))
    conn.commit()
    conn.close()


def verify_user(username, password):
    import hashlib
    hashed = hashlib.sha256(password.encode()).hexdigest()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM web_users WHERE id = 1 AND username = ? AND password = ?", (username, hashed))
    row = cursor.fetchone()
    conn.close()
    return row is not None


def get_jobs(limit=50):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, status, total_numbers, valid_count, invalid_count, error_count, 
               processed_count, created_at, completed_at
        FROM jobs 
        ORDER BY created_at DESC 
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    jobs = []
    for row in rows:
        jobs.append({
            'id': row[0],
            'status': row[1],
            'total_numbers': row[2],
            'valid_count': row[3],
            'invalid_count': row[4],
            'error_count': row[5],
            'processed_count': row[6],
            'created_at': row[7],
            'completed_at': row[8]
        })
    return jobs


def get_job(job_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, status, total_numbers, valid_count, invalid_count, error_count,
               processed_count, valid_numbers, invalid_numbers, error_numbers,
               created_at, completed_at
        FROM jobs WHERE id = ?
    """, (job_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            'id': row[0],
            'status': row[1],
            'total_numbers': row[2],
            'valid_count': row[3],
            'invalid_count': row[4],
            'error_count': row[5],
            'processed_count': row[6],
            'valid_numbers': row[7].split(',') if row[7] else [],
            'invalid_numbers': row[8].split(',') if row[8] else [],
            'error_numbers': row[9].split(',') if row[9] else [],
            'created_at': row[10],
            'completed_at': row[11]
        }
    return None


def create_job(job_id, total):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO jobs (id, status, total_numbers, processed_count)
        VALUES (?, 'processing', ?, 0)
    """, (job_id, total))
    conn.commit()
    conn.close()


def update_job_progress(job_id, valid, invalid, error):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE jobs SET valid_count = ?, invalid_count = ?, error_count = ? WHERE id = ?
    """, (valid, invalid, error, job_id))
    conn.commit()
    conn.close()


def complete_job(job_id, valid_numbers, invalid_numbers, error_numbers):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE jobs SET 
            status = 'completed',
            valid_numbers = ?,
            invalid_numbers = ?,
            error_numbers = ?,
            completed_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (','.join(valid_numbers), ','.join(invalid_numbers), ','.join(error_numbers), job_id))
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


def process_numbers(numbers, api_url, instance_name, api_key, progress_callback=None, job_id=None):
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
                
                if job_id:
                    update_job_progress(job_id, len(results['valid']), len(results['invalid']), len(results['error']))
                
                time.sleep(random.uniform(2.5, 5.5))
        
        if batch_idx < len(batches) - 1:
            time.sleep(180)
            if progress_callback:
                progress_callback({'type': 'batch_complete', 'batch': batch_idx + 1, 'total': len(batches)})
    
    if job_id:
        complete_job(job_id, results['valid'], results['invalid'], results['error'])
    
    return results