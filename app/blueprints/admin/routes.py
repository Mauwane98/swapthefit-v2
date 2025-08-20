# app/blueprints/admin/routes.py
from flask import Blueprint, render_template, url_for, flash, redirect, request, abort
from flask_login import login_required, current_user
from app.models.users import User
from app.models.listings import Listing
from app.models.notifications import Notification
from app.models.reviews import Review # For viewing user reviews
from app.models.swaps import SwapRequest # For viewing swap requests
from app.models.reports import Report # For viewing reports
from app.models.donations import Donation # For viewing donations
from app.models.disputes import Dispute
from app.extensions import db
from app.utils.security import roles_required
from mongoengine.queryset.visitor import Q
from app.blueprints.admin.forms import UserManagementForm, ListingModerationForm # Assuming these forms exist
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

# Admin Dashboard Overview (can be expanded)
@admin_bp.route("/")
@admin_bp.route("/dashboard")
@login_required
@roles_required('admin')
def dashboard():
    """
    Admin dashboard overview.
    """
    # Example: Fetch some summary statistics for the dashboard
    total_users = User.objects.count()
    active_listings = Listing.objects(is_available=True).count()
    pending_reports = Report.objects(status='pending').count()
    open_disputes = Dispute.objects(status__in=['open', 'under review']).count()

    return render_template('admin/dashboard.html', 
                           title='Admin Dashboard',
                           total_users=total_users,
                           active_listings=active_listings,
                           pending_reports=pending_reports,
                           open_disputes=open_disputes)


# --- User Management ---
@admin_bp.route("/manage_users")
@login_required
@roles_required('admin')
def manage_users():
    """
    Admin route to view and manage all users.
    Allows filtering and searching.
    """
    query = User.objects
    search_term = request.args.get('search_term')
    role_filter = request.args.get('role_filter')
    status_filter = request.args.get('status_filter') # 'active', 'inactive'

    if search_term:
        query = query.filter(
            Q(username__icontains=search_term) |
            Q(email__icontains=search_term)
        )
    if role_filter and role_filter != 'all':
        query = query.filter(role=role_filter)
    if status_filter:
        if status_filter == 'active':
            query = query.filter(active=True)
        elif status_filter == 'inactive':
            query = query.filter(active=False)

    users = query.order_by('-date_joined')
    
    # Pass filter options for dropdowns
    roles = ['all', 'parent', 'school', 'ngo', 'admin']
    statuses = ['all', 'active', 'inactive']

    return render_template('admin/manage_users.html', 
                           title='Manage Users', 
                           users=users,
                           search_term=search_term,
                           role_filter=role_filter,
                           status_filter=status_filter,
                           roles=roles,
                           statuses=statuses)

@admin_bp.route("/user/<string:user_id>/edit", methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def edit_user(user_id):
    """
    Admin route to edit a user's details, including role and active status.
    """
    user = User.objects(id=user_id).first_or_404()
    form = UserManagementForm(obj=user) # Populate form with user data

    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        user.active = form.active.data # Update active status

        # Prevent admin from deactivating themselves
        if user.id == current_user.id and not user.active:
            flash('You cannot deactivate your own admin account.', 'danger')
            return redirect(url_for('admin.manage_users'))

        user.save()
        flash(f'User {user.username} updated successfully!', 'success')
        return redirect(url_for('admin.manage_users'))
    
    elif request.method == 'GET':
        # Populate form fields on GET request
        form.username.data = user.username
        form.email.data = user.email
        form.role.data = user.role
        form.active.data = user.active

    return render_template('admin/edit_user.html', title='Edit User', form=form, user=user)

@admin_bp.route("/user/<string:user_id>/delete", methods=['POST'])
@login_required
@roles_required('admin')
def delete_user(user_id):
    """
    Admin route to delete a user.
    """
    user_to_delete = User.objects(id=user_id).first_or_404()

    # Prevent admin from deleting themselves
    if user_to_delete.id == current_user.id:
        flash('You cannot delete your own admin account.', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    # Optionally, handle associated data (listings, messages, etc.)
    # e.g., set listing.user_id to None or delete cascade
    
    user_to_delete.delete()
    flash(f'User {user_to_delete.username} deleted successfully!', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route("/user/<string:user_id>/suspend", methods=['POST'])
@login_required
@roles_required('admin')
def suspend_user(user_id):
    """
    Admin route to suspend a user (set active status to False).
    """
    user_to_suspend = User.objects(id=user_id).first_or_404()

    # Prevent admin from suspending themselves
    if user_to_suspend.id == current_user.id:
        flash('You cannot suspend your own admin account.', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    if not user_to_suspend.active:
        flash(f'User {user_to_suspend.username} is already suspended.', 'info')
        return redirect(url_for('admin.manage_users'))

    user_to_suspend.active = False
    user_to_suspend.save()
    flash(f'User {user_to_suspend.username} has been suspended.', 'success')
    return redirect(url_for('admin.manage_users'))

# --- Listing Moderation ---
@admin_bp.route("/manage_listings")
@login_required
@roles_required('admin')
def manage_listings():
    """
    Admin route to view and moderate all listings.
    Allows filtering by status, type, etc.
    """
    from mongoengine.queryset.visitor import Q
    query_params = {}
    search_term = request.args.get('search_term')
    status_filter = request.args.get('status_filter') # 'available', 'pending_pickup', 'donated', 'sold', 'swapped', 'suspended'
    listing_type_filter = request.args.get('listing_type_filter')

    if search_term:
        query_params['$or'] = [
            Q(title__icontains=search_term),
            Q(description__icontains=search_term),
            Q(school_name__icontains=search_term),
            Q(brand__icontains=search_term)
        ]
    if status_filter and status_filter != 'all':
        query_params['status'] = status_filter # Assuming 'status' field in Listing model
    if listing_type_filter and listing_type_filter != 'all':
        query_params['listing_type'] = listing_type_filter

    listings = Listing.objects(**query_params).order_by('-date_posted')

    # Pass filter options for dropdowns
    listing_statuses = ['all', 'available', 'pending_pickup', 'donated', 'sold', 'swapped', 'suspended']
    listing_types = ['all', 'sale', 'swap', 'donation']

    return render_template('admin/manage_listings.html', 
                           title='Manage Listings', 
                           listings=listings,
                           search_term=search_term,
                           status_filter=status_filter,
                           listing_type_filter=listing_type_filter,
                           listing_statuses=listing_statuses,
                           listing_types=listing_types)

@admin_bp.route("/listing/<string:listing_id>/moderate", methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def moderate_listing(listing_id):
    """
    Admin route to moderate a specific listing (e.g., change status, remove).
    """
    listing = Listing.objects(id=listing_id).first_or_404()
    form = ListingModerationForm(obj=listing) # Populate form with listing data

    if form.validate_on_submit():
        listing.status = form.status.data
        listing.is_available = form.is_available.data # Update availability
        listing.is_premium = form.is_premium.data # Allow setting premium status
        listing.save()
        flash(f'Listing "{listing.title}" updated successfully!', 'success')
        return redirect(url_for('admin.manage_listings'))
    
    elif request.method == 'GET':
        form.status.data = listing.status
        form.is_available.data = listing.is_available
        form.is_premium.data = listing.is_premium

    return render_template('admin/moderate_listing.html', title='Moderate Listing', form=form, listing=listing)

@admin_bp.route("/listing/<string:listing_id>/remove", methods=['POST'])
@login_required
@roles_required('admin')
def remove_listing(listing_id):
    """
    Admin route to permanently remove a listing.
    """
    listing_to_remove = Listing.objects(id=listing_id).first_or_404()
    
    # Optionally, delete associated image file
    if listing_to_remove.image_files:
        for image_file in listing_to_remove.image_files:
            if image_file and image_file != 'default.jpg':
                try:
                    image_path = os.path.join(current_app.root_path, 'static/uploads', image_file)
                    if os.path.exists(image_path):
                        os.remove(image_path)
                except Exception as e:
                    current_app.logger.error(f"Error deleting image file {image_file}: {e}")

    listing_to_remove.delete()
    flash(f'Listing "{listing_to_remove.title}" permanently removed.', 'success')
    return redirect(url_for('admin.manage_listings'))

# --- Admin views for other features (already implemented in other blueprints but linked here for admin access) ---
@admin_bp.route("/view_notifications")
@login_required
@roles_required('admin')
def view_notifications():
    """
    Admin view for all notifications (can be filtered).
    """
    # Re-use the notifications blueprint's index, but potentially with admin filters
    return redirect(url_for('notifications.index', filter='all')) # Admins can see all notifications for themselves

@admin_bp.route("/view_reviews")
@login_required
@roles_required('admin')
def view_reviews():
    """
    Admin view for all reviews (can be filtered).
    """
    reviews = Review.objects.order_by('-date_posted')
    # You might want to add filters here (e.g., by user, by rating)
    return render_template('admin/view_reviews.html', title='Manage Reviews', reviews=reviews)

@admin_bp.route("/view_swap_requests")
@login_required
@roles_required('admin')
def view_swap_requests():
    """
    Admin view for all swap requests."""
    swap_requests = SwapRequest.objects.order_by('-request_date')
    # You might want to add filters here (e.g., by status)
    return render_template('admin/view_swap_requests.html', title='Manage Swap Requests', swap_requests=swap_requests)

@admin_bp.route("/view_donations")
@login_required
@roles_required('admin')
def view_donations():
    """
    Admin view for all donation records."""
    donations = Donation.objects.order_by('-donation_date')
    # You might want to add filters here (e.g., by status, recipient)
    return render_template('admin/view_donations.html', title='Manage Donations', donations=donations)

@admin_bp.route("/listing/<string:listing_id>/remove", methods=['POST'])
@login_required
@roles_required('admin')
def remove_listing(listing_id):
    """
    Admin route to permanently remove a listing.
    """
    listing_to_remove = Listing.objects(id=listing_id).first_or_404()
    
    # Optionally, delete associated image file
    if listing_to_remove.image_files:
        for image_file in listing_to_remove.image_files:
            if image_file and image_file != 'default.jpg':
                try:
                    image_path = os.path.join(current_app.root_path, 'static/uploads', image_file)
                    if os.path.exists(image_path):
                        os.remove(image_path)
                except Exception as e:
                    current_app.logger.error(f"Error deleting image file {image_file}: {e}")

    listing_to_remove.delete()
    flash(f'Listing "{listing_to_remove.title}" permanently removed.', 'success')
    return redirect(url_for('admin.manage_listings'))

# --- Admin views for other features (already implemented in other blueprints but linked here for admin access) ---
@admin_bp.route("/view_notifications")
@login_required
@roles_required('admin')
def view_notifications():
    """
    Admin view for all notifications (can be filtered).
    """
    # Re-use the notifications blueprint's index, but potentially with admin filters
    return redirect(url_for('notifications.index', filter='all')) # Admins can see all notifications for themselves

@admin_bp.route("/view_reviews")
@login_required
@roles_required('admin')
def view_reviews():
    """Admin view for all reviews (can be filtered)."""
    reviews = Review.objects.order_by('-date_posted')
    # You might want to add filters here (e.g., by user, by rating)
    return render_template('admin/view_reviews.html', title='Manage Reviews', reviews=reviews)

@admin_bp.route("/view_swap_requests")
@login_required
@roles_required('admin')
def view_swap_requests():
    """Admin view for all swap requests."""
    swap_requests = SwapRequest.objects.order_by('-request_date')
    # You might want to add filters here (e.g., by status)
    return render_template('admin/view_swap_requests.html', title='Manage Swap Requests', swap_requests=swap_requests)

@admin_bp.route("/view_donations")
@login_required
@roles_required('admin')
def view_donations():
    """
    Admin view for all donation records."""
    donations = Donation.objects.order_by('-donation_date')
    # You might want to add filters here (e.g., by status, recipient)
    return render_template('admin/view_donations.html', title='Manage Donations', donations=donations)