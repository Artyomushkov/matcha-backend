from lib_db.db import get_db


def update_query(table_name, set_dict: dict, conditions_dict: dict):
    query = "UPDATE " + table_name + " SET "
    updates = ""
    for key in set_dict.keys():
        updates += key + " = %s, "
    updates = updates[0:len(updates) - 2]
    conditions = ""
    for key in conditions_dict.keys():
        conditions += key + " = %s AND "
    conditions = conditions[0:len(conditions) - 5]
    query += updates + " WHERE " + conditions
    print(query)
    print(set_dict)
    db = get_db()
    with db.cursor() as cur:
        cur.execute(query, tuple(set_dict.values()) + tuple(conditions_dict.values()))
        db.commit()