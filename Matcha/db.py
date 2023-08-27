import psycopg2

import click
from flask import current_app, g
import os


def get_db():
    if 'db' not in g:
        g.db = psycopg2.connect(host=current_app.config["DB_HOST"], dbname=current_app.config["DB_NAME"], 
                  user=current_app.config["DB_USER"], password=current_app.config["DB_PASSWORD"],
                  port=current_app.config["DB_PORT"])

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    db = get_db()

    schema_sql = open(os.path.abspath(os.path.dirname(__file__) + '/schema.sql'), "r")
    try:
        with db.cursor() as cur:
            cur.execute(schema_sql.read())
            db.commit()
    finally:
        schema_sql.close()

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')