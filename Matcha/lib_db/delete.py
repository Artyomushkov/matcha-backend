from lib_db.db import get_db

def delete_query(table_name, query_dict: dict):
    conditions = ""
    for key in query_dict.keys():
        conditions += key + " = %s AND "
    conditions = conditions[0:len(conditions) - 5]
    query = "DELETE FROM " + table_name + " WHERE " + conditions
    db = get_db()
    with db.cursor() as cur:
        try:
            cur.execute(query, tuple(query_dict.values()))
        finally:
            db.commit()