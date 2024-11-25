from flask import Blueprint

bp = Blueprint('tag', __name__, url_prefix='/tag')
from tags import routes