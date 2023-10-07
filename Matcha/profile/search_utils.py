from flask import request

from Matcha.lib_db.select import select_query
from Matcha.profile.exceptions import NotFoundError

def is_get_params_valid_search(request: request):
  if request.args.get('id') == None or \
    request.args.get('ageFrom') == None or \
    request.args.get('ageTo') == None or \
    request.args.get('fameFrom') == None or \
    request.args.get('fameTo') == None or \
    request.args.get('location') == None or \
    request.args.get('locationRadius') == None or \
    request.args.get('tags') == None or \
    request.args.get('order') == None:
      return False
  return True

def get_user_sex_prefernces(id):
  fields_needed = "gender, sexPref"
  condition_args = {'id': id}
  info = select_query('profile', fields_needed, condition_args)
  if not info:
     raise NotFoundError('User not found')
  info = {
    'gender': info[0][0],
    'sexPref': info[0][1]
  }
  res = {}
  if info['sexPref'] == 'women':
    res['gender'] = ['female']
  elif info['sexPref'] == 'men':
    res['gender'] = ['male']
  else:
    res['gender'] = ['male', 'female', 'other']
  if info['gender'] == 'male':
    res['sexPref'] = ['men', 'both']
  elif info['gender'] == 'female':
    res['sexPref'] = ['women', 'both']
  else:
    res['sexPref'] = ['both']
  return res

def parse_data_to_frontend(data):
  res = []
  for user in data:
    res.append({
      'firstname': user[0],
      'dateOfBirth': user[1],
      'location': {'lat': user[2], 'lon': user[3]},
      'gender': user[4],
      'tags': user[5],
      'mainImage': user[6],
      'sexPref': user[7],
    })
  return res  