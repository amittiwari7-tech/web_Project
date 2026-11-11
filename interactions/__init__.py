from flask import Blueprint

interactions_bp = Blueprint('interactions', __name__, template_folder='templates')
from . import routes