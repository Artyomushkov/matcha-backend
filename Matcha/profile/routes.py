from datetime import date
import functools
from passlib.hash import sha256_crypt

from flask import (
    Response, current_app, flash, g, redirect, render_template, request, session, url_for, jsonify
)
from Matcha.lib_db.insert import insert_query
from Matcha.lib_db.select import select_query
from Matcha.lib_db.update import update_query
from Matcha.profile import bp
from werkzeug.security import check_password_hash, generate_password_hash

from Matcha.db import get_db
import uuid
import psycopg2.extras
from Matcha.profile.short_profile_entity import ShortProfile

from Matcha.utils.utils import is_valid_uuid

TABLE_NAME = 'profile'

"""need to make fame rating zero"""
@bp.route('/register', methods=['POST'])
def register():
    """need to send mail to verify registration"""
    psycopg2.extras.register_uuid()
    try:
        password = request.json['password']
    except:
        return "Password is missing", 400
    id = uuid.uuid4()
    request.json['id'] = id
    request.json['emailVerified'] = False
    request.json['password'] = sha256_crypt.encrypt(password)
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
    return jsonify({'id': id}), 201

@bp.route('/id/<id>', methods = ['GET'])
def find_by_id(id):
    if not is_valid_uuid(id):
        return "Wrong id format", 400
    fields_needed = "id, firstName, lastName"
    condition_args = dict()
    condition_args['id'] = id
    try:
        profile = select_query(TABLE_NAME, fields_needed, condition_args)
    except Exception as err:
        return "Database query failed", 500
    if not profile:
        return "There is no user with such id", 400
    return jsonify(ShortProfile(profile[0]).__dict__), 200

@bp.route('/login', methods=['POST'])
def login():
    fields_needed = "id, firstName, lastName, password"
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
        if sha256_crypt.verify(request.json['password'], profile[0][3]):
            return jsonify(ShortProfile(profile[0]).__dict__), 200
        else:
            return "Password is wrong", 401
    except Exception as err:
        return "There is no password in request body", 400

"""isOnline need to set to true and lastSeen at the current moment"""
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
    try:
        person_req = find_by_id(request.json['id'])
        if person_req[1] == 400:
            raise TypeError(person_req[0])
        if person_req[1] == 500:
            raise Exception(person_req[0])
        condition_args['id'] = request.json['id']
        request.json.pop('id')
    except TypeError as err:
        return str(err), 400
    except Exception as err:
        return "Id processing failed", 500
    try:
        update_query(TABLE_NAME, request.json, condition_args)
    except Exception as err:
        return "Database query failed", 500
    return jsonify({'id' : condition_args['id']}), 201
          
@bp.route('/all', methods=['GET'])
def show():
    db = get_db()
    error = None
    try:
        with db.cursor() as cur:
            cur.execute("""
            SELECT * FROM profile;
            """,)
            profiles = cur.fetchall()
    except:
        error = "smth wrong with db"
    if error != None:
        return jsonify(error)
    return jsonify(profiles)