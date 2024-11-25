from lib_db.db import get_db

def insert_query(table_name, query_dict: dict):
    columns = "("
    for key in query_dict.keys():
        columns += key + ", "
    columns = columns[0:len(columns) - 2] + ")"
    operators = "(" + "%s, " * len(query_dict)
    operators = operators[0:len(operators) - 2] + ")"
    query = "INSERT INTO " + table_name + " " + columns + \
        " VALUES " + operators + ";"
    db = get_db()
    with db.cursor() as cur:
        try:
            cur.execute(query, tuple(query_dict.values()))
        finally:
            db.commit()
     