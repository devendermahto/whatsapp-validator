import os
import re
import uuid
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from flask_socketio import SocketIO, emit
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'whatsapp-validator-secret-key-change-in-production'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

import core
core.init_db()

active_tasks = {}


@app.route('/')
def index():
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        creds = core.get_api_credentials()
        if creds and creds.get('username'):
            if core.verify_user(username, password):
                session['authenticated'] = True
                session['username'] = username
                return redirect(url_for('index'))
            else:
                return render_template('login.html', error='Invalid credentials')
        else:
            if username == 'admin' and password == 'admin123':
                core.save_user_auth(username, password)
                session['authenticated'] = True
                session['username'] = username
                return redirect(url_for('index'))
            return render_template('login.html', error='Setup your account first')
    
    creds = core.get_api_credentials()
    if creds and creds.get('username'):
        return render_template('login.html')
    return render_template('login.html', setup=True)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/api/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        data = request.json
        api_url = data.get('api_url', '').strip()
        instance_name = data.get('instance_name', '').strip()
        api_key = data.get('api_key', '').strip()
        
        if data.get('username') and data.get('password'):
            core.save_user_auth(data['username'], data['password'])
        
        if not api_url or not instance_name or not api_key:
            return jsonify({'success': False, 'error': 'All fields are required'})
        
        core.save_api_credentials(api_url, instance_name, api_key)
        
        connected = core.check_connection(api_url, instance_name, api_key)
        if connected:
            return jsonify({'success': True, 'message': 'API connected successfully!'})
        else:
            return jsonify({'success': False, 'error': 'Could not connect to API. Check URL and credentials.'})
    
    creds = core.get_api_credentials()
    jobs = core.get_jobs(20)
    return jsonify({'credentials': creds, 'jobs': jobs})


@app.route('/api/jobs')
def get_all_jobs():
    jobs = core.get_jobs(50)
    return jsonify({'jobs': jobs})


@app.route('/api/job/<job_id>')
def get_job_details(job_id):
    job = core.get_job(job_id)
    if job:
        return jsonify({'job': job})
    return jsonify({'error': 'Job not found'}), 404


@app.route('/api/check-connection')
def check_connection():
    creds = core.get_api_credentials()
    if not creds or not creds.get('api_url'):
        return jsonify({'connected': False, 'message': 'API not configured'})
    
    connected = core.check_connection(creds['api_url'], creds['instance_name'], creds['api_key'])
    return jsonify({'connected': connected})


@app.route('/api/validate', methods=['POST'])
def validate():
    data = request.json
    text = data.get('text', '')
    
    numbers = re.findall(r'\d{10,15}', text)
    if not numbers:
        return jsonify({'success': False, 'error': 'No valid numbers found (10-15 digits)'})
    
    numbers = list(set(numbers))
    job_id = str(uuid.uuid4())[:8]
    
    core.create_job(job_id, len(numbers))
    active_tasks[job_id] = True
    
    def progress_callback(result):
        if result.get('type') == 'batch_complete':
            socketio.emit('batch_complete', result)
            return
        
        socketio.emit('progress', {
            'job_id': job_id,
            'status': result.get('status'),
            'number': result.get('number'),
            'emoji': result.get('emoji')
        })
    
    def run_validation():
        creds = core.get_api_credentials()
        try:
            core.process_numbers(
                numbers, 
                creds['api_url'], 
                creds['instance_name'], 
                creds['api_key'],
                progress_callback,
                job_id
            )
        except Exception as e:
            print(f"Validation error: {e}")
        finally:
            active_tasks[job_id] = False
            socketio.emit('complete', {'job_id': job_id})
    
    thread = threading.Thread(target=run_validation)
    thread.start()
    
    return jsonify({'success': True, 'job_id': job_id, 'total': len(numbers)})


@app.route('/api/download/<job_id>')
def download_results(job_id):
    job = core.get_job(job_id)
    if not job:
        return jsonify({'error': 'Job not found'})
    
    content = []
    content.append("=== WhatsApp Validator Results ===")
    content.append(f"Job ID: {job_id}")
    content.append(f"Total: {job['total_numbers']}")
    content.append(f"Valid: {job['valid_count']}")
    content.append(f"Invalid: {job['invalid_count']}")
    content.append(f"Error: {job['error_count']}")
    content.append("")
    content.append("=== Valid Numbers ===")
    content.extend(job['valid_numbers'])
    content.append("")
    content.append("=== Invalid Numbers ===")
    content.extend(job['invalid_numbers'])
    content.append("")
    content.append("=== Error Numbers ===")
    content.extend(job['error_numbers'])
    
    filename = f"results_{job_id}.txt"
    filepath = os.path.join(os.path.dirname(__file__), filename)
    with open(filepath, 'w') as f:
        f.write('\n'.join(content))
    
    return send_file(filepath, as_attachment=True, download_name=f"whatsapp_results_{job_id}.txt")


if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000, host='0.0.0.0')