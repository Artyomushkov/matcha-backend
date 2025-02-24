from flask import Blueprint

bp = Blueprint('status', __name__, url_prefix='/status')
from .socket_handle import *