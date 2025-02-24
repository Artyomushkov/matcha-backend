import time
from flask import jsonify

import psycopg2
from profile.mail_utils import confirm_email_send
from lib_db.delete import delete_query
from lib_db.select import select_query
from lib_db.update import update_query
from passlib.hash import sha256_crypt
from lib_db.insert import insert_query
from profile.exceptions import NotFoundError, BadRequest, FatalError
from profile.profile_entities import ProfileType
from profile.profile_common import find_profile_by_id
from utils.utils import is_valid_uuid
from notification.sockets import like_notify
from chat.utils import delete_chat_on_unlike

TABLE_NAME = 'profile'

def register_user(id, request_data):
  request_data['id'] = id
  request_data['emailVerified'] = False
  request_data['password'] = sha256_crypt.encrypt(request_data['password'])
  request_data['fameRating'] = 0
  try:
    insert_query(TABLE_NAME, request_data)
  except psycopg2.errors.NotNullViolation:
    raise BadRequest("You haven't defined one of the fields")
  except psycopg2.errors.UniqueViolation as err:
    if str(err).find('username') != -1:
      raise BadRequest("Profile with this username already exists")
    elif str(err).find('email') != -1:
      raise BadRequest("Profile with this email already exists")     
    else:
      raise FatalError(str(err))
  except psycopg2.errors.StringDataRightTruncation as err:
    raise BadRequest("One of the fields is too long (more than 50 symbols)")
  except Exception as err:
    raise FatalError(str(err))
  try:
    confirm_email_send(id, request_data['email'], True)
  except Exception as err:
    print(err)
    delete_query(TABLE_NAME, {'id': id})
    raise FatalError("sending email error")
  
def add_views_to_db(id, guest_id, profile):
  fields_needed = "viewed"
  viewed = select_query(TABLE_NAME, fields_needed, {'id': guest_id})
  print(viewed)
  print('1')
  if not viewed:
    raise NotFoundError("There is no user with such id")
  if id not in viewed[0][0]:
    print('2')
    update_query(TABLE_NAME, {'viewed': viewed[0][0] + [id]}, {'id': guest_id})
    print('21')
  if guest_id not in profile.viewedMe:
    print('3')
    update_query(TABLE_NAME, {'viewedMe': profile.viewedMe + [guest_id]}, {'id': id})
    print('31')

# Need to add a check for dateofbirth limits
def check_edit_data(id, request_data):
    if not is_valid_uuid(id):
        raise TypeError("Wrong ID format")
    if not isinstance(request_data['firstName'], str):
        raise TypeError("First name should be a string")
    if not isinstance(request_data['lastName'], str):
        raise TypeError("Last name should be a string")
    if len(request_data['firstName']) > 50 or len(request_data['lastName']) > 50:
        raise TypeError("First name or last name is too long")
    if not isinstance(request_data['tagList'], list):
        raise TypeError("TagList should be an array")
    if len(request_data['tagList']) > 10:
        raise TypeError("Too many tags")
    if not isinstance(request_data['pictures'], list):
        raise TypeError("Pictures should be an array")
    if len(request_data['pictures']) > 8:
        raise TypeError("Too many pictures")
    if not isinstance(request_data['dateOfBirth'], int):
        raise TypeError("dateOfBirth should be a number")
    if not isinstance(request_data['biography'], str):
        raise TypeError("Biography should be a string")
    if len(request_data['biography']) > 250:
        raise TypeError("Biography is too long")
    lat = request_data['location'].get('lat')
    lon = request_data['location'].get('lon')
    if isinstance(lat, str) or isinstance(lat, str):
      raise TypeError("Coordinates should be numbers")
    request_data['GPSlat'] = float(lat)
    request_data['GPSlon'] = float(lon)
    if request_data['GPSlat'] < -90 or request_data['GPSlat'] > 90:
      raise TypeError("Latitude is out of range")
    if request_data['GPSlon'] < -180 or request_data['GPSlon'] > 180:
      raise TypeError("Longitude is out of range")
    request_data.pop('location')
    gender = request_data['gender']
    if gender != "male" and gender != "female" and gender != "other":
      raise TypeError("There is no such type of gender")
    sex_pref = request_data['sexPref']
    if sex_pref != "men" and sex_pref != "women" and sex_pref != "both":
      raise TypeError("Type of sex preference is unavailable")
    request_data['isOnline'] = True
    request_data['lastSeen'] = int(time.time())
    find_profile_by_id(id, ProfileType.SHORT)
    return request_data

def like_unlike(id, guest_id, liked, liked_me, if_like):
  if if_like:
    if id not in liked:
      try:
        update_query(TABLE_NAME, {'liked': liked + [id]}, {'id': guest_id})
      except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    else:
        return jsonify({"error": "The user is already liked"}), 400
    if guest_id not in liked_me:
      try:
        update_query(TABLE_NAME, {'likedMe': liked_me + [guest_id]}, {'id': id})
      except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
  else:
    if id in liked:
      try:
        liked.remove(id)
        update_query(TABLE_NAME, {'liked': liked}, {'id': guest_id})
      except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    else:
        return jsonify({"error": "The user is already not liked"}), 400
    if guest_id in liked_me:
      try:
        liked_me.remove(guest_id)
        update_query(TABLE_NAME, {'likedMe': liked_me}, {'id': id})
      except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    try:
      delete_chat_on_unlike(id, guest_id)
    except Exception as err:
       return jsonify("Error while deleting chat"), 500
  try:
    like_notify(id, guest_id, if_like)
  except Exception as err:
    print(err)
    pass     
  return jsonify({'liker': guest_id}), 200
