from flask import jsonify, request, current_app
from functools import wraps
from lib_db.select import select_query
import jwt

def token_required(f):
  @wraps(f)
  def decorator(*args, **kwargs):
    token = request.headers.get('Authorization')
    if not token:
      return jsonify({'error': 'a jwt token is missing'}), 401
    try:
      data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
    except:
      return jsonify({'error': 'token is invalid'}), 401
    return f(*args, **kwargs)
  return decorator