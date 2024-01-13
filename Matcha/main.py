import os
from dotenv import load_dotenv
from flask import Flask
from flask_mail import Mail
from lib_db.db import init_db
from flask_cors import CORS

load_dotenv()  
app = Flask(__name__, instance_relative_config=True)
app.config.from_mapping(
    SECRET_KEY=os.environ.get("SECRET_KEY"),
    DB_USER=os.environ.get("DB_USER"),
    DB_HOST=os.environ.get("DB_HOST"),
    DB_PORT=os.environ.get("DB_PORT"),
    DB_NAME=os.environ.get("DB_NAME"),
    DB_PASSWORD=os.environ.get("DB_PASSWORD"),
    SECURITY_PASSWORD_SALT=os.environ.get("SECURITY_PASSWORD_SALT"),
    MAIL_USERNAME=os.environ.get("MAIL_USERNAME"),
    MAIL_PASSWORD=os.environ.get("MAIL_PASSWORD"),
    MAIL_SERVER=os.environ.get("MAIL_SERVER"),
    MAIL_PORT=os.environ.get("MAIL_PORT"),
    MAIL_USE_TLS=False,
    MAIL_USE_SSL=True
)
CORS(app)
    
from lib_db import db
db.init_app(app)
with app.app_context():
    db.init_db()

mail = Mail(app)

from profile import bp as profile_bp
app.register_blueprint(profile_bp)

from tags import bp as tags_bp
app.register_blueprint(tags_bp)