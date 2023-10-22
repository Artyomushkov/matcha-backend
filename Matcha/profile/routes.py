import time
from passlib.hash import sha256_crypt

from flask import (
    Response, current_app, flash, g, redirect, render_template, request, session, url_for, jsonify
)
from lib_db.insert import insert_query
from lib_db.select import select_query
from lib_db.update import update_query
from utils.mail_utils import send_email
from profile import bp

from lib_db.db import get_db
import uuid
import psycopg2.extras
from profile.exceptions import NotFoundError
from profile.profile_utils import ProfileType, confirm_email_send, confirm_token, find_profile_by_id, generate_token, send_reset_password, check_post_fields
from profile.short_profile_entity import ShortProfile

from utils.utils import is_valid_uuid

TABLE_NAME = 'profile'

@bp.route('/register', methods=['POST'])
def register():
    if not check_post_fields(request.json, {'username', 'password', 'firstName', 'lastName', 'email'}):
        return jsonify({"error": "Not all necessary fields are in the request"}), 400
    psycopg2.extras.register_uuid()
    id = uuid.uuid4()
    request.json['id'] = id
    request.json['emailVerified'] = False
    request.json['password'] = sha256_crypt.encrypt(request.json['password'])
    request.json['fameRating'] = 0
    try:
        insert_query(TABLE_NAME, request.json)
    except psycopg2.errors.NotNullViolation:
        return jsonify({"error": "You haven't defined one of the fields"}), 400
    except psycopg2.errors.UniqueViolation as err:
        message = "undefined error"
        str_err = str(err)
        if str_err.find('username') != -1:
            message = "Profile with this username already exists"
        elif str_err.find('email') != -1:
            message = "Profile with this email already exists"     
        return message, 400
    except psycopg2.errors.StringDataRightTruncation as err:
        return jsonify({"error": "One of the fields is too long (more than 50 symbols)"}), 400
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    try:
        confirm_email_send(request.json['email'])
    except Exception as err:
        return jsonify({"error": "Email sending failed"}), 500
    return jsonify({'id': id}), 201

@bp.route('/id/<id>', methods = ['GET'])
def find_by_id(id):
    user_id = request.args.get('user')
    if user_id == None:
        return jsonify({"error": "There is no user id provided"}), 400
    if not is_valid_uuid(user_id):
        return jsonify({"error": "Wrong user id format"}), 400
    if not is_valid_uuid(id):
        return jsonify({"error": "Wrong id format"}), 400
    fields_needed = "viewed"
    condition_args = dict()
    condition_args['id'] = user_id
    try:
        viewed = select_query(TABLE_NAME, fields_needed, condition_args)
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    if not viewed:
        return jsonify({"error": "There is no user with such id"}), 400
    try:
        profile = find_profile_by_id(id, ProfileType.USUAL)
    except NotFoundError as err:
        return str(err), 400
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    if id not in viewed[0][0]:
        try:
            update_query(TABLE_NAME, {'viewed': viewed[0][0] + [id]}, {'id': user_id})
        except Exception as err:
            return jsonify({"error": "Database query failed"}), 500
    if user_id not in profile.viewedMe:
        try:
            update_query(TABLE_NAME, {'viewedMe': profile.viewedMe + [user_id]}, {'id': id})
        except Exception as err:
            return jsonify({"error": "Database query failed"}), 500
        profile.viewedMe.append(user_id)
    return jsonify(profile.__dict__), 200

@bp.route('/login', methods=['POST'])
def login():
    if not check_post_fields(request.json, {'username', 'password'}):
        return jsonify({"error": "Not all necessary fields are in the request"}), 400
    fields_needed = "id, firstName, lastName, mainImage, isOnline, lastSeen, password"
    condition_args = dict()
    condition_args['username'] = request.json['username']
    try:
        profile = select_query(TABLE_NAME, fields_needed, condition_args)
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    if not profile:
        return jsonify({"error": "There is no user with such username"}), 400
    if sha256_crypt.verify(request.json['password'], profile[0][6]):
        return jsonify(ShortProfile(profile[0]).__dict__), 200
    else:
        return jsonify({"error": "Password is wrong"}), 401
    
@bp.route('/edit', methods = ['PUT'])
def edit():
    if not check_post_fields(request.json, {'id', 'firstName', 'lastName', 'dateOfBirth', 'biography', 'tagList', 'mainImage', 'location'}):
        return jsonify({"error": "Not all necessary fields are in the request"}), 400
    if not isinstance(request.json['tagList'], list):
        return jsonify({"error": "TagList should be an array"}), 400
    if 'pictures' in request.json and not isinstance(request.json['pictures'], list):
        return jsonify({"error": "Pictures should be an array"}), 400
    if not isinstance(request.json['dateOfBirth'], int):
        return jsonify({"error": "dateOfBirth should be a number"}), 400
    try:
        lat = request.json['location']['lat']
        lon = request.json['location']['lon']
        if isinstance(lat, str) or isinstance(lat, str):
            raise TypeError("Coordinates should be numbers")
        request.json['GPSlat'] = float(lat)
        request.json['GPSlon'] = float(lon)
        request.json.pop('location')
    except Exception as err:
        return jsonify({"error": str(err)}), 400
    try:
        gender = request.json['gender']
        if gender != "male" and gender != "female" and gender != "other":
            raise TypeError("There is no such type of gender")
        sex_pref = request.json['sexPref']
        if sex_pref != "men" and sex_pref != "women" and sex_pref != "both":
            raise TypeError("Type of sex preference is unavailable")
    except TypeError as err:
        return jsonify({"error": str(err)}), 400
    except Exception as err:
        return jsonify({"error": "There is no gender or sex pref in request"}), 400
    condition_args = dict()
    request.json['isOnline'] = True
    request.json['lastSeen'] = int(time.time())
    try:
        person_req = find_profile_by_id(request.json['id'], ProfileType.SHORT)
        condition_args['id'] = request.json['id']
        request.json.pop('id')
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 400
    except Exception as err:
        return jsonify({"error": str(err)}), 500
    try:
        update_query(TABLE_NAME, request.json, condition_args)
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    fullProfile = find_profile_by_id(condition_args['id'], ProfileType.FULL)
    return jsonify(fullProfile.__dict__), 201

@bp.route('/me', methods=['GET'])
def find_me():
    id = request.args.get('id')
    if id == None:
        return jsonify({"error": "There is no id provided"}), 400
    if not is_valid_uuid(id):
        return jsonify({"error": "Id is invalid"}), 400
    try:
        profile = find_profile_by_id(id, ProfileType.FULL)
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 400
    except Exception as err:
        return jsonify({"error": str(err)}), 500
    return jsonify(profile.__dict__), 200

@bp.route("/confirm/<token>")
def confirm(token):
    email = confirm_token(token)
    if not email:
        return jsonify({"error": "The confirmation link is invalid or has expired"}), 400
    fields_needed = "id"
    condition_args = dict()
    condition_args['email'] = email
    try:
        id = select_query(TABLE_NAME, fields_needed, condition_args)
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    if not id:
        return jsonify({"error": "There is no user with such email"}), 400
    try:
        update_query(TABLE_NAME, {'emailVerified': True}, {'id': id[0][0]})
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    """need to add redirect maybe"""
    return "Email confirmed", 200

@bp.route('/mailReset/<token>/<id>', methods=['GET'])
def mail_reset(token, id):
    email = confirm_token(token)
    if not email:
        return jsonify({"error": "The confirmation link is invalid or has expired"}), 400
    fields_needed = "id"
    condition_args = dict()
    condition_args['email'] = email
    try:
        id = select_query(TABLE_NAME, fields_needed, condition_args)
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    if not id:
        return jsonify({"error": "There is no user with such username"}), 400
    try:
        update_query(TABLE_NAME, {'password': None}, {'id': id[0][0]})
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    """Maybe need to add redirect"""
    return "Password reset", 200

@bp.route('/editMail', methods=['POST'])
def edit_mail():
    if not check_post_fields(request.json, {'id', 'email'}):    
        return jsonify({"error": "Not all necessary fields are in the request"}), 400
    if not is_valid_uuid(request.json['id']):
        return jsonify({"error": "Id is invalid"}), 400
    try:
        id_check = find_profile_by_id(request.json['id'], ProfileType.SHORT)
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 400
    except Exception as err:
        return jsonify({"error": str(err)}), 500
    try:
        update_query(TABLE_NAME, {'email': request.json['email'], 'emailVerified': False}, 
                     {'id': request.json['id']})
    except psycopg2.errors.UniqueViolation as err:
        return jsonify({"error": "Profile with this email already exists"}), 400
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    try:
        confirm_email_send(request.json['email'])
    except Exception as err:
        return jsonify({"error": "Email sending failed"}), 500
    return jsonify({'id': request.json['id']}), 200

@bp.route('/resendMail', methods=['GET'])
def resend_mail():
    id = request.args.get('id')
    if id == None:
        return jsonify({"error": "There is no id provided"}), 400
    if not is_valid_uuid(id):
        return jsonify({"error": "Id is invalid"}), 400
    fields_needed = "email, emailVerified"
    condition_args = dict()
    condition_args['id'] = id
    try:
        data = select_query(TABLE_NAME, fields_needed, condition_args)
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    if not data:   
        return jsonify({"error": "There is no user with such id"}), 400
    if data[0][1] == True:
        return jsonify({"error": "Email is already verified"}), 400
    try:
        confirm_email_send(data[0][0])
    except Exception as err:
        return jsonify({"error": "Email sending failed"}), 500
    return jsonify({'id': id}), 200

@bp.route('/changeUsername', methods=['PUT'])
def change_username():
    if not check_post_fields(request.json, {'id', 'username'}):
        return jsonify({"error": "Not all necessary fields are in the request"}), 400
    if not is_valid_uuid(request.json['id']):
        return jsonify({"error": "Id is invalid"}), 400
    try:
        id_check = find_profile_by_id(request.json['id'], ProfileType.SHORT)
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 400
    except Exception as err:
        return jsonify({"error": str(err)}), 500
    try:
        update_query(TABLE_NAME, {'username': request.json['username']}, {'id': request.json['id']})
    except psycopg2.errors.UniqueViolation as err:
        return jsonify({"error": "Profile with this username already exists"}), 400
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    return jsonify({'id': request.json['id']}), 200

@bp.route('/resetPassword', methods=['POST'])
def reset_password():
    if not check_post_fields(request.json, {'username'}):
        return jsonify({"error": "Not all necessary fields are in the request"}), 400
    fields_needed = "email, id"
    condition_args = dict()
    condition_args['username'] = request.json['username']
    try:
        data = select_query(TABLE_NAME, fields_needed, condition_args)
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    if not data:
        return jsonify({"error": "There is no user with such username"}), 400
    try:
        send_reset_password(data[0][0], data[0][1])
    except Exception as err:
        return jsonify({"error": "Email sending failed"}), 500
    return jsonify({'id': data[0][1]}), 200

@bp.route('/updatePassword', methods=['POST'])
def update_password():
    if not check_post_fields(request.json, {'id', 'password'}):
        return jsonify({"error": "Not all necessary fields are in the request"}), 400
    if not is_valid_uuid(request.json['id']):
        return jsonify({"error": "Id is invalid"}), 400
    try:
        id_check = find_profile_by_id(request.json['id'], ProfileType.SHORT)
    except NotFoundError as err:
        return str(err), 400
    except Exception as err:
        return str(err), 500
    try:
        update_query(TABLE_NAME, {'password': sha256_crypt.encrypt(request.json['password'])}, 
                     {'id': request.json['id']})
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    return jsonify({'id': request.json['id']}), 200

@bp.route('/checkUsername', methods=['GET'])
def check_username():
    username = request.args.get('username')
    if username == None:
        return jsonify({"error": "There is no username provided"}), 400
    fields_needed = "id"
    condition_args = dict()
    condition_args['username'] = username
    try:
        data = select_query(TABLE_NAME, fields_needed, condition_args)
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    if data:
        return jsonify({"exists": True}), 200
    return jsonify({"exists": False}), 200

@bp.route('/like', methods=['PUT'])
def like():
    if not check_post_fields(request.json, {'likerId', 'wasLikedId'}):
        return jsonify({"error": "Not all necessary fields are in the request"}), 400
    if not is_valid_uuid(request.json['likerId']):
        return jsonify({"error": "LikerId is invalid"}), 400
    if not is_valid_uuid(request.json['wasLikedId']):
        return jsonify({"error": "WasLikedId is invalid"}), 400
    if request.json['likerId'] == request.json['wasLikedId']:
        return jsonify({"error": "You can't like yourself"}), 400
    fields_needed = "liked"
    condition_args = dict()
    condition_args['id'] = request.json['likerId']
    try:
        liked = select_query(TABLE_NAME, fields_needed, condition_args)
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    if not liked:
        return jsonify({"error": "There is no user with likerId"}), 400
    fields_needed = "likedMe"
    condition_args = dict()
    condition_args['id'] = request.json['wasLikedId']
    try:
        likedMe = select_query(TABLE_NAME, fields_needed, condition_args)
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    if not likedMe:
        return jsonify({"error": "There is no user with wasLikedId"}), 400
    if request.json['wasLikedId'] not in liked[0][0]:
        try:
            update_query(TABLE_NAME, {'liked': liked[0][0] + [request.json['wasLikedId']]}, {'id': request.json['likerId']})
        except Exception as err:
            return jsonify({"error": "Database query failed"}), 500
    else:
        return jsonify({"error": "The user is already liked"}), 400
    if request.json['likerId'] not in likedMe[0][0]:
        try:
            update_query(TABLE_NAME, {'likedMe': likedMe[0][0] + [request.json['likerId']]}, {'id': request.json['wasLikedId']})
        except Exception as err:
            return jsonify({"error": "Database query failed"}), 500
    return jsonify({'likerId': request.json['likerId']}), 200

@bp.route('/unlike', methods=['PUT'])
def unlike():
    if not check_post_fields(request.json, {'likerId', 'wasLikedId'}):
        return jsonify({"error": "Not all necessary fields are in the request"}), 400
    if not is_valid_uuid(request.json['likerId']):
        return jsonify({"error": "LikerId is invalid"}), 400
    if not is_valid_uuid(request.json['wasLikedId']):
        return jsonify({"error": "WasLikedId is invalid"}), 400
    if request.json['likerId'] == request.json['wasLikedId']:
        return jsonify({"error": "You can't unlike yourself"}), 400
    fields_needed = "liked"
    condition_args = dict()
    condition_args['id'] = request.json['likerId']
    try:
        liked = select_query(TABLE_NAME, fields_needed, condition_args)
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    if not liked:
        return jsonify({"error": "There is no user with likerId"}), 400
    fields_needed = "likedMe"
    condition_args = dict()
    condition_args['id'] = request.json['wasLikedId']
    try:
        likedMe = select_query(TABLE_NAME, fields_needed, condition_args)
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    if not likedMe:
        return jsonify({"error": "There is no user with wasLikedId"}), 400
    if request.json['wasLikedId'] in liked[0][0]:
        try:
            liked[0][0].remove(request.json['wasLikedId'])
            update_query(TABLE_NAME, { 'liked': liked[0][0] }, {'id': request.json['likerId']})
        except Exception as err:
            return jsonify({"error": "Database query failed"}), 500
    else:
        return jsonify({"error": "The user is not liked"}), 400
    if request.json['likerId'] in likedMe[0][0]:
        try:
            likedMe[0][0].remove(request.json['likerId'])
            update_query(TABLE_NAME, {'likedMe': likedMe[0][0]}, {'id': request.json['wasLikedId']})
        except Exception as err:
            return jsonify({"error": "Database query failed"}), 500
    return jsonify({'likerId': request.json['likerId']}), 200

@bp.route('/likedByMe', methods=['GET'])
def get_liked_by_me():
    id = request.args.get('id')
    if id == None:
        return jsonify({"error": "There is no id provided"}), 400
    if not is_valid_uuid(id):
        return jsonify({"error": "Id is invalid"}), 400
    fields_needed = "liked"
    condition_args = dict()
    condition_args['id'] = id
    try:
        liked = select_query(TABLE_NAME, fields_needed, condition_args)
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    if not liked:
        return jsonify({"error": "There is no user with such id"}), 400
    profileList = []
    for liked_id in liked[0][0]:
        try:
            profileList.append(find_profile_by_id(liked_id, ProfileType.SHORT).__dict__)
        except NotFoundError as err:
            return jsonify({"error": str(err)}), 400
        except Exception as err:
            return jsonify({"error": str(err)}), 500
    return jsonify(profileList), 200

@bp.route('/wasLikedBy', methods=['GET'])
def was_liked_by():
    id = request.args.get('id')
    if id == None:
        return jsonify({"error": "There is no id provided"}), 400
    if not is_valid_uuid(id):
        return jsonify({"error": "Id is invalid"}), 400
    fields_needed = "likedMe"
    condition_args = dict()
    condition_args['id'] = id
    try:
        likedMe = select_query(TABLE_NAME, fields_needed, condition_args)
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    if not likedMe:
        return jsonify({"error": "There is no user with such id"}), 400
    profileList = []
    for liked_id in likedMe[0][0]:
        try:
            profileList.append(find_profile_by_id(liked_id, ProfileType.SHORT).__dict__)
        except NotFoundError as err:
            return jsonify({"error": str(err)}), 400
        except Exception as err:
            return jsonify({"error": str(err)}), 500
    return jsonify(profileList), 200

@bp.route('/blacklistAdd', methods=['PUT'])
def blacklist_add():
    if not check_post_fields(request.json, {'id', 'blackedId'}):
        return jsonify({"error": "Not all necessary fields are in the request"}), 400
    if not is_valid_uuid(request.json['id']):
        return jsonify({"error": "Id is invalid"}), 400
    if not is_valid_uuid(request.json['blackedId']):
        return jsonify({"error": "BlackedId is invalid"}), 400
    if request.json['id'] == request.json['blackedId']:
        return jsonify({"error": "You can't add yourself to blacklist"}), 400
    try:
        blackedId_check = find_profile_by_id(request.json['blackedId'], ProfileType.SHORT)
    except NotFoundError as err:
        return "There is no user with blackedId", 400
    except Exception as err:
        return "Database error", 500
    fields_needed = "blacklist"
    condition_args = dict()
    condition_args['id'] = request.json['id']
    try:
        blacklist = select_query(TABLE_NAME, fields_needed, condition_args)
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    if not blacklist:
        return jsonify({"error": "There is no user with id"}), 400
    if request.json['blackedId'] in blacklist[0][0]:
        return jsonify({"error": "The user is already in blacklist"}), 400
    blacklist[0][0].append(request.json['blackedId'])
    try:
        update_query(TABLE_NAME, {'blacklist': blacklist[0][0]}, {'id': request.json['id']})
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    return jsonify({'id': request.json['id']}), 200

@bp.route('/isInBlacklist', methods=['GET'])
def is_in_blacklist():
    id = request.args.get('id')
    blackedId = request.args.get('blackedId')
    if id == None:
        return jsonify({"error": "There is no id provided"}), 400
    if blackedId == None:
        return jsonify({"error": "There is no blackedId provided"}), 400
    if not is_valid_uuid(id):
        return jsonify({"error": "Id is invalid"}), 400
    if not is_valid_uuid(blackedId):
        return jsonify({"error": "BlackedId is invalid"}), 400
    fields_needed = "blacklist"
    condition_args = dict()
    condition_args['id'] = id
    try:
        blacklist = select_query(TABLE_NAME, fields_needed, condition_args)
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    if not blacklist:
        return jsonify({"error": "There is no user with id"}), 400
    if blackedId in blacklist[0][0]:
        return jsonify({"black": True}), 200
    return jsonify({"black": False}), 200

@bp.route('/deleteFromBlacklist', methods=['PUT'])
def delete_from_blacklist():
    if not check_post_fields(request.json, {'id', 'blackedId'}):
        return jsonify({"error": "Not all necessary fields are in the request"}), 400
    if not is_valid_uuid(request.json['id']):
        return jsonify({"error": "Id is invalid"}), 400
    if not is_valid_uuid(request.json['blackedId']):
        return jsonify({"error": "BlackedId is invalid"}), 400
    if request.json['id'] == request.json['blackedId']:
        return jsonify({"error": "You can't delete yourself from blacklist"}), 400
    fields_needed = "blacklist"
    condition_args = dict()
    condition_args['id'] = request.json['id']
    try:
        blacklist = select_query(TABLE_NAME, fields_needed, condition_args)
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    if not blacklist:
        return jsonify({"error": "There is no user with id"}), 400
    if request.json['blackedId'] not in blacklist[0][0]:
        return jsonify({"error": "The user is not in blacklist"}), 400
    blacklist[0][0].remove(request.json['blackedId'])
    try:
        update_query(TABLE_NAME, {'blacklist': blacklist[0][0]}, {'id': request.json['id']})
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    return jsonify({'id': request.json['id']}), 200