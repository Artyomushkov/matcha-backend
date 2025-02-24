import time
import uuid
from flask_socketio import emit, join_room, leave_room, send
import psycopg2
from lib_db.insert import insert_query
from main import socketio
from lib_db.update import update_query
from lib_db.select import select_query
from profile.profile_entities import ProfileType
from profile.profile_common import find_profile_by_id
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
    try:
        chat = select_query('chat', 'id', {'id' : data['room']})
        if chat:
            send(data['message'], to=data['room'])
            if data['recipientId'] in user_rooms:
                actor = find_profile_by_id(data['authorId'], ProfileType.SHORT)
                actor.id = str(actor.id)
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