from flask import Blueprint

bp = Blueprint('chat', __name__, url_prefix='/chat')
from chat import routes
from .sockets import *