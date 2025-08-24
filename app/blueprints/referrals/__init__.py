from flask import Blueprint

referrals_bp = Blueprint('referrals', __name__)

from . import routes