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
            username TEXT,
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
            country_code TEXT DEFAULT '91',
            total_numbers INTEGER DEFAULT 0,
            valid_count INTEGER DEFAULT 0,
            invalid_count INTEGER DEFAULT 0,
            error_count INTEGER DEFAULT 0,
            skipped_count INTEGER DEFAULT 0,
            processed_count INTEGER DEFAULT 0,
            valid_numbers TEXT,
            invalid_numbers TEXT,
            error_numbers TEXT,
            skipped_numbers TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def normalize_number(phone, country_code):
    """
    Normalize phone number based on selected country code.
    Returns (normalized_number, status)
    - status: 'valid_format' | 'skipped' | 'error'
    """
    digits = re.sub(r'\D', '', phone)
    
    if not digits:
        return phone, 'error'
    
    if digits.startswith(country_code):
        return digits, 'valid_format'
    
    if len(digits) > 10:
        first_two = digits[:2]
        if first_two in ['91', '1', '44', '92', '971', '966', '20', '234', '254', '880', '973', '965', '968', '973', '212']:
            return digits, 'skipped'
        return digits, 'valid_format'
    
    if len(digits) >= 8 and len(digits) <= 10:
        return country_code + digits, 'valid_format'
    
    return digits, 'error'


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
        SELECT id, status, country_code, total_numbers, valid_count, invalid_count, error_count,
               skipped_count, processed_count, created_at, completed_at
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
            'country_code': row[2],
            'total_numbers': row[3],
            'valid_count': row[4],
            'invalid_count': row[5],
            'error_count': row[6],
            'skipped_count': row[7],
            'processed_count': row[8],
            'created_at': row[9],
            'completed_at': row[10]
        })
    return jobs


def get_job(job_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, status, country_code, total_numbers, valid_count, invalid_count, error_count,
               skipped_count, processed_count, valid_numbers, invalid_numbers, error_numbers,
               skipped_numbers, created_at, completed_at
        FROM jobs WHERE id = ?
    """, (job_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            'id': row[0],
            'status': row[1],
            'country_code': row[2],
            'total_numbers': row[3],
            'valid_count': row[4],
            'invalid_count': row[5],
            'error_count': row[6],
            'skipped_count': row[7],
            'processed_count': row[8],
            'valid_numbers': row[9].split(',') if row[9] else [],
            'invalid_numbers': row[10].split(',') if row[10] else [],
            'error_numbers': row[11].split(',') if row[11] else [],
            'skipped_numbers': row[12].split(',') if row[12] else [],
            'created_at': row[13],
            'completed_at': row[14]
        }
    return None


def create_job(job_id, total, country_code='91'):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO jobs (id, status, country_code, total_numbers, processed_count)
        VALUES (?, 'processing', ?, ?, 0)
    """, (job_id, country_code, total))
    conn.commit()
    conn.close()


def update_job_progress(job_id, valid, invalid, error, skipped=0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE jobs SET valid_count = ?, invalid_count = ?, error_count = ?, skipped_count = ? WHERE id = ?
    """, (valid, invalid, error, skipped, job_id))
    conn.commit()
    conn.close()


def update_job_status(job_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE jobs SET status = ? WHERE id = ?", (status, job_id))
    conn.commit()
    conn.close()


def delete_job(job_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()


def complete_job(job_id, valid_numbers, invalid_numbers, error_numbers, skipped_numbers):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE jobs SET
            status = 'completed',
            valid_numbers = ?,
            invalid_numbers = ?,
            error_numbers = ?,
            skipped_numbers = ?,
            completed_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (','.join(valid_numbers), ','.join(invalid_numbers), ','.join(error_numbers), ','.join(skipped_numbers), job_id))
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
        print(f"[DEBUG] Checking number: {phone_number}")
        print(f"[DEBUG] URL: {url}")
        print(f"[DEBUG] API Key: {api_key[:10]}..." if len(api_key) > 10 else f"[DEBUG] API Key: {api_key}")
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"[DEBUG] Response Status: {response.status_code}")
        print(f"[DEBUG] Response Body: {response.text[:500]}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"[DEBUG] JSON Data: {data}")
            except:
                print(f"[DEBUG] Not JSON response")
                return {'number': phone_number, 'status': 'error', 'emoji': '⏳', 'error': 'Invalid JSON response'}
            
            results = data.get('response') or data.get('data') or []
            if results and isinstance(results, list) and len(results) > 0:
                exists = results[0].get('exists', False)
                print(f"[DEBUG] exists: {exists}")
                if exists:
                    return {'number': phone_number, 'status': 'valid', 'emoji': '✅'}
                else:
                    return {'number': phone_number, 'status': 'invalid', 'emoji': '⛔️'}
            else:
                print(f"[DEBUG] No results or unexpected format")
                return {'number': phone_number, 'status': 'error', 'emoji': '⏳', 'error': 'No results in response'}
        
        elif response.status_code == 401:
            print(f"[DEBUG] Unauthorized - Invalid API Key")
            return {'number': phone_number, 'status': 'error', 'emoji': '⏳', 'error': 'Invalid API Key'}
        elif response.status_code == 404:
            print(f"[DEBUG] Not Found - Instance not found")
            return {'number': phone_number, 'status': 'error', 'emoji': '⏳', 'error': 'Instance not found'}
        else:
            print(f"[DEBUG] HTTP Error: {response.status_code}")
            return {'number': phone_number, 'status': 'error', 'emoji': '⏳', 'error': f'HTTP {response.status_code}'}
            
    except requests.exceptions.Timeout:
        print(f"[DEBUG] Timeout for number: {phone_number}")
        return {'number': phone_number, 'status': 'error', 'emoji': '⏳', 'error': 'Timeout'}
    except requests.exceptions.ConnectionError as e:
        print(f"[DEBUG] Connection Error: {e}")
        return {'number': phone_number, 'status': 'error', 'emoji': '⏳', 'error': 'Connection failed'}
    except Exception as e:
        print(f"[DEBUG] Exception: {e}")
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


def process_numbers(numbers, api_url, instance_name, api_key, country_code='91', progress_callback=None, job_id=None):
    results = {'valid': [], 'invalid': [], 'error': [], 'skipped': []}
    processed_numbers = []
    
    normalized_numbers = []
    for num in numbers:
        normalized, status = normalize_number(num, country_code)
        if status == 'skipped':
            results['skipped'].append(num)
        elif status == 'valid_format':
            normalized_numbers.append(normalized)
        else:
            results['error'].append(num)
    
    normalized_numbers = list(set(normalized_numbers))
    batches = list(chunk_list(normalized_numbers, 50))
    
    for batch_idx, batch in enumerate(batches):
        if job_id:
            job = get_job(job_id)
            if job and job['status'] == 'stopped':
                break
            while job and job['status'] == 'paused':
                time.sleep(2)
                job = get_job(job_id)
                if job and job['status'] == 'stopped':
                    break
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {executor.submit(check_number, api_url, instance_name, api_key, num): num for num in batch}
            
            for future in as_completed(futures):
                result = future.result()
                results[result['status']].append(result['number'])
                processed_numbers.append(result['number'])
                
                if progress_callback:
                    progress_callback(result)
                
                if job_id:
                    update_job_progress(
                        job_id, 
                        len(results['valid']), 
                        len(results['invalid']), 
                        len(results['error']),
                        len(results['skipped'])
                    )
                
                time.sleep(random.uniform(2.5, 5.5))
        
        if batch_idx < len(batches) - 1:
            time.sleep(180)
            if progress_callback:
                progress_callback({'type': 'batch_complete', 'batch': batch_idx + 1, 'total': len(batches)})
    
    if job_id:
        job = get_job(job_id)
        if job and job['status'] != 'stopped':
            complete_job(job_id, results['valid'], results['invalid'], results['error'], results['skipped'])
    
    return results
