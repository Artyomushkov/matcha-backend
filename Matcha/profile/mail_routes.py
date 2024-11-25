import re
from flask import jsonify, request
import psycopg2
from profile.mail_utils import confirm_token
from profile import bp
from lib_db.select import select_query
from lib_db.update import update_query
from profile.exceptions import NotFoundError, BadRequest, FatalError
from profile.mail_utils import check_user_email
from profile.profile_common import find_profile_by_id
from utils.utils import is_valid_uuid, check_and_clean_fields
from profile.profile_spec import confirm_email_send
from profile.profile_entities import ShortProfile, ProfileType

TABLE_NAME = 'profile'

@bp.route("<id>/mail/<token>", methods=["GET", "DELETE"])
def mail_confirm(id, token):
    email = confirm_token(token)
    if not email:
        return jsonify({"error": "The confirmation link is invalid or has expired"}), 400
    try:
        check_user_email(id, email)
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 404
    except BadRequest as err:
        return jsonify({"error": str(err)}), 400
    except FatalError as err:    
        return jsonify({"error": str(err)}), 500
    if request.method == 'GET':
        try:
            update_query(TABLE_NAME, {'emailVerified': True}, {'id': id})
        except Exception as err:
            return jsonify({"error": "Database query failed"}), 500
    elif request.method == 'DELETE':
        try:
            update_query(TABLE_NAME, {'password': None}, {'id': id})
        except Exception as err:
            return jsonify({"error": "Database query failed"}), 500
    return "Email confirmed", 200

@bp.route('/<id>/mail', methods=['PUT', 'GET'])
def id_mail_route(id):
    if not is_valid_uuid(id):
        return jsonify({"error": "Id is invalid"}), 400
    if request.method == 'PUT':
        return mail_change_put(id, request.json)
    elif request.method == 'GET':
        return mail_resend_get(id)

def mail_change_put(id, request_data):
    request_data = check_and_clean_fields(request.json, {'email'})
    if not request_data:
        return jsonify({"error": "Not all necessary fields are in the request"}), 400
    if not re.match(r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$', request_data['email']):
        return jsonify({"error": "Wrong email format"}), 400
    try:
        find_profile_by_id(id, ProfileType.SHORT)
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 400
    except Exception as err:
        return jsonify({"error": str(err)}), 500
    try:
        update_query(TABLE_NAME, {'email': request_data['email'], 'emailVerified': False}, {'id': id})
    except psycopg2.errors.UniqueViolation as err:
        return jsonify({"error": "Profile with this email already exists"}), 400
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    try:
        confirm_email_send(id, request_data['email'], True)
    except Exception as err:
        return jsonify({"error": "Email sending failed"}), 500
    return jsonify({'id': id}), 200

def mail_resend_get(id):
    fields_needed = "email, emailVerified"
    try:
        data = select_query(TABLE_NAME, fields_needed, {'id': id})
    except Exception as err:
        return jsonify({"error": "Database query failed"}), 500
    if not data:   
        return jsonify({"error": "There is no user with such id"}), 400
    if data[0][1] == True:
        return jsonify({"error": "Email is already verified"}), 400
    try:
        confirm_email_send(id, data[0][0], True)
    except Exception as err:
        return jsonify({"error": "Email sending failed"}), 500
    return jsonify({'id': id}), 200