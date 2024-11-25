from flask import Blueprint

bp = Blueprint('profile', __name__, url_prefix='/profile')
from profile import routes
from profile import search
from profile import mail_routes