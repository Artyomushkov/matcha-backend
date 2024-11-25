import time
import uuid
from flask import jsonify, request
import psycopg2
from profile.profile_entities import ProfileType
from profile.profile_common import find_profile_by_id
from chat import bp
from utils.utils import is_valid_uuid, check_and_clean_fields
from lib_db.select import select_for_chat, select_query
from lib_db.insert import insert_query
from profile.exceptions import NotFoundError
from chat.utils import get_chat_dto

@bp.route('/', methods=['POST'])
def create_chat():
  request_data = check_and_clean_fields(request.json, {'user1', 'user2'})
  if not request_data:
    return jsonify({"error": "Not all necessary fields are in the request"}), 400
  if not is_valid_uuid(request_data['user1']) or not is_valid_uuid(request_data['user2']):
    return jsonify({"error": "Wrong user id format"}), 400
  if request_data['user1'] == request_data['user2']:
    return jsonify({"error": "You can't have chat with yourself"}), 400
  try:
    user1 = find_profile_by_id(request_data['user1'], ProfileType.USUAL)
    user2 = find_profile_by_id(request_data['user2'], ProfileType.USUAL)
  except NotFoundError as err:
    return str(err), 400
  except Exception as err:
    return str(err), 500
  if user1.id not in user2.likedMe or user2.id not in user1.likedMe:
    return jsonify({"error": "You can't have chat without match"}), 400
  psycopg2.extras.register_uuid()
  table_name = "chat"
  fields_needed = "id"
  condition_args_first = { 'userOneId': request_data['user1'], 'userTwoId': request_data['user2'] }
  condition_args_second = { 'userOneId': request_data['user2'], 'userTwoId': request_data['user1'] }
  try:
    chat_one = select_query(table_name, fields_needed, condition_args_first)
    chat_two = select_query(table_name, fields_needed, condition_args_second)
  except Exception as err:
    return jsonify({"error": "Database query failed"}), 500
  if len(chat_one) != 0:
    return chat_one[0][0], 200
  if len(chat_two) != 0:
    return chat_two[0][0], 200
  new_chat = {}
  new_chat['id'] = uuid.uuid4()
  new_chat['userOneId'] = request_data['user1']
  new_chat['userTwoId'] = request_data['user2']
  new_chat['dateCreated'] = int(time.time()) * 100
  try:
    insert_query(table_name, new_chat)
  except Exception as err:
    return jsonify({"error": "Database query failed"}), 500
  return jsonify({"id": new_chat['id']}), 200

@bp.route('/<page>', methods=['GET'])
def get_users_chats(page):
  user = request.args.get('user')
  if user == None:
    return jsonify({"error": "There is no user id provided"}), 400
  if not is_valid_uuid(user):
    return jsonify({"error": "Wrong user id format"}), 400
  try:
    page = int(page)
  except ValueError:
    return jsonify({"error": "Wrong page format"}), 400
  table_name = "chat"
  fields_needed = "id, userOneId, userTwoId, dateCreated"
  condition_args = {'userOneId': user, 'userTwoId': user}
  try:
    chats = select_for_chat(table_name, fields_needed, condition_args, page - 1)
  except Exception as err:
    return jsonify({"error": "Database query failed"}), 500
  response = []
  try:
    for chat in chats:
      chat_dto = get_chat_dto(chat, user)
      response.append(chat_dto)
  except NotFoundError as err:
    return str(err), 400
  except Exception as err:
    return str(err), 500
  return jsonify(response), 200

@bp.route('/<id>/messages/<page>', methods=['GET'])
def get_messages(id, page):
  if not is_valid_uuid(id):
    return jsonify({"error": "Wrong chat id format"}), 400
  try:
    chat = select_query("chat", "id, userOneId, userTwoId", {'id': id})
  except Exception as err:
    return jsonify({"error": "Database query failed"}), 500
  if len(chat) == 0:
    return jsonify({"error": "Chat doesn't exist"}), 400
  user_id = request.args.get('user')
  if user_id == None:
    return jsonify({"error": "There is no user id provided"}), 400
  if user_id != str(chat[0][1]) and user_id != str(chat[0][2]):
    return jsonify({"error": "User is not a member of this chat"}), 400
  table_name = "message"
  fields_needed = "id, chatId, authorId, content"
  try:
    messages = select_for_chat(table_name, fields_needed, {'chatId': id}, int(page) - 1)
  except Exception as err:
    return jsonify({"error": "Database query failed"}), 500
  response = []
  try:
    response.append(get_chat_dto(chat[0], user_id))
  except NotFoundError as err:
    return str(err), 400
  except Exception as err:
    return str(err), 500
  print(response)
  for message in messages:
    message_dto = {}
    message_dto['id'] = message[0]
    message_dto['chatId'] = message[1]
    message_dto['authorId'] = message[2]
    message_dto['text'] = message[3]
    response.append(message_dto)
  return jsonify(response), 200

#test method
@bp.route('/<id>/messages', methods=['POST'])
def send_message(id):
  if not is_valid_uuid(id):
    return jsonify({"error": "Wrong chat id format"}), 400
  request_data = check_and_clean_fields(request.json, {'authorId', 'content'})
  if not request_data:
    return jsonify({"error": "Not all necessary fields are in the request"}), 400
  try:
    chat = select_query("chat", "id, userOneId, userTwoId", {'id': id})
  except Exception as err:
    return jsonify({"error": "Database query failed"}), 500
  if len(chat) == 0:
    return jsonify({"error": "Chat doesn't exist"}), 400
  if str(chat[0][1]) != str(request_data['authorId']) and str(chat[0][2]) != str(request_data['authorId']):
    return jsonify({"error": "AuthorID is not a member of this chat"}), 400
  try:
    find_profile_by_id(request_data['authorId'], ProfileType.SHORT)
  except NotFoundError as err:
    return str(err), 400
  except Exception as err:
    return str(err), 500
  psycopg2.extras.register_uuid()
  request_data['id'] = uuid.uuid4()
  request_data['chatId'] = id
  request_data['dateCreated'] = int(time.time()) * 100
  table_name = "message"
  try:
    insert_query(table_name, request_data)
  except Exception as err:
    return jsonify({"error": "Database query failed"}), 500
  return jsonify({"id": request_data['id']}), 200