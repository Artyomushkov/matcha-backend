import time
import uuid
from notification.entities import Notification
from notification import bp
from utils.utils import check_and_clean_fields, is_valid_uuid
from flask import request, jsonify
from lib_db.insert import insert_query
from profile.profile_entities import ProfileType
from profile.profile_common import find_profile_by_id
from lib_db.select import select_for_chat
from profile.exceptions import NotFoundError

TABLE_NAME = "notification"

@bp.route('/<page>', methods=['GET'])
def get_notifications(page):
  user = request.args.get('user')
  if not is_valid_uuid(user):
    return jsonify({"error": "Invalid user id"}), 400
  try:
    find_profile_by_id(user, ProfileType.SHORT)
  except NotFoundError as err:
    return str(err), 400
  except Exception as err:
    return str(err), 500
  try:
    page = int(page) - 1
  except ValueError as err:
    return jsonify({"error": "Invalid page number"}), 400 
  try:
    notifications = select_for_chat(TABLE_NAME, "id, recipientId, actorId, type, dateCreated", {"recipientId": user}, page)
  except Exception as err:
    return jsonify({"error": "Database query failed"}), 500
  response = []
  for notification_data in notifications:
    response.append(Notification(notification_data).__dict__)
  return jsonify({'notifications' : response}), 200

#test method
@bp.route('/', methods=['POST'])
def create_notification():
  request_data = check_and_clean_fields(request.json, {'recipient', 'actor', 'type'})
  if not request_data:
    return jsonify({"error": "Not all necessary fields are in the request"}), 400
  id = str(uuid.uuid4())
  date_created = int(time.time()) * 100
  try:
    insert_query("notification", { 'id': id, 'recipientId': request_data['recipient'], 'actorId': request_data['actor'],
                                  'type': request_data['type'], 'dateCreated': date_created })
  except Exception as err:
    return jsonify({"error": "Database query failed"}), 500
  return jsonify({"id": id}), 200