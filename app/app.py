from datetime import datetime
import re
import secrets
import threading
import time

from flask import Flask, abort, redirect, render_template, request, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'timer_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# 部屋ごとのタイマー状態。現在の構成は単一プロセスでの利用を想定する。
ROOM_IDLE_TIMEOUT = 60 * 60
ROOM_CLEANUP_INTERVAL = 60
MAX_TIMER_DURATION = 24 * 60 * 60
ROOM_ID_PATTERN = re.compile(r'^[0-9a-f]{16}$')
rooms = {}
rooms_lock = threading.RLock()


def new_room_state():
    """新しい部屋の初期状態を作成する。"""
    return {
        'is_running': False,
        'start_time': None,
        'duration': 0,
        'remaining_time': 0,
        'last_activity': datetime.now(),
        'connected_clients': 0,
    }


def create_room():
    """新しい共有タイマー部屋を作成してIDを返す。"""
    room_id = secrets.token_hex(8)
    with rooms_lock:
        rooms[room_id] = new_room_state()
    return room_id


def cleanup_rooms(now=None):
    """一定時間使われていない停止済み・未接続の部屋を削除する。"""
    now = now or datetime.now()
    with rooms_lock:
        stale_room_ids = [
            room_id
            for room_id, state in rooms.items()
            if not state['is_running']
            and state['connected_clients'] == 0
            and (now - state['last_activity']).total_seconds() > ROOM_IDLE_TIMEOUT
        ]
        for room_id in stale_room_ids:
            del rooms[room_id]
    return stale_room_ids


def room_update(state):
    """クライアントへ送るタイマー状態を作成する。"""
    return {
        'remaining_time': state['remaining_time'],
        'is_running': state['is_running'],
    }


def current_room_id():
    room_id = request.args.get('room_id')
    if room_id and ROOM_ID_PATTERN.fullmatch(room_id):
        return room_id
    return None


def parse_duration(data):
    """入力値を検証し、秒数に変換する。不正値はNoneを返す。"""
    try:
        minutes = int(data.get('minutes', 0))
        seconds = int(data.get('seconds', 0))
    except (TypeError, ValueError, AttributeError):
        return None

    if minutes < 0 or seconds < 0 or seconds > 59:
        return None

    duration = minutes * 60 + seconds
    if duration <= 0 or duration > MAX_TIMER_DURATION:
        return None
    return duration


def timer_thread():
    """バックグラウンドで部屋ごとのタイマーを管理するスレッド。"""
    last_cleanup = datetime.now()
    while True:
        updates = []
        finished_rooms = []
        now = datetime.now()

        with rooms_lock:
            for room_id, state in rooms.items():
                if state['is_running'] and state['start_time']:
                    elapsed = (now - state['start_time']).total_seconds()
                    state['remaining_time'] = max(0, state['duration'] - elapsed)
                    updates.append((room_id, room_update(state)))

                    if state['remaining_time'] <= 0:
                        state['is_running'] = False
                        state['start_time'] = None
                        state['last_activity'] = now
                        finished_rooms.append(room_id)

        if (now - last_cleanup).total_seconds() >= ROOM_CLEANUP_INTERVAL:
            cleanup_rooms(now)
            last_cleanup = now

        for room_id, update in updates:
            socketio.emit('timer_update', update, to=room_id)
        for room_id in finished_rooms:
            socketio.emit('timer_finished', to=room_id)

        time.sleep(1)


# バックグラウンドスレッドを開始
timer_bg_thread = threading.Thread(target=timer_thread, daemon=True)
timer_bg_thread.start()


@app.route('/')
def index():
    """トップページを新しい共有タイマーへ転送する。"""
    return redirect(url_for('room', room_id=create_room()))


@app.route('/room/<room_id>')
def room(room_id):
    """指定された共有タイマーを表示する。"""
    if not ROOM_ID_PATTERN.fullmatch(room_id):
        abort(404)
    with rooms_lock:
        state = rooms.get(room_id)
        if state is None:
            abort(404)
        state['last_activity'] = datetime.now()
    return render_template('index.html', room_id=room_id)


@socketio.on('connect')
def handle_connect():
    """新しいクライアントを指定された部屋へ接続する。"""
    room_id = current_room_id()
    if not room_id:
        return False

    with rooms_lock:
        state = rooms.get(room_id)
        if state is None:
            return False
        state['connected_clients'] += 1
        state['last_activity'] = datetime.now()
        state = state.copy()
    join_room(room_id)
    emit('timer_update', room_update(state))


@socketio.on('disconnect')
def handle_disconnect():
    """クライアントを共有タイマー部屋から切断する。"""
    room_id = current_room_id()
    if room_id:
        with rooms_lock:
            state = rooms.get(room_id)
            if state:
                state['connected_clients'] = max(0, state['connected_clients'] - 1)
                state['last_activity'] = datetime.now()
        leave_room(room_id)


@socketio.on('start_timer')
def handle_start_timer(data):
    """指定された部屋のタイマーを開始する。"""
    room_id = current_room_id()
    if not room_id:
        return

    duration = parse_duration(data)
    if duration is None:
        emit('timer_error', {
            'message': 'タイマーは1秒以上24時間以内で設定してください。',
        })
        return

    with rooms_lock:
        state = rooms.get(room_id)
        if state is None:
            return
        state['duration'] = duration
        state['start_time'] = datetime.now()
        state['is_running'] = True
        state['remaining_time'] = duration
        state['last_activity'] = datetime.now()
        update = room_update(state)

    socketio.emit('timer_started', {
        'duration': duration,
        **update,
    }, to=room_id)


@socketio.on('stop_timer')
def handle_stop_timer():
    """指定された部屋のタイマーを停止する。"""
    room_id = current_room_id()
    if not room_id:
        return

    with rooms_lock:
        state = rooms.get(room_id)
        if state is None:
            return
        state['is_running'] = False
        state['start_time'] = None
        state['remaining_time'] = 0
        state['last_activity'] = datetime.now()

    socketio.emit('timer_stopped', to=room_id)


@socketio.on('pause_timer')
def handle_pause_timer():
    """指定された部屋のタイマーを一時停止する。"""
    room_id = current_room_id()
    if not room_id:
        return

    with rooms_lock:
        state = rooms.get(room_id)
        if state is None:
            return
        if not state['is_running']:
            return

        elapsed = (datetime.now() - state['start_time']).total_seconds()
        state['remaining_time'] = max(0, state['duration'] - elapsed)
        state['is_running'] = False
        state['start_time'] = None
        state['last_activity'] = datetime.now()
        remaining_time = state['remaining_time']

    socketio.emit('timer_paused', {
        'remaining_time': remaining_time,
    }, to=room_id)


@socketio.on('resume_timer')
def handle_resume_timer():
    """指定された部屋のタイマーを再開する。"""
    room_id = current_room_id()
    if not room_id:
        return

    with rooms_lock:
        state = rooms.get(room_id)
        if state is None:
            return
        if state['is_running'] or state['remaining_time'] <= 0:
            return

        state['duration'] = state['remaining_time']
        state['start_time'] = datetime.now()
        state['is_running'] = True
        state['last_activity'] = datetime.now()
        remaining_time = state['remaining_time']

    socketio.emit('timer_resumed', {
        'remaining_time': remaining_time,
    }, to=room_id)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8000, debug=False, allow_unsafe_werkzeug=True)
