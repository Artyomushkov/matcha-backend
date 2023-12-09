import datetime
import time
from flask import request

from lib_db.select import select_query
from profile.exceptions import NotFoundError
import geopy.distance

def is_get_params_valid_search(request: request):
  if request.args.get('id') == None or \
    request.args.get('ageFrom') == None or \
    request.args.get('ageTo') == None or \
    request.args.get('fameFrom') == None or \
    request.args.get('fameTo') == None or \
    request.args.get('lat') == None or \
    request.args.get('lon') == None or \
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

def get_age_range(age_from, age_to):
  if age_from == None:
    age_from = 18
  if age_to == None:
    age_to = 100
  year_from = 2023 - int(age_to)
  year_to = 2023 - int(age_from)
  if year_from < 1900 or year_to < 1900 or year_from > 2023 or year_to > 2023 or year_from > year_to:
    raise Exception('Invalid age range')
  time_from = time.mktime(datetime.datetime(year=year_from, month=1, day=1).timetuple())
  time_to = time.mktime(datetime.datetime(year=year_to, month=1, day=1).timetuple())
  return time_from, time_to

def get_fame_range(fame_from, fame_to):
  if fame_from == None:
    fame_from = 0
  if fame_to == None:
    fame_to = 5
  fame_from = float(fame_from)
  fame_to = float(fame_to)
  if fame_from < 0 or fame_to < 0 or fame_from > 5 or fame_to > 5 or fame_from > fame_to:
    raise Exception('Invalid fame range')
  return fame_from, fame_to

def get_geo_range(location, radius):
  if location == None:
    raise Exception('Invalid geo data')
  if location.get('lat') == None or location.get('lon') == None:
    raise Exception('Invalid geo data')
  if radius == None:
    return -90, 90, -180, 180
  lat = float(location.get('lat'))
  lon = float(location.get('lon'))
  radius = float(radius)
  if lat < -90 or lat > 90 or lon < -180 or lon > 180 or radius < 0:
    raise Exception('Invalid geo data')
  northPoint = geopy.distance.distance(kilometers=radius).destination(geopy.Point(lat, lon), 0).latitude
  southPoint = geopy.distance.distance(kilometers=radius).destination(geopy.Point(lat, lon), 180).latitude
  westPoint = geopy.distance.distance(kilometers=radius).destination(geopy.Point(lat, lon), 270).longitude
  eastPoint = geopy.distance.distance(kilometers=radius).destination(geopy.Point(lat, lon), 90).longitude
  return southPoint, northPoint, westPoint, eastPoint

def parse_data_to_frontend(data):
  res = []
  for user in data:
    res.append({
      'id': user[0],
      'firstname': user[1],
      'dateOfBirth': user[2],
      'location': {'lat': user[3], 'lon': user[4]},
      'gender': user[5],
      'tags': user[6],
      'mainImage': user[7],
      'sexPref': user[8],
    })
  return res

def create_order_condition(order):
  if order == None:
    return ""
  if order == 'most_young':
    return " ORDER BY dateOfBirth DESC"
  elif order == 'least_young':
    return " ORDER BY dateOfBirth ASC"
  elif order == 'most_famed':
    return " ORDER BY fameRating DESC"
  elif order == 'more_interests':
    return " ORDER BY array_inter_length() DESC"
  else:
    raise Exception('Invalid order')
  