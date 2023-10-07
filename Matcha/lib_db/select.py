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

def select_for_search(id, sex_info):
    fields_needed = "firstname, dateOfBirth, gpslat, gpslon, gender, tagList, mainImage, sexPref"
    query = "SELECT " + fields_needed + " FROM profile WHERE "
    conditions = "id != %s AND ("
    conditions += "gender = %s OR " * len(sex_info["gender"])
    conditions = conditions[0:len(conditions) - 4] + ") AND ("
    conditions += "sexPref = %s OR " * len(sex_info["sexPref"])
    conditions = conditions[0:len(conditions) - 4] + ")"
    query += conditions + ';'
    print(query)
    print(tuple([id] + sex_info["gender"] + sex_info["sexPref"]))
    db = get_db()
    with db.cursor() as cur:
        cur.execute(query, tuple([id] + sex_info["gender"] + sex_info["sexPref"]))
        res = cur.fetchall()
    return res