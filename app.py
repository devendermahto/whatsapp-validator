import os
import re
from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'whatsapp-validator-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

import core
core.init_db()

active_tasks = {}
task_results = {}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        data = request.json
        api_url = data.get('api_url', '').strip()
        instance_name = data.get('instance_name', '').strip()
        api_key = data.get('api_key', '').strip()
        
        if not api_url or not instance_name or not api_key:
            return jsonify({'success': False, 'error': 'All fields are required'})
        
        core.save_api_credentials(api_url, instance_name, api_key)
        
        connected = core.check_connection(api_url, instance_name, api_key)
        if connected:
            return jsonify({'success': True, 'message': 'API connected successfully!'})
        else:
            return jsonify({'success': False, 'error': 'Could not connect to API. Check URL and credentials.'})
    
    creds = core.get_api_credentials()
    return jsonify({'credentials': creds})


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
    task_id = str(threading.get_ident())
    active_tasks[task_id] = True
    task_results[task_id] = {'valid': [], 'invalid': [], 'error': [], 'total': len(numbers), 'processed': 0}
    
    def progress_callback(result):
        if result.get('type') == 'batch_complete':
            socketio.emit('batch_complete', result, room=request.sid)
            return
        
        task_results[task_id][result['status']].append(result['number'])
        task_results[task_id]['processed'] += 1
        socketio.emit('progress', {
            'processed': task_results[task_id]['processed'],
            'total': task_results[task_id]['total'],
            'current': result
        }, room=request.sid)
    
    def run_validation():
        creds = core.get_api_credentials()
        try:
            results = core.process_numbers(
                numbers, 
                creds['api_url'], 
                creds['instance_name'], 
                creds['api_key'],
                progress_callback
            )
            task_results[task_id].update(results)
        except Exception as e:
            task_results[task_id]['error_msg'] = str(e)
        finally:
            active_tasks[task_id] = False
            socketio.emit('complete', task_results[task_id], room=request.sid)
    
    thread = threading.Thread(target=run_validation)
    thread.start()
    
    return jsonify({'success': True, 'task_id': task_id, 'total': len(numbers)})


@app.route('/api/results/<task_id>')
def get_results(task_id):
    if task_id in task_results:
        return jsonify({'results': task_results[task_id]})
    return jsonify({'error': 'Task not found'})


@app.route('/api/download/<task_id>')
def download_results(task_id):
    if task_id not in task_results:
        return jsonify({'error': 'Task not found'})
    
    results = task_results[task_id]
    content = []
    content.append("=== WhatsApp Validator Results ===\n")
    content.append(f"Total: {results.get('total', 0)}\n")
    content.append(f"Valid: {len(results.get('valid', []))}\n")
    content.append(f"Invalid: {len(results.get('invalid', []))}\n")
    content.append(f"Error: {len(results.get('error', []))}\n")
    content.append("\n=== Invalid Numbers ===\n")
    content.extend(results.get('invalid', []))
    content.append("\n=== Error Numbers ===\n")
    content.extend(results.get('error', []))
    
    filename = f"results_{task_id}.txt"
    filepath = os.path.join(os.path.dirname(__file__), filename)
    with open(filepath, 'w') as f:
        f.write('\n'.join(content))
    
    return send_file(filepath, as_attachment=True, download_name=f"whatsapp_results_{task_id}.txt")


if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)