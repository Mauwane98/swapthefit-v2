from flask import Blueprint, render_template, url_for, flash, redirect, request, current_app
from flask_login import login_required, current_user
from app.models.users import User
from app.blueprints.profile.forms import EditProfileForm, DashboardSettingsForm, UnblockUserForm, PayoutDetailsForm # Import PayoutDetailsForm
from app.blueprints.auth.forms import RequestResetForm, ResetPasswordForm
from app.extensions import db, bcrypt, mail # Import bcrypt and mail for password reset
from flask_mail import Message # For sending emails
import secrets
import os
import json # For handling blocked_users_json

profile_bp = Blueprint('profile', __name__)

def save_picture(form_picture):
    """
    Saves the uploaded profile picture to the static/profile_pics directory.
    Generates a random filename to prevent collisions.
    """
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_fn)

    # Resize image if necessary (Pillow/PIL could be used here)
    # For now, just save it directly
    form_picture.save(picture_path)
    return picture_fn

@profile_bp.route("/profile", methods=['GET', 'POST'])
@login_required
def profile():
    """
    Displays and allows editing of the current user's profile and dashboard settings.
    """
    edit_form = EditProfileForm(obj=current_user)
    dashboard_settings_form = DashboardSettingsForm(obj=current_user) # Instantiate new form

    if request.method == 'POST':
        if edit_form.submit.data and edit_form.validate(): # Check which form was submitted
            if edit_form.profile_pic.data:
                picture_file = save_picture(edit_form.profile_pic.data)
                current_user.image_file = picture_file
            current_user.username = edit_form.username.data
            current_user.email = edit_form.email.data
            current_user.save()
            flash('Your account has been updated!', 'success')
            return redirect(url_for('profile.profile'))
        
        elif dashboard_settings_form.submit.data and dashboard_settings_form.validate(): # Check which form was submitted
            current_user.show_my_listings_on_dashboard = dashboard_settings_form.show_my_listings_on_dashboard.data
            current_user.show_swap_activity_on_dashboard = dashboard_settings_form.show_swap_activity_on_dashboard.data
            current_user.show_account_summary_on_dashboard = dashboard_settings_form.show_account_summary_on_dashboard.data
            current_user.show_activity_feed_on_dashboard = dashboard_settings_form.show_activity_feed_on_dashboard.data
            current_user.save()
            flash('Your dashboard settings have been updated!', 'success')
            return redirect(url_for('profile.profile'))
        else:
            flash('Please correct the errors in the form.', 'danger')

    elif request.method == 'GET':
        edit_form.username.data = current_user.username
        edit_form.email.data = current_user.email
        # Populate dashboard settings form on GET request
        dashboard_settings_form.show_my_listings_on_dashboard.data = current_user.show_my_listings_on_dashboard
        dashboard_settings_form.show_swap_activity_on_dashboard.data = current_user.show_swap_activity_on_dashboard
        dashboard_settings_form.show_account_summary_on_dashboard.data = current_user.show_account_summary_on_dashboard
        dashboard_settings_form.show_activity_feed_on_dashboard.data = current_user.show_activity_feed_on_dashboard

    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template(
        'profile/profile.html', 
        title='Profile', 
        image_file=image_file, 
        edit_form=edit_form, # Renamed to edit_form
        dashboard_settings_form=dashboard_settings_form # Pass new form
    )

@profile_bp.route("/profile/payout_details", methods=['GET', 'POST'])
@login_required
def payout_details():
    """
    Allows sellers (users with role 'school' or 'ngo') to enter and update their bank details for payouts.
    """
    if not (current_user.has_role('school') or current_user.has_role('ngo')):
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('profile.profile'))

    form = PayoutDetailsForm(obj=current_user)

    if form.validate_on_submit():
        current_user.bank_name = form.bank_name.data
        current_user.account_number = form.account_number.data
        current_user.account_name = form.account_name.data
        # paystack_recipient_code will be set when creating recipient via Paystack API
        current_user.save()
        flash('Your payout details have been updated!', 'success')
        return redirect(url_for('profile.profile'))

    elif request.method == 'GET':
        form.bank_name.data = current_user.bank_name
        form.account_number.data = current_user.account_number
        form.account_name.data = current_user.account_name

    return render_template('profile/payout_details.html', title='Payout Details', form=form)

# --- User Blocking Feature Routes ---
@profile_bp.route("/user/<string:user_id>/block", methods=['POST'])
@login_required
def block_user(user_id):
    """
    Allows the current user to block another user.
    """
    user_to_block = User.objects(id=user_id).first_or_404()

    if current_user.id == user_to_block.id:
        flash('You cannot block yourself!', 'danger')
        return redirect(url_for('listings.user_profile', user_id=user_id))

    if current_user.is_blocking(user_id):
        flash(f'You have already blocked {user_to_block.username}.', 'info')
    else:
        current_user.add_blocked_user(user_id)
        current_user.save()
        flash(f'You have blocked {user_to_block.username}. You will no longer receive messages or see their listings.', 'success')
    
    return redirect(url_for('listings.user_profile', user_id=user_id))

@profile_bp.route("/user/<string:user_id>/unblock", methods=['POST'])
@login_required
def unblock_user(user_id):
    """
    Allows the current user to unblock another user.
    """
    user_to_unblock = User.objects(id=user_id).first_or_404()

    if current_user.id == user_to_unblock.id:
        flash('You cannot unblock yourself!', 'danger')
        return redirect(url_for('listings.user_profile', user_id=user_id))

    if not current_user.is_blocking(user_id):
        flash(f'You are not blocking {user_to_unblock.username}.', 'info')
    else:
        current_user.remove_blocked_user(user_id)
        current_user.save()
        flash(f'You have unblocked {user_to_unblock.username}.', 'success')
    
    return redirect(url_for('listings.user_profile', user_id=user_id))

@profile_bp.route("/profile/blocked_users")
@login_required
def view_blocked_users():
    """
    Displays a list of users blocked by the current user.
    """
    blocked_user_ids = current_user.get_blocked_users()
    blocked_users = User.objects(id__in=blocked_user_ids)
    
    form = UnblockUserForm()
    return render_template('profile/blocked_users.html', title='Blocked Users', blocked_users=blocked_users, form=form)