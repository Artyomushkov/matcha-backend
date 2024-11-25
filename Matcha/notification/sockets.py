import time
import uuid
from flask_socketio import emit
from profile.profile_entities import ProfileType
from profile.profile_common import find_profile_by_id
from main import user_rooms
from main import socketio
from lib_db.insert import insert_query
from lib_db.select import select_query

def like_notify(user_id, guest_id, if_like):
  try:
    actor = find_profile_by_id(guest_id, ProfileType.SHORT)
  except Exception as err:
    emit('error', {'msg': str(err)}, room=user_rooms[user_id])
    return
  type = 'like' if if_like else 'unlike'
  try:
    fields_needed = "liked"
    liked_by_user = select_query('profile', fields_needed, {'id': user_id})
    if if_like:
      if guest_id in liked_by_user[0][0]:
        type = 'match'
        emit('notification', {'actor': actor.__dict__, 'type': type}, namespace='/', to=user_rooms[user_id])
      else:
        emit('notification', {'actor': actor.__dict__, 'type': type}, namespace='/', to=user_rooms[user_id])
    else:
      if guest_id in liked_by_user[0][0]:
        emit('notification', {'actor': actor.__dict__, 'type': type}, namespace='/', to=user_rooms[user_id])
  except Exception as err:
    emit('error', {'msg': str(err)}, room=user_rooms[user_id])
    pass
  notification_id = str(uuid.uuid4())
  date_created = int(time.time()) * 100
  try:
    insert_query("notification", { 'id': notification_id, 'recipientId': user_id, 'actorId': guest_id,
                                    'type': type, 'dateCreated': date_created })
  except Exception as err:
    emit('error', {'msg': str(err)}, room=user_rooms[user_id])
    return
  
def view_notify(user_id, guest_id):
  try:
    actor = find_profile_by_id(guest_id, ProfileType.SHORT)
  except Exception as err:
    emit('error', {'msg': str(err)}, room=user_rooms[user_id])
    return
  emit('notification', {'actor': actor.__dict__, 'type': 'view'}, namespace='/', to=user_rooms[user_id])
  notification_id = str(uuid.uuid4())
  date_created = int(time.time()) * 100
  try:
    insert_query("notification", { 'id': notification_id, 'recipientId': user_id, 'actorId': guest_id,
                                  'type': 'view', 'dateCreated': date_created })
  except Exception as err:
    emit('error', {'msg': str(err)}, room=user_rooms[user_id])
    return