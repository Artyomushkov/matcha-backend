import time
from passlib.hash import sha256_crypt

from flask import (
    Response, current_app, flash, g, redirect, render_template, request, session, url_for, jsonify
)
from Matcha.lib_db.insert import insert_query
from Matcha.lib_db.select import select_query
from Matcha.lib_db.update import update_query
from Matcha.mail_utils import send_email
from Matcha.profile import bp

from Matcha.db import get_db
import uuid
import psycopg2.extras
from Matcha.profile.exceptions import NotFoundError
from Matcha.profile.profile_utils import ProfileType, confirm_email_send, confirm_token, find_profile_by_id, generate_token, send_reset_password
from Matcha.profile.short_profile_entity import ShortProfile

from Matcha.utils.utils import is_valid_uuid

TABLE_NAME = 'profile'

@bp.route('/register', methods=['POST'])
def register():
    if request.json.keys() < {'username', 'password', 'firstName', 'lastName', 'email'}:
        return "Not all necessary fields are in the request", 400
    psycopg2.extras.register_uuid()
    id = uuid.uuid4()
    request.json['id'] = id
    request.json['emailVerified'] = False
    request.json['password'] = sha256_crypt.encrypt(request.json['password'])
    request.json['fameRating'] = 0
    try:
        insert_query(TABLE_NAME, request.json)
    except psycopg2.errors.NotNullViolation:
        return "You haven't defined one of the fields", 400
    except psycopg2.errors.UniqueViolation as err:
        message = "undefined error"
        str_err = str(err)
        if str_err.find('username') != -1:
            message = "Profile with this username already exists"
        elif str_err.find('email') != -1:
            message = "Profile with this email already exists"     
        return message, 400
    except psycopg2.errors.StringDataRightTruncation as err:
        return "One of the fields is too long (more than 50 symbols)", 400
    except Exception as err:
        return "Database query failed", 500
    try:
        confirm_email_send(request.json['email'])
    except Exception as err:
        return "Email sending failed", 500
    return jsonify({'id': id}), 201

@bp.route('/id/<id>', methods = ['GET'])
def find_by_id(id):
    user_id = request.args.get('user')
    if user_id == None:
        return "There is no user id provided", 400
    if not is_valid_uuid(user_id):
        return "Wrong user id format", 400
    if not is_valid_uuid(id):
        return "Wrong id format", 400
    fields_needed = "viewed"
    condition_args = dict()
    condition_args['id'] = user_id
    try:
        viewed = select_query(TABLE_NAME, fields_needed, condition_args)
    except Exception as err:
        return "Database query failed", 500
    if not viewed:
        return "There is no user with such id", 400
    try:
        profile = find_profile_by_id(id, ProfileType.USUAL)
    except NotFoundError as err:
        return str(err), 400
    except Exception as err:
        return "Database query failed", 500
    if id not in viewed[0][0]:
        try:
            update_query(TABLE_NAME, {'viewed': viewed[0][0] + [id]}, {'id': user_id})
        except Exception as err:
            return "Database query failed", 500
    if user_id not in profile.viewedMe:
        try:
            update_query(TABLE_NAME, {'viewedMe': profile.viewedMe + [user_id]}, {'id': id})
        except Exception as err:
            return "Database query failed", 500
        profile.viewedMe.append(user_id)
    return jsonify(profile.__dict__), 200

@bp.route('/login', methods=['POST'])
def login():
    fields_needed = "id, firstName, lastName, mainImage, isOnline, lastSeen, password"
    condition_args = dict()
    try:
        condition_args['username'] = request.json['username']
    except Exception as err:
        return "There is no username in request body", 400
    try:
        profile = select_query(TABLE_NAME, fields_needed, condition_args)
    except Exception as err:
        return "Database query failed", 500
    if not profile:
        return "There is no user with such username", 400
    try:
        if sha256_crypt.verify(request.json['password'], profile[0][6]):
            return jsonify(ShortProfile(profile[0]).__dict__), 200
        else:
            return "Password is wrong", 401
    except Exception as err:
        return "There is no password in request body", 400

@bp.route('/edit', methods = ['PUT'])
def edit():
    if request.json.keys() < {'id', 'gender', 'sexPref', 'dateOfBirth', 'biography', 'tagList', 'mainImage', 'location'}:
        return "Not all necessary fields are in the request", 400
    if not isinstance(request.json['tagList'], list):
        return "TagList should be an array", 400
    if 'pictures' in request.json and not isinstance(request.json['pictures'], list):
        return "Pictures should be an array", 400
    if not isinstance(request.json['dateOfBirth'], int):
        return "dateOfBirth should be a number", 400
    try:
        lat = request.json['location']['lat']
        lon = request.json['location']['lon']
        if isinstance(lat, str) or isinstance(lat, str):
            raise TypeError("Coordinates should be numbers")
        request.json['GPSlat'] = float(lat)
        request.json['GPSlon'] = float(lon)
        request.json.pop('location')
    except Exception as err:
        return str(err), 400
    try:
        gender = request.json['gender']
        if gender != "male" and gender != "female" and gender != "other":
            raise TypeError("There is no such type of gender")
        sex_pref = request.json['sexPref']
        if sex_pref != "men" and sex_pref != "women" and sex_pref != "both":
            raise TypeError("Type of sex preference is unavailable")
    except TypeError as err:
        return str(err), 400
    except Exception as err:
        return "There is no gender or sex pref in request", 400
    condition_args = dict()
    request.json['isOnline'] = True
    request.json['lastSeen'] = int(time.time())
    try:
        person_req = find_profile_by_id(request.json['id'], ProfileType.SHORT)
        condition_args['id'] = request.json['id']
        request.json.pop('id')
    except NotFoundError as err:
        return str(err), 400
    except Exception as err:
        return str(err), 500
    try:
        update_query(TABLE_NAME, request.json, condition_args)
    except Exception as err:
        return "Database query failed", 500
    fullProfile = find_profile_by_id(condition_args['id'], ProfileType.FULL)
    return jsonify(fullProfile.__dict__), 201

@bp.route('/me', methods=['GET'])
def find_me():
    id = request.args.get('id')
    if id == None:
        return "There is no id provided", 400
    if not is_valid_uuid(id):
        return "Id is invalid", 400
    try:
        profile = find_profile_by_id(id, ProfileType.FULL)
    except NotFoundError as err:
        return str(err), 400
    except Exception as err:
        return str(err), 500
    return jsonify(profile.__dict__), 200

@bp.route("/confirm/<token>")
def confirm(token):
    email = confirm_token(token)
    if not email:
        return "The confirmation link is invalid or has expired", 400
    fields_needed = "id"
    condition_args = dict()
    condition_args['email'] = email
    try:
        id = select_query(TABLE_NAME, fields_needed, condition_args)
    except Exception as err:
        return "Database query failed", 500
    if not id:
        return "There is no user with such email", 400
    try:
        update_query(TABLE_NAME, {'emailVerified': True}, {'id': id[0][0]})
    except Exception as err:
        return "Database query failed", 500
    return "Email confirmed", 200

@bp.route('/mailReset/<token>/<id>', methods=['GET'])
def mail_reset(token, id):
    email = confirm_token(token)
    if not email:
        return "The confirmation link is invalid or has expired", 400
    fields_needed = "id"
    condition_args = dict()
    condition_args['email'] = email
    try:
        id = select_query(TABLE_NAME, fields_needed, condition_args)
    except Exception as err:
        return "Database query failed", 500
    if not id:
        return "There is no user with such username", 400
    try:
        update_query(TABLE_NAME, {'password': None}, {'id': id[0][0]})
    except Exception as err:
        return "Database query failed", 500
    return "Password reset", 200

@bp.route('/editMail', methods=['POST'])
def edit_mail():
    if request.json.keys() < {'id', 'email'}:
        return "Not all necessary fields are in the request", 400
    if not is_valid_uuid(request.json['id']):
        return "Id is invalid", 400
    try:
        id_check = find_profile_by_id(request.json['id'], ProfileType.SHORT)
    except NotFoundError as err:
        return str(err), 400
    except Exception as err:
        return str(err), 500
    try:
        update_query(TABLE_NAME, {'email': request.json['email'], 'emailVerified': False}, 
                     {'id': request.json['id']})
    except psycopg2.errors.UniqueViolation as err:
        return "Profile with this email already exists", 400
    except Exception as err:
        return "Database query failed", 500
    try:
        confirm_email_send(request.json['email'])
    except Exception as err:
        return "Email sending failed", 500
    return jsonify({'id': request.json['id']}), 200

@bp.route('/resendMail', methods=['GET'])
def resend_mail():
    id = request.args.get('id')
    if id == None:
        return "There is no id provided", 400
    if not is_valid_uuid(id):
        return "Id is invalid", 400
    fields_needed = "email, emailVerified"
    condition_args = dict()
    condition_args['id'] = id
    try:
        data = select_query(TABLE_NAME, fields_needed, condition_args)
    except Exception as err:
        return "Database query failed", 500
    if not data:   
        return "There is no user with such id", 400
    if data[0][1] == True:
        return "Email is already verified", 400
    try:
        confirm_email_send(data[0][0])
    except Exception as err:
        return "Email sending failed", 500
    return jsonify({'id': id}), 200

@bp.route('/changeUsername', methods=['PUT'])
def change_username():
    if request.json.keys() < {'id', 'username'}:
        return "Not all necessary fields are in the request", 400
    if not is_valid_uuid(request.json['id']):
        return "Id is invalid", 400
    try:
        id_check = find_profile_by_id(request.json['id'], ProfileType.SHORT)
    except NotFoundError as err:
        return str(err), 400
    except Exception as err:
        return str(err), 500
    try:
        update_query(TABLE_NAME, {'username': request.json['username']}, {'id': request.json['id']})
    except psycopg2.errors.UniqueViolation as err:
        return "Profile with this username already exists", 400
    except Exception as err:
        return "Database query failed", 500
    return jsonify({'id': request.json['id']}), 200

@bp.route('/resetPassword', methods=['POST'])
def reset_password():
    if request.json.keys() < {'username'}:
        return "Not all necessary fields are in the request", 400
    fields_needed = "email, id"
    condition_args = dict()
    condition_args['username'] = request.json['username']
    try:
        data = select_query(TABLE_NAME, fields_needed, condition_args)
    except Exception as err:
        return "Database query failed", 500
    if not data:
        return "There is no user with such username", 400
    try:
        send_reset_password(data[0][0], data[0][1])
    except Exception as err:
        return "Email sending failed", 500
    return jsonify({'id': data[0][1]}), 200

@bp.route('/updatePassword', methods=['POST'])
def update_password():
    if request.json.keys() < {'id', 'password'}:
        return "Not all necessary fields are in the request", 400
    if not is_valid_uuid(request.json['id']):
        return "Id is invalid", 400
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
        return "Database query failed", 500
    return jsonify({'id': request.json['id']}), 200

@bp.route('/checkUsername', methods=['GET'])
def check_username():
    username = request.args.get('username')
    if username == None:
        return "There is no username provided", 400
    fields_needed = "id"
    condition_args = dict()
    condition_args['username'] = username
    try:
        data = select_query(TABLE_NAME, fields_needed, condition_args)
    except Exception as err:
        return "Database query failed", 500
    if data:
        return jsonify({"exists": True}), 200
    return jsonify({"exists": False}), 200

"Need to fix checking of necessary fields"
@bp.route('/like', methods=['PUT'])
def like():
    if request.json.keys() < {'likerId', 'wasLikedId'}:
        return "Not all necessary fields are in the request", 400
    if not is_valid_uuid(request.json['likerId']):
        return "LikerId is invalid", 400
    if not is_valid_uuid(request.json['wasLikedId']):
        return "WasLikedId is invalid", 400
    if request.json['likerId'] == request.json['wasLikedId']:
        return "You can't like yourself", 400
    fields_needed = "liked"
    condition_args = dict()
    condition_args['id'] = request.json['likerId']
    try:
        liked = select_query(TABLE_NAME, fields_needed, condition_args)
    except Exception as err:
        return "Database query failed", 500
    if not liked:
        return "There is no user with likerId", 400
    fields_needed = "likedMe"
    condition_args = dict()
    condition_args['id'] = request.json['wasLikedId']
    try:
        likedMe = select_query(TABLE_NAME, fields_needed, condition_args)
    except Exception as err:
        return "Database query failed", 500
    if not likedMe:
        return "There is no user with wasLikedId", 400
    if request.json['wasLikedId'] not in liked[0][0]:
        try:
            update_query(TABLE_NAME, {'liked': liked[0][0] + [request.json['wasLikedId']]}, {'id': request.json['likerId']})
        except Exception as err:
            return "Database query failed", 500
    else:
        return "The user is already liked", 400
    if request.json['likerId'] not in likedMe[0][0]:
        try:
            update_query(TABLE_NAME, {'likedMe': likedMe[0][0] + [request.json['likerId']]}, {'id': request.json['wasLikedId']})
        except Exception as err:
            return "Database query failed", 500
    return jsonify({'id': request.json['likerId']}), 200
