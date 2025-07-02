from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import threading
import time
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'timer_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# タイマーの状態を管理するグローバル変数
timer_state = {
    'is_running': False,
    'start_time': None,
    'duration': 0,  # 秒
    'remaining_time': 0
}

def timer_thread():
    """バックグラウンドでタイマーを管理するスレッド"""
    while True:
        if timer_state['is_running'] and timer_state['start_time']:
            elapsed = (datetime.now() - timer_state['start_time']).total_seconds()
            remaining = max(0, timer_state['duration'] - elapsed)
            timer_state['remaining_time'] = remaining
            
            # 全クライアントにタイマー状態を送信
            socketio.emit('timer_update', {
                'remaining_time': remaining,
                'is_running': timer_state['is_running']
            })
            
            # タイマー終了チェック
            if remaining <= 0 and timer_state['is_running']:
                timer_state['is_running'] = False
                socketio.emit('timer_finished')
        
        time.sleep(1)

# バックグラウンドスレッドを開始
timer_bg_thread = threading.Thread(target=timer_thread, daemon=True)
timer_bg_thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    """新しいクライアントが接続した時"""
    print('Client connected')
    # 現在のタイマー状態を新しいクライアントに送信
    emit('timer_update', {
        'remaining_time': timer_state['remaining_time'],
        'is_running': timer_state['is_running']
    })

@socketio.on('disconnect')
def handle_disconnect():
    """クライアントが切断した時"""
    print('Client disconnected')

@socketio.on('start_timer')
def handle_start_timer(data):
    """タイマー開始"""
    minutes = int(data.get('minutes', 0))
    seconds = int(data.get('seconds', 0))
    
    timer_state['duration'] = minutes * 60 + seconds
    timer_state['start_time'] = datetime.now()
    timer_state['is_running'] = True
    timer_state['remaining_time'] = timer_state['duration']
    
    # 全クライアントにタイマー開始を通知
    socketio.emit('timer_started', {
        'duration': timer_state['duration'],
        'remaining_time': timer_state['remaining_time']
    })

@socketio.on('stop_timer')
def handle_stop_timer():
    """タイマー停止"""
    timer_state['is_running'] = False
    timer_state['start_time'] = None
    timer_state['remaining_time'] = 0
    
    # 全クライアントにタイマー停止を通知
    socketio.emit('timer_stopped')

@socketio.on('pause_timer')
def handle_pause_timer():
    """タイマー一時停止"""
    if timer_state['is_running']:
        elapsed = (datetime.now() - timer_state['start_time']).total_seconds()
        timer_state['remaining_time'] = max(0, timer_state['duration'] - elapsed)
        timer_state['is_running'] = False
        timer_state['start_time'] = None
        
        # 全クライアントにタイマー一時停止を通知
        socketio.emit('timer_paused', {
            'remaining_time': timer_state['remaining_time']
        })

@socketio.on('resume_timer')
def handle_resume_timer():
    """タイマー再開"""
    if not timer_state['is_running'] and timer_state['remaining_time'] > 0:
        timer_state['duration'] = timer_state['remaining_time']
        timer_state['start_time'] = datetime.now()
        timer_state['is_running'] = True
        
        # 全クライアントにタイマー再開を通知
        socketio.emit('timer_resumed', {
            'remaining_time': timer_state['remaining_time']
        })

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8000, debug=False, allow_unsafe_werkzeug=True)
