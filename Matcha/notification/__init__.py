from flask import Blueprint

bp = Blueprint('notification', __name__, url_prefix='/notification')
from notification import routes
from notification import sockets
from notification import utils
from notification import entities