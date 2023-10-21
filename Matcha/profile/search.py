from flask import jsonify, request
from lib_db.select import select_for_search
from profile import bp
from profile.exceptions import NotFoundError
from profile.search_utils import get_user_sex_prefernces, is_get_params_valid_search, parse_data_to_frontend
from utils.utils import is_valid_uuid

@bp.route('/search', methods=['GET'])
def search():
  id = request.args.get('id')
  if not is_valid_uuid(id):
    return jsonify({'error': 'Invalid user id'}), 400
  if not is_get_params_valid_search(request):
    return jsonify({'error': 'Not enough GET parameters'}), 400
  try:
    sex_info = get_user_sex_prefernces(id)
  except NotFoundError as e:
    return str(e), 400
  except Exception as e:
    return "Database error", 500
  try:
    data = select_for_search(id, sex_info)
  except Exception as e:
    print(str(e))
    return "Database error", 500
  return jsonify(parse_data_to_frontend(data)), 200