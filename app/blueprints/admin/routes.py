from flask import Blueprint, render_template
from flask_jwt_extended import jwt_required
from app.utils.security import admin_required
from app.extensions import mongo
from app.models.listings import Listing

admin_bp = Blueprint('admin_bp', __name__,
                     template_folder='templates',
                     static_folder='static')

@admin_bp.route('/dashboard', endpoint='dashboard') # Added unique endpoint
@jwt_required
@admin_required()
def dashboard():
    """Displays the main admin dashboard with a list of all users."""
    users = mongo.db.users.find().sort("created_at", -1)
    return render_template('admin/dashboard.html', users=users)

@admin_bp.route('/listings', endpoint='manage_listings') # Added unique endpoint
@jwt_required
@admin_required()
def manage_listings():
    """Displays a list of all listings for admin management."""
    listings = Listing.find_all_with_owner_info()
    return render_template('admin/manage_listings.html', listings=listings)
