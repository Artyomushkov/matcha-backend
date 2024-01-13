import psycopg2
from lib_db.insert import insert_query
import uuid
from tags import bp

TABLE_NAME = 'tags'

def add_tags_to_db(tags_list):
  for tag in tags_list:
    id = id = uuid.uuid4()
    try:
      insert_query(TABLE_NAME, {'id': id, 'tag': tag})
    except psycopg2.errors.UniqueViolation as err:
      continue
  