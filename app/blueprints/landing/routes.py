from flask import Blueprint, render_template

# Create a Blueprint object
landing_bp = Blueprint('landing_bp', __name__,
                       template_folder='templates',
                       static_folder='static')

@landing_bp.route('/')
def index():
    """Serves the landing page."""
    return render_template('landing/index.html')