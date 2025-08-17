import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models.users import User
from app.blueprints.profile.forms import EditProfileForm # Import the new form

profile_bp = Blueprint('profile', __name__, url_prefix='/profile', template_folder='templates')

# Directory for uploaded profile pictures
UPLOAD_FOLDER = os.path.join(current_app.root_path, 'static', 'profile_pics')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@profile_bp.route('/<string:user_id>')
def user_profile(user_id):
    """
    Displays a user's public profile. This route is also handled in listings_bp.
    This can be kept for direct access to profile via /profile/<user_id>.
    """
    user_profile_obj = User.objects(id=user_id).first()
    if not user_profile_obj:
        abort(404) # User not found

    # You might fetch listings or reviews here if this route is the primary profile view
    # For now, it delegates some display to listings.user_profile
    return redirect(url_for('listings.user_profile', user_id=user_id))


@profile_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """
    Allows the current logged-in user to edit their profile information.
    """
    form = EditProfileForm(obj=current_user) # Populate form with current user's data

    if form.validate_on_submit():
        # Check for username change
        if form.username.data != current_user.username:
            # The form's validate_username already checks for uniqueness
            current_user.username = form.username.data
            
        # Check for email change
        if form.email.data != current_user.email:
            # The form's validate_email already checks for uniqueness
            current_user.email = form.email.data
        
        # Update about_me field
        current_user.about_me = form.about_me.data # Ensure 'about_me' field exists in User model

        # Handle profile picture upload
        if form.profile_pic.data:
            try:
                # Secure filename to prevent directory traversal attacks
                filename = secure_filename(form.profile_pic.data.filename)
                # Construct the full path to save the file
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                # Save the uploaded file
                form.profile_pic.data.save(file_path)
                # Update the user's profile_pic URL
                current_user.profile_pic = url_for('static', filename=f'profile_pics/{filename}')
                flash('Profile picture updated!', 'success')
            except Exception as e:
                current_app.logger.error(f"Error saving profile picture: {e}")
                flash('Failed to upload profile picture. Please try again.', 'danger')
                # It's important to return here or ensure the form re-renders with errors
                return render_template('profile/profile.html', title='Edit Profile', form=form)

        try:
            current_user.save() # Save the updated user object to MongoDB
            flash('Your profile has been updated successfully!', 'success')
            return redirect(url_for('profile.user_profile', user_id=current_user.id))
        except Exception as e:
            current_app.logger.error(f"Error updating user profile: {e}")
            flash('An error occurred while updating your profile. Please try again.', 'danger')
            
    # For GET requests or if form validation fails on POST
    return render_template('profile/profile.html', title='Edit Profile', form=form)

