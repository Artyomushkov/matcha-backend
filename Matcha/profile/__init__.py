from flask import Blueprint

bp = Blueprint('profile', __name__, url_prefix='/profile')
from profile import routes
from profile import search