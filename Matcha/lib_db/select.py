from Matcha.db import get_db

def select_query(table_name, fields_needed, query_dict: dict):
    query = "SELECT " + fields_needed + " FROM " + table_name + " WHERE "
    conditions = ""
    for key in query_dict.keys():
        conditions += key + " = %s AND "
    conditions = conditions[0:len(conditions) - 5]
    query += conditions + ';'
    db = get_db()
    with db.cursor() as cur:
        cur.execute(query, tuple(query_dict.values()))
        res = cur.fetchall()
    return res