from flask import jsonify, request
from lib_db.select import select_for_search
from profile import bp
from profile.exceptions import NotFoundError
from profile.search_utils import get_user_sex_prefernces, is_get_params_valid_search, parse_data_to_frontend, get_age_range, get_fame_range, get_geo_range, create_order_condition
from utils.utils import is_valid_uuid

@bp.route('/search/<page>', methods=['POST'])
def search(page):
  id = request.json.get('id')
  if not id:
    return jsonify({'error': 'No user id'}), 400
  if not is_valid_uuid(id):
    return jsonify({'error': 'Invalid user id'}), 400
  try:
    age_range = get_age_range(request.json.get('ageFrom'), request.json.get('ageTo'))
    fame_range = get_fame_range(request.json.get('fameFrom'), request.json.get('fameTo'))
    geo_range = get_geo_range(request.json.get('location'), request.json.get('locationRadius'))
    order = create_order_condition(request.json.get('order'))
  except Exception as e:
    return jsonify({'error': str(e)}), 400
  try:
    sex_info = get_user_sex_prefernces(id)
  except NotFoundError as e:
    return jsonify({'error': str(e)}), 400
  except Exception as e:
    return jsonify({'error': "Database error"}), 500
  try:
    data = select_for_search(id, sex_info, age_range, fame_range, geo_range, request.json.get('tags'), page, order)
  except Exception as e:
    print(str(e))
    return jsonify({'error': "Database error"}), 500
  return jsonify(parse_data_to_frontend(data)), 200