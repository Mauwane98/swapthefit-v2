from flask import Blueprint

sponsored_content_bp = Blueprint('sponsored_content', __name__)

from . import routes