import time
from flask_socketio import emit
from main import socketio
from lib_db.update import update_query
from flask import request
from main import user_rooms

@socketio.on('register')
def change_status_to_online(data):
    if not data:
        return
    if not data['id']:
        return
    user_rooms[data['id']] = request.sid
    try:
        update_query('profile', {'isOnline': True}, {'id': data['id']})
    except Exception as e:
        emit('error', {'msg': str(e)}, room=request.sid) 

@socketio.on('disconnect')
def disconnect():
    for id, sid in user_rooms.items():
        if sid == request.sid:
            del user_rooms[id]
            try:
                timeNow = int(time.time()) * 100
                update_query('profile', {'isOnline': False, 'lastSeen': timeNow }, {'id': id })
            except Exception as e:
                print(str(e))
            finally: 
                break
