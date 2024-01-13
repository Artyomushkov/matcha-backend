from flask import Blueprint

bp = Blueprint('tags', __name__, url_prefix='/tags')
from tags import routes