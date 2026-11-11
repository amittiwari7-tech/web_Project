from flask import Blueprint

recharge_bp = Blueprint('recharge', __name__, template_folder='templates',url_prefix='/recharge')

from . import routes