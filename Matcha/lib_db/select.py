from lib_db.db import get_db

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

def select_for_search(id, sex_info, age_range, fame_range, geo_range, tags, page_num, order_condition, order_data):
    fields_needed = "id, firstname, dateOfBirth, gpslat, gpslon, gender, tagList, mainImage, sexPref"
    query = "SELECT " + fields_needed + " FROM profile WHERE "
    conditions = "id != %s AND ("
    conditions += "gender = %s OR " * len(sex_info["gender"])
    conditions = conditions[0:len(conditions) - 4] + ") AND ("
    conditions += "sexPref = %s OR " * len(sex_info["sexPref"])
    conditions = conditions[0:len(conditions) - 4] + ")"
    conditions += " AND dateOfBirth BETWEEN %s AND %s"
    conditions += " AND fameRating BETWEEN %s AND %s"
    conditions += " AND gpslat BETWEEN %s AND %s"
    conditions += " AND gpslon BETWEEN %s AND %s"
    if tags != None:
        conditions += " AND %s = ANY(tagList)" * len(tags)
    conditions += order_condition
    conditions += " LIMIT 10 OFFSET %s"
    query += conditions + ';'
    print(query)
    db = get_db()
    with db.cursor() as cur:
        data = (id,) + tuple(sex_info["gender"]) + tuple(sex_info["sexPref"]) + (age_range[0], age_range[1], 
                fame_range[0], fame_range[1], geo_range[0], geo_range[1], geo_range[2], geo_range[3]) + \
                tuple(tags if tags != None else []) + \
                ((order_data, (int(page_num) - 1) * 10) if order_data != None else ((int(page_num) - 1) * 10,))
        print(data)
        cur.execute(query, data)
        res = cur.fetchall()
    return res