import datetime
import jwt
from passlib.hash import sha256_crypt
import re

from flask import (
    current_app, request, jsonify
)
from auth_middleware.jwt_decorator import token_required
from tags.routes import add_tags_to_db
from lib_db.select import select_query
from lib_db.update import update_query
from profile import bp

import uuid
import psycopg2.extras
from profile.exceptions import NotFoundError, BadRequest
from profile.profile_spec import confirm_email_send, register_user, add_views_to_db, check_edit_data, like_unlike
from profile.profile_entities import ShortProfile, ProfileType
from profile.profile_common import find_profile_by_id
from notification.sockets import view_notify
from chat.utils import delete_chat_on_unlike
from profile.profile_common import is_password_valid


from utils.utils import is_valid_uuid, check_and_clean_fields

TABLE_NAME = 'profile'

@bp.route('/', methods=['POST'])
def create():
    request_data = check_and_clean_fields(request.json, {'username', 'password', 'firstName', 'lastName', 'email'})
    if not request_data:    
        return jsonify({"error": "Not all necessary fields are in the request"}), 400
    if not re.match(r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$', request_data['email']):
        return jsonify({"error": "Wrong email format"}), 400
    check_password = is_password_valid(request_data['password'])
    if check_password:
        return jsonify({"error": check_password}), 400
    psycopg2.extras.register_uuid()
    id = uuid.uuid4()
    try:
        register_user(id, request_data)
    except BadRequest as err:
        return jsonify({"error": str(err)}), 400
    except Exception as err:
        print(err)
        return jsonify({"error": "Internal server error"}), 500
    return jsonify({'id': id}), 201

@bp.route('/<id>', methods = ['GET', 'PUT'])
def id_route(id):
    if request.method == 'GET':
        guest_id = request.args.get('user')
        return get_profile_info(guest_id, id)
    elif request.method == 'PUT':
        return edit_profile(id, request.json)

#@token_required
def get_profile_info(guest_id, id):
    if guest_id == None:
        return jsonify({"error": "There is no user id provided"}), 400
    if not is_valid_uuid(guest_id) or not is_valid_uuid(id):
        return jsonify({"error": "Wrong id format"}), 400
    try:
        profile = find_profile_by_id(id,
            ProfileType.FULL if id == guest_id else ProfileType.USUAL)
    except NotFoundError as err:
        return str(err), 400
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    if not id == guest_id:
        try:
            view_notify(id, guest_id)
        except Exception as err:
            pass
        try:
            add_views_to_db(id, guest_id, profile)
        except NotFoundError as err:
            return jsonify({"error": str(err)}), 400
        except Exception as err:
            print(err)
            return jsonify({"error": "Database query failed"}), 500
        if guest_id not in profile.viewedMe:
            profile.viewedMe.append(guest_id)
            profile.fameRating = round(len(profile.likedMe) / len(profile.viewedMe) * 5, 2)
    return jsonify(profile.__dict__), 200

def edit_profile(id, request_data):
    request_data = check_and_clean_fields(request.json, {'firstName', 'lastName', 'dateOfBirth', 'gender',
                                'sexPref', 'pictures', 'biography', 'tagList', 'mainImage', 'location'})
    if not request_data:
        return jsonify({"error": "Not all necessary fields are in the request"}), 400
    try:
        check_edit_data(id, request_data)
    except TypeError as err:
        return jsonify({"error": str(err)}), 400
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 400
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    try:
        update_query(TABLE_NAME, request_data, {'id': id})
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    profile = find_profile_by_id(id, ProfileType.FULL)
    try:
        add_tags_to_db(profile.tagList)
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    return jsonify(profile.__dict__), 201

@bp.route('/login', methods=['POST'])
def login():
    request_data = check_and_clean_fields(request.json, {'username', 'password'})
    if not request_data:
        return jsonify({"error": "Not all necessary fields are in the request"}), 400      
    fields_needed = "id, firstName, lastName, mainImage, isOnline, lastSeen, password"
    try:
        profile = select_query(TABLE_NAME, fields_needed, {'username': request_data['username']})
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    if not profile:
        return jsonify({"error": "There is no user with such username"}), 400
    if sha256_crypt.verify(request.json['password'], profile[0][6]):
        loginedUser = ShortProfile(profile[0])
        response = loginedUser.__dict__
        response['jwt_token'] = jwt.encode({'id' : str(loginedUser.id), 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=180)}, current_app.config['SECRET_KEY'], "HS256")
        return jsonify(response), 200
    else:
        return jsonify({"error": "Password is wrong"}), 401

@bp.route('/<id>/username', methods=['PUT'])
def change_username(id):
    request_data = check_and_clean_fields(request.json, {'username'})
    if not request_data:
        return jsonify({"error": "Not all necessary fields are in the request"}), 400
    if not is_valid_uuid(id):
        return jsonify({"error": "Id is invalid"}), 400
    if len(request_data['username']) > 50:
        return jsonify({"error": "Username is too long"}), 400
    try:
        find_profile_by_id(id, ProfileType.SHORT)
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 400
    except Exception as err:
        return jsonify({"error": str(err)}), 500
    try:
        update_query(TABLE_NAME, {'username': request_data['username']}, {'id': id})
    except psycopg2.errors.UniqueViolation as err:
        return jsonify({"error": "Profile with this username already exists"}), 400
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    return jsonify({'id': id }), 200

@bp.route('/username', methods=['GET'])
def check_username():
    username = request.args.get('username')
    if username == None:
        return jsonify({"error": "There is no username provided"}), 400
    fields_needed = "id"
    try:
        data = select_query(TABLE_NAME, fields_needed, {'username': username})
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    if data:
        return jsonify({"exists": True}), 200
    return jsonify({"exists": False}), 200

@bp.route('/password', methods=['DELETE'])
def reset_password():
    request_data = check_and_clean_fields(request.json, {'username'})
    if not request_data:
        return jsonify({"error": "Not all necessary fields are in the request"}), 400
    fields_needed = "id, email"
    try:
        data = select_query(TABLE_NAME, fields_needed, {'username': request_data['username']})
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    if not data:
        return jsonify({"error": "There is no user with such username"}), 400
    try:
        confirm_email_send(data[0][0], data[0][1], False)
    except Exception as err:
        return jsonify({"error": "Email sending failed"}), 500
    return jsonify({'id': data[0][0]}), 200

@bp.route('/<id>/password', methods=['PUT'])
def update_password(id):
    if not check_and_clean_fields(request.json, {'password'}):
        return jsonify({"error": "Not all necessary fields are in the request"}), 400
    if not isinstance(request.json['password'], str):
        return jsonify({"error": "Password should be a string"}), 400
    if not is_valid_uuid(id):
        return jsonify({"error": "Id is invalid"}), 400
    check_password = is_password_valid(request.json['password'])
    if check_password:
        return jsonify({"error": check_password}), 400
    try:
        find_profile_by_id(id, ProfileType.SHORT)
    except NotFoundError as err:
        return str(err), 400
    except Exception as err:
        return str(err), 500
    try:
        update_query(TABLE_NAME, {'password': sha256_crypt.encrypt(request.json['password'])}, 
                     {'id': id})
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    return jsonify({'id': id}), 200

@bp.route('/<id>/like', methods=['GET', 'PUT', 'DELETE'])
def like_route(id):
    if request.method == 'GET':
        return get_likes(id, request.args.get('who'))
    elif request.method == 'PUT' or request.method == 'DELETE':
        return like_unlike_route(id, request.json, request.method)

def like_unlike_route(id, request_data, method):
    request_data = check_and_clean_fields(request_data, {'user'})
    if not request_data:
        return jsonify({"error": "Not all necessary fields are in the request"}), 400
    if not is_valid_uuid(id) or not is_valid_uuid(request_data.get('user')):
        return jsonify({"error": "ID is invalid"}), 400
    if id == request_data['user']:
        return jsonify({"error": "You can't like yourself"}), 400
    fields_needed = "liked"
    try:
        liked = select_query(TABLE_NAME, fields_needed, {'id': request_data['user']})
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    if not liked:
        return jsonify({"error": "There is no user with user id"}), 400
    fields_needed = "likedMe"
    try:
        likedMe = select_query(TABLE_NAME, fields_needed, {'id': id})
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    if not likedMe:
        return jsonify({"error": "There is no user with ID from link"}), 400
    if method == 'PUT':
        return like_unlike(id, request_data['user'], liked[0][0], likedMe[0][0], if_like=True)
    elif method == 'DELETE':
        return like_unlike(id, request_data['user'], liked[0][0], likedMe[0][0], if_like=False)

def get_likes(id, who):
    if who == None:
        return jsonify({"error": "There is no who provided"}), 400
    if not is_valid_uuid(id):
        return jsonify({"error": "Wrong id format"}), 400
    if who != 'me' and who != 'byMe':
        return jsonify({"error": "Wrong who format"}), 400
    fields_needed = "liked" if who == 'byMe' else "likedMe"
    try:
        liked = select_query(TABLE_NAME, fields_needed, {'id': id})
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

@bp.route('/<id>/blacklist', methods=['PUT', 'DELETE', 'GET'])
def blacklist_route(id):
    if request.method == 'GET':
        user = request.args.get('user')
    else:
        request_data = check_and_clean_fields(request.json, {'user'})
        if not request_data:
            return jsonify({"error": "Not all necessary fields are in the request"}), 400
        user = request_data.get('user')
    if not is_valid_uuid(id) or not is_valid_uuid(user):
        return jsonify({"error": "Id is invalid"}), 400
    if id == user:
        return jsonify({"error": "User and ID should be different"}), 400
    try:
        find_profile_by_id(id, ProfileType.SHORT)
    except NotFoundError as err:
        return "There is no user with user ID", 400
    except Exception as err:
        return "Database error", 500
    fields_needed = "blacklist"
    try:
        blacklist = select_query(TABLE_NAME, fields_needed, {'id': user})
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    if not blacklist:
        return jsonify({"error": "There is no user with user ID"}), 400
    if request.method == 'PUT':
        if id in blacklist[0][0]:
            return jsonify({"error": "The user is already in blacklist"}), 400
        blacklist[0][0].append(id)
        try:
            like_unlike_route(id, {'user': user}, 'DELETE')
            delete_chat_on_unlike(id, user)
        except Exception as err:
            return jsonify({"error": "Database query failed during blocking user"}), 500
    elif request.method == 'DELETE':
        if id not in blacklist[0][0]:
            return jsonify({"error": "The user is not in blacklist"}), 400
        blacklist[0][0].remove(id)
    elif request.method == 'GET':
        if id in blacklist[0][0]:
            return jsonify({"blacklist": True}), 200
        return jsonify({"blacklist": False}), 200
    try:
        update_query(TABLE_NAME, {'blacklist': blacklist[0][0]}, {'id': request_data['user']})
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    return jsonify({'id': request_data['user']}), 200

@bp.route('/<id>/fake', methods=['PUT', 'DELETE'])
def fake_route(id):
    if not is_valid_uuid(id):
        return jsonify({"error": "Id is invalid"}), 400
    request_data = check_and_clean_fields(request.json, {'user'})
    if not request_data:    
        return jsonify({"error": "Not all necessary fields are in the request"}), 400
    if id == request_data['user']:
        return jsonify({"error": "You can't mark yourself as fake"}), 400
    if request.method == 'PUT':
        return fake_action(id, True)
    elif request.method == 'DELETE':
        return fake_action(id, False)

def fake_action(id, if_fake):
    try:
        find_profile_by_id(id, ProfileType.SHORT)
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 400
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    try:
        update_query(TABLE_NAME, {'isFake': if_fake}, {'id': id})
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    return jsonify({'id': id}), 200

@bp.route('/test', methods=['GET'])
def test_db():
    user = {}
    try:
        user = find_profile_by_id('00818140-f095-9ecc-11af-0e751809a8c0', ProfileType.FULL).__dict__
    except Exception as err:
        return str(err), 500
    return user
