# app/blueprints/admin/routes.py
from flask import Blueprint, render_template, url_for, flash, redirect, request, current_app
from flask_login import login_required, current_user
from app.models.users import User
from app.models.listings import Listing
from app.models.reviews import Review # For viewing user reviews
from app.models.swaps import SwapRequest # For viewing swap requests
from app.models.reports import Report # For viewing reports
from app.models.donations import Donation # For viewing donations
from app.models.payments import Order # Import Order model
from app.models.disputes import Dispute # Import Dispute model
from app.utils.security import roles_required
from mongoengine.queryset.visitor import Q
from app.blueprints.admin.forms import UserManagementForm, ListingModerationForm, SuspendUserForm, BanUserForm, DeleteUserForm, ToggleListingStatusForm, DeleteListingForm
import os

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
    try:
        total_users = User.objects.count()
        current_app.logger.info(f"Total users: {total_users}")
    except Exception as e:
        current_app.logger.error(f"Error fetching total users: {e}")
        total_users = 0

    try:
        active_listings = Listing.objects(is_available=True).count()
        current_app.logger.info(f"Active listings: {active_listings}")
    except Exception as e:
        current_app.logger.error(f"Error fetching active listings: {e}")
        active_listings = 0

    try:
        pending_reports = Report.objects(status='pending').count()
        current_app.logger.info(f"Pending reports: {pending_reports}")
    except Exception as e:
        current_app.logger.error(f"Error fetching pending reports: {e}")
        pending_reports = 0

    try:
        open_disputes = Dispute.objects(status__in=['open', 'under review']).count()
        current_app.logger.info(f"Open disputes: {open_disputes}")
    except Exception as e:
        current_app.logger.error(f"Error fetching open disputes: {e}")
        open_disputes = 0

    try:
        total_listings = Listing.objects.count()
        current_app.logger.info(f"Total listings: {total_listings}")
    except Exception as e:
        current_app.logger.error(f"Error fetching total listings: {e}")
        total_listings = 0

    try:
        total_sale_listings = Listing.objects(listing_type='sale').count()
        current_app.logger.info(f"Total sale listings: {total_sale_listings}")
    except Exception as e:
        current_app.logger.error(f"Error fetching total sale listings: {e}")
        total_sale_listings = 0

    try:
        total_swap_listings = Listing.objects(listing_type='swap').count()
        current_app.logger.info(f"Total swap listings: {total_swap_listings}")
    except Exception as e:
        current_app.logger.error(f"Error fetching total swap listings: {e}")
        total_swap_listings = 0

    try:
        total_donation_listings = Listing.objects(listing_type='donation').count()
        current_app.logger.info(f"Total donation listings: {total_donation_listings}")
    except Exception as e:
        current_app.logger.error(f"Error fetching total donation listings: {e}")
        total_donation_listings = 0

    try:
        total_completed_swaps = SwapRequest.objects(status='completed').count()
        current_app.logger.info(f"Total completed swaps: {total_completed_swaps}")
    except Exception as e:
        current_app.logger.error(f"Error fetching total completed swaps: {e}")
        total_completed_swaps = 0

    try:
        total_completed_orders = Order.objects(status='completed').count()
        current_app.logger.info(f"Total completed orders: {total_completed_orders}")
    except Exception as e:
        current_app.logger.error(f"Error fetching total completed orders: {e}")
        total_completed_orders = 0

    try:
        total_completed_donations = Donation.objects(status='completed').count()
        current_app.logger.info(f"Total completed donations: {total_completed_donations}")
    except Exception as e:
        current_app.logger.error(f"Error fetching total completed donations: {e}")
        total_completed_donations = 0

    # Calculate total value of completed orders (assuming price is stored in Listing and linked via Order)
    total_order_value = 0
    try:
        for order in Order.objects(status='completed'):
            if order.listing and order.listing.price:
                total_order_value += order.listing.price
        current_app.logger.info(f"Total order value: {total_order_value}")
    except Exception as e:
        current_app.logger.error(f"Error calculating total order value: {e}")
        total_order_value = 0
    
    # Calculate total value of completed donations (assuming price is stored in Listing and linked via Donation)
    total_donation_value = 0
    try:
        for donation in Donation.objects(status='completed'):
            if donation.listing and donation.listing.price:
                total_donation_value += donation.listing.price
        current_app.logger.info(f"Total donation value: {total_donation_value}")
    except Exception as e:
        current_app.logger.error(f"Error calculating total donation value: {e}")
        total_donation_value = 0

    return render_template('admin/dashboard.html', 
                           title='Admin Dashboard',
                           total_users=total_users,
                           active_listings=active_listings,
                           pending_reports=pending_reports,
                           open_disputes=open_disputes,
                           total_listings=total_listings,
                           total_sale_listings=total_sale_listings,
                           total_swap_listings=total_swap_listings,
                           total_donation_listings=total_donation_listings,
                           total_completed_swaps=total_completed_swaps,
                           total_completed_orders=total_completed_orders,
                           total_completed_donations=total_completed_donations,
                           total_order_value=total_order_value,
                           total_donation_value=total_donation_value)


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

    # Instantiate forms for actions
    suspend_form = SuspendUserForm()
    ban_form = BanUserForm()
    delete_form = DeleteUserForm()

    return render_template('admin/manage_users.html', 
                           title='Manage Users', 
                           users=users,
                           search_term=search_term,
                           role_filter=role_filter,
                           status_filter=status_filter,
                           roles=roles,
                           statuses=statuses,
                           suspend_form=suspend_form,
                           ban_form=ban_form,
                           delete_form=delete_form)

@admin_bp.route("/user/<string:user_id>/edit", methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def edit_user(user_id):
    """
    Admin route to edit a user's details, including role, active, ban status, and ban reason.
    """
    user = User.objects(id=user_id).first_or_404()
    form = UserManagementForm(obj=user) # Populate form with user data

    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        user.active = form.active.data
        user.is_banned = form.is_banned.data
        user.ban_reason = form.ban_reason.data

        # If user is banned, they must also be inactive
        if user.is_banned:
            user.active = False

        # Prevent admin from deactivating or banning themselves
        if user.id == current_user.id and (not user.active or user.is_banned):
            flash('You cannot deactivate or ban your own admin account.', 'danger')
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
        form.is_banned.data = user.is_banned
        form.ban_reason.data = user.ban_reason

    return render_template('admin/edit_user.html', title='Edit User', form=form, user=user)

@admin_bp.route("/user/<string:user_id>/delete", methods=['POST'])
@login_required
@roles_required('admin')
def delete_user(user_id):
    """
    Admin route to delete a user.
    """
    user_to_delete = User.objects(id=user_id).first_or_404()
    form = DeleteUserForm()
    if form.validate_on_submit():
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
    Admin route to suspend a user (set active status to False) with a reason.
    """
    user_to_suspend = User.objects(id=user_id).first_or_404()
    form = SuspendUserForm()
    if form.validate_on_submit():
        reason = request.form.get('reason', '') # Get reason from form data

    # Prevent admin from suspending themselves
    if user_to_suspend.id == current_user.id:
        flash('You cannot suspend your own admin account.', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    if not user_to_suspend.active:
        flash(f'User {user_to_suspend.username} is already suspended.', 'info')
        return redirect(url_for('admin.manage_users'))

    user_to_suspend.active = False
    user_to_suspend.ban_reason = reason # Store the reason
    user_to_suspend.save()
    flash(f'User {user_to_suspend.username} has been suspended.', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route("/user/<string:user_id>/ban", methods=['POST'])
@login_required
@roles_required('admin')
def ban_user(user_id):
    """
    Admin route to permanently ban a user (set is_banned to True and active to False) with a reason.
    """
    user_to_ban = User.objects(id=user_id).first_or_404()
    form = BanUserForm()
    if form.validate_on_submit():
        reason = request.form.get('reason', 'No reason provided.') # Get reason from form data

    # Prevent admin from banning themselves
    if user_to_ban.id == current_user.id:
        flash('You cannot ban your own admin account.', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    if user_to_ban.is_banned:
        flash(f'User {user_to_ban.username} is already banned.', 'info')
        return redirect(url_for('admin.manage_users'))

    user_to_ban.active = False
    user_to_ban.is_banned = True
    user_to_ban.ban_reason = reason # Store the reason
    user_to_ban.save()
    flash(f'User {user_to_ban.username} has been permanently banned.', 'success')
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

    # Instantiate forms for actions
    toggle_status_form = ToggleListingStatusForm()
    delete_listing_form = DeleteListingForm()

    return render_template('admin/manage_listings.html', 
                           title='Manage Listings', 
                           listings=listings,
                           search_term=search_term,
                           status_filter=status_filter,
                           listing_type_filter=listing_type_filter,
                           listing_statuses=listing_statuses,
                           listing_types=listing_types,
                           toggle_status_form=toggle_status_form,
                           delete_listing_form=delete_listing_form)

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
    current_app.logger.info(f"Attempting to remove listing: {listing_id}")
    listing_to_remove = Listing.objects(id=listing_id).first_or_404()
    form = DeleteListingForm()
    if form.validate_on_submit():
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
    else:
        current_app.logger.error(f"DeleteListingForm validation failed: {form.errors}")
        flash('Failed to delete listing due to a form error.', 'danger')
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

@admin_bp.route("/listing/<string:listing_id>/toggle_status", methods=['POST'])
@login_required
@roles_required('admin')
def toggle_listing_status(listing_id):
    """
    Admin route to toggle a listing's availability status.
    """
    listing = Listing.objects(id=listing_id).first_or_404()
    listing.is_available = not listing.is_available
    listing.save()
    flash(f'Listing "{listing.title}" status toggled successfully!', 'success')
    return redirect(url_for('admin.manage_listings'))

@admin_bp.route("/manage_payments")
@login_required
@roles_required('admin')
def manage_payments():
    """
    Admin view for all payment records (orders).
    """
    orders = Order.objects.order_by('-created_at')
    # You might want to add filters here (e.g., by status, user, listing)
    return render_template('admin/manage_payments.html', title='Manage Payments', orders=orders)