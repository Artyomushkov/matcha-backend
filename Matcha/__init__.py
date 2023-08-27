import os
from dotenv import load_dotenv
from flask import Flask


def create_app():
    
    load_dotenv()  
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY"),
        DB_USER=os.environ.get("DB_USER"),
        DB_HOST=os.environ.get("DB_HOST"),
        DB_PORT=os.environ.get("DB_PORT"),
        DB_NAME=os.environ.get("DB_NAME"),
        DB_PASSWORD=os.environ.get("DB_PASSWORD"),
        PASSWORD_HASH=os.environ.get("PASSWORD_HASH")
    )
    
    from . import db
    db.init_app(app)

    from Matcha.profile import bp as profile_bp
    app.register_blueprint(profile_bp)

    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    return app