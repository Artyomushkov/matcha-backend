from flask import jsonify, request
import psycopg2
from lib_db.insert import insert_query
from lib_db.select import select_query
import uuid
from tags import bp

TABLE_NAME = 'tags'

def add_tags_to_db(tags_list):
  for tag in tags_list:
    id = str(uuid.uuid4())
    try:
      insert_query(TABLE_NAME, {'id': id, 'tag': tag})
    except psycopg2.errors.UniqueViolation as err:
      continue
    except Exception as err:
      print(err)

@bp.route('/', methods=['GET'])
def tags():
  prefix = request.args.get('prefix')
  if prefix == None:
    prefix = ""
  query_dict = {'tag': prefix + '%'}
  try:
    res = select_query(TABLE_NAME, 'tag', query_dict)
  except Exception as err:
    return {'error': str(err)}, 500
  return jsonify({'tags': [tag[0] for tag in res]})