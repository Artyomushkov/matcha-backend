import time
import uuid
from flask_socketio import emit, join_room, leave_room, send
import psycopg2
from lib_db.insert import insert_query
from main import socketio
from lib_db.update import update_query
from lib_db.select import select_query
from main import user_rooms
from flask import request

@socketio.on('join')
def on_join(data):
    try:
        chat = select_query('chat', 'id', {'id' : data['room']})
        if chat:
            join_room(data['room'])
        else:
            emit('error', {'msg': 'Room not found'}, to=request.sid)
    except Exception as err:
        emit('error', {'msg': str(err)}, to=request.sid)

@socketio.on('leave')
def on_leave(data):
    leave_room(data['room'])

@socketio.on('message')
def handle_message(data):
    print("TEST")
    print(user_rooms)
    try:
        chat = select_query('chat', 'id', {'id' : data['room']})
        if chat:
            send(data['message'], to=data['room'])
        else:
            emit('error', {'msg': 'Room not found'}, to=request.sid)
    except Exception as err:
        emit('error', {'msg': str(err)}, to=request.sid)
    psycopg2.extras.register_uuid()
    message_data = {}
    message_data['id'] = uuid.uuid4()
    message_data['chatId'] = data['room']
    message_data['authorId'] = data['authorId']
    message_data['content'] = data['message']
    message_data['dateCreated'] = int(time.time()) * 100
    try:
      insert_query('message', message_data)
    except Exception as err:
        emit('error', {'msg': str(err)}, to=request.sid)
        pass