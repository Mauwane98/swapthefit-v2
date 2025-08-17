from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import mongo
from app.utils.security import admin_required
from bson.objectid import ObjectId

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@admin_required()
def dashboard():
    """
    Displays the main admin dashboard with platform analytics.
    """
    user_count = mongo.db.users.count_documents({})
    listing_count = mongo.db.listings.count_documents({})
    # Add more analytics as needed
    return render_template('admin/dashboard.html', user_count=user_count, listing_count=listing_count)

@admin_bp.route('/users')
@login_required
@admin_required()
def manage_users():
    """
    Displays a list of all users for the admin to manage.
    """
    users = mongo.db.users.find()
    return render_template('admin/manage_users.html', users=users)

@admin_bp.route('/delete_user/<user_id>', methods=['POST'])
@login_required
@admin_required()
def delete_user(user_id):
    """
    Handles the deletion of a user by an admin.
    """
    user = mongo.db.users.find_one_or_404({'_id': ObjectId(user_id)})
    if user['_id'] == ObjectId(current_user.id):
        flash("You cannot delete your own admin account.", "danger")
        return redirect(url_for('admin.manage_users'))
    
    mongo.db.users.delete_one({'_id': ObjectId(user_id)})
    flash(f"User '{user['username']}' has been deleted successfully.", "success")
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/listings')
@login_required
@admin_required()
def manage_listings():
    """
    Displays all listings for the admin to manage.
    """
    listings = mongo.db.listings.find()
    return render_template('admin/manage_listings.html', listings=listings)