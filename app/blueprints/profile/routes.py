# app/blueprints/profile/routes.py
from flask import Blueprint, render_template, url_for, flash, redirect, request, current_app
from flask_login import login_required, current_user
from app.models.users import User
from app.blueprints.profile.forms import EditProfileForm
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
    Displays and allows editing of the current user's profile.
    """
    form = EditProfileForm(obj=current_user)
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.save()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('profile.profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('profile/profile.html', title='Profile', image_file=image_file, form=form)

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
    
    return render_template('profile/blocked_users.html', title='Blocked Users', blocked_users=blocked_users)