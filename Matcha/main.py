import os
from dotenv import load_dotenv
from flask import Flask, render_template
from flask_mail import Mail
from flask_socketio import SocketIO, join_room, leave_room, send
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
socketio = SocketIO(app)

user_rooms = {}
    
from lib_db import db
db.init_app(app)

mail = Mail(app)

from profile import bp as profile_bp
app.register_blueprint(profile_bp)

from tags import bp as tags_bp
app.register_blueprint(tags_bp)

from chat import bp as chat_bp
app.register_blueprint(chat_bp)

from notification import bp as notification_bp
app.register_blueprint(notification_bp)

@app.route("/")
def index():
    return render_template("socket_test.html")

@app.route("/chat_test")
def chat_test():
    return render_template('copilot_chat.html')

@app.route("/chat_test2")
def chat_test2():
    return render_template('copilot_chat2.html')

@app.route("/test")
def test():
    return "hooray"

if __name__ == '__main__':
    socketio.run(app)