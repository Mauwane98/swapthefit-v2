from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.models.users import User
from app.models.listings import Listing
from app.models.swaps import SwapRequest
from app.models.reviews import Review
from app.models.notifications import Notification
from app.blueprints.auth.routes import roles_required # Import the custom roles_required decorator

admin_bp = Blueprint('admin', __name__, url_prefix='/admin', template_folder='templates')

@admin_bp.route('/dashboard')
@login_required
@roles_required('admin') # Only users with 'admin' role can access
def dashboard():
    """
    Displays the main admin dashboard with platform analytics.
    Fetches counts of users, listings, pending swaps, and unread notifications.
    """
    # Get counts of all users, listings, pending swaps, and unread notifications
    user_count = User.objects.count()
    listing_count = Listing.objects.count()
    pending_swaps_count = SwapRequest.objects(status='pending').count()
    unread_notifications_count = Notification.objects(read=False).count() # Total unread notifications across all users

    return render_template(
        'admin/dashboard.html', 
        user_count=user_count, 
        listing_count=listing_count,
        pending_swaps_count=pending_swaps_count,
        unread_notifications_count=unread_notifications_count,
        title='Admin Dashboard'
    )

@admin_bp.route('/users')
@login_required
@roles_required('admin') # Only users with 'admin' role can access
def manage_users():
    """
    Displays a list of all users for the admin to manage.
    Includes filtering and sorting options.
    """
    # Fetch all users, sorted by date_joined (newest first)
    users = User.objects.order_by('-date_joined').all()
    return render_template('admin/manage_users.html', users=users, title='Manage Users')

@admin_bp.route('/delete_user/<string:user_id>', methods=['POST'])
@login_required
@roles_required('admin') # Only users with 'admin' role can access
def delete_user(user_id):
    """
    Handles the deletion of a user by an admin.
    Also deletes all associated data (listings, messages, reviews, swaps, notifications).
    """
    user_to_delete = User.objects(id=user_id).first()
    if not user_to_delete:
        flash("User not found.", "danger")
        return redirect(url_for('admin.manage_users'))
    
    # Prevent admin from deleting their own account
    if str(user_to_delete.id) == str(current_user.id):
        flash("You cannot delete your own admin account.", "danger")
        return redirect(url_for('admin.manage_users'))
    
    try:
        # Delete all associated data for the user
        Listing.objects(owner=user_to_delete.id).delete()
        Message.objects(Q(sender=user_to_delete.id) | Q(recipient=user_to_delete.id)).delete()
        Review.objects(Q(reviewer=user_to_delete.id) | Q(reviewed_user=user_to_delete.id)).delete()
        SwapRequest.objects(Q(proposer=user_to_delete.id) | Q(recipient=user_to_delete.id)).delete()
        Notification.objects(Q(sender=user_to_delete.id) | Q(recipient=user_to_delete.id)).delete()
        
        # Finally, delete the user account
        user_to_delete.delete()
        flash(f"User '{user_to_delete.username}' and all associated data have been deleted successfully.", "success")
    except Exception as e:
        flash(f"An error occurred while deleting user: {e}", "danger")
        current_app.logger.error(f"Error deleting user {user_id}: {e}")

    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/listings')
@login_required
@roles_required('admin') # Only users with 'admin' role can access
def manage_listings():
    """
    Displays all listings for the admin to manage.
    Admins can view, edit, or delete any listing.
    """
    # Fetch all listings, sorted by creation date (newest first)
    listings = Listing.objects.order_by('-created_at').all()
    return render_template('admin/manage_listings.html', listings=listings, title='Manage Listings')

@admin_bp.route('/toggle_listing_status/<string:listing_id>', methods=['POST'])
@login_required
@roles_required('admin')
def toggle_listing_status(listing_id):
    """
    Allows an admin to toggle the 'is_active' status of a listing.
    """
    listing = Listing.objects(id=listing_id).first()
    if not listing:
        flash("Listing not found.", "danger")
        return redirect(url_for('admin.manage_listings'))
    
    try:
        listing.is_active = not listing.is_active
        listing.save()
        status_message = "deactivated" if not listing.is_active else "activated"
        flash(f"Listing '{listing.title}' has been {status_message}.", "success")
    except Exception as e:
        flash(f"An error occurred while toggling listing status: {e}", "danger")
        current_app.logger.error(f"Error toggling listing status for {listing_id}: {e}")

    return redirect(url_for('admin.manage_listings'))

@admin_bp.route('/view_swap_requests')
@login_required
@roles_required('admin')
def view_swap_requests():
    """
    Allows an admin to view all swap requests.
    """
    swap_requests = SwapRequest.objects.order_by('-date_proposed').all()
    return render_template('admin/view_swap_requests.html', swap_requests=swap_requests, title='Manage Swap Requests')

@admin_bp.route('/view_reviews')
@login_required
@roles_required('admin')
def view_reviews():
    """
    Allows an admin to view all reviews.
    """
    reviews = Review.objects.order_by('-date_posted').all()
    return render_template('admin/view_reviews.html', reviews=reviews, title='Manage Reviews')

@admin_bp.route('/view_notifications')
@login_required
@roles_required('admin')
def view_notifications():
    """
    Allows an admin to view all notifications.
    """
    notifications = Notification.objects.order_by('-created_at').all()
    return render_template('admin/view_notifications.html', notifications=notifications, title='Manage Notifications')
