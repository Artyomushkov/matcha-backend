from flask import Blueprint

bp = Blueprint('profile', __name__, url_prefix='/profile')
from Matcha.profile import routes