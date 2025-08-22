from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.blueprints.auth.forms import RegistrationForm, LoginForm, RequestResetForm, ResetPasswordForm
from wtforms.validators import ValidationError
from app.models.users import User
from app.utils.emails import send_password_reset_email, send_welcome_email
import datetime
# Import the roles_required decorator from app.utils.security
 
# Import the activity logger
from app.utils.activity_logger import log_activity

auth_bp = Blueprint('auth', __name__, template_folder='templates')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handles user registration.
    - Displays a registration form on GET request.
    - Processes form submission on POST request:
      - Validates form data.
      - Hashes password using bcrypt.
      - Creates a new User object and saves it to MongoDB.
      - Sends a welcome email to the new user.
      - Flashes success/error messages.
      - Redirects to login page on successful registration.
    """
    # If a user is already logged in, redirect them away from the registration page.
    if current_user.is_authenticated:
        flash('You are already registered and logged in.', 'info')
        return redirect(url_for('landing_bp.index')) # Redirect to landing or dashboard

    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            # Create a new User instance
            user = User(
                username=form.username.data,
                email=form.email.data,
                role=form.role.data, # Assign role based on form selection
                image_file='default.jpg', # Explicitly set default image file
                active=True # Explicitly set user as active
            )
            # Set the password using the bcrypt-hashing method
            user.set_password(form.password.data)

            # Handle optional contact person for school/NGO roles
            if form.role.data in ['school', 'ngo']:
                user.contact_person = form.contact_person.data if form.contact_person.data else None
            else:
                user.contact_person = None # Ensure it's not set for 'parent'

            # Save the new user to the MongoDB database
            user.save()

            # Log user registration activity
            log_activity(
                user_id=user.id,
                action_type='user_registered',
                description=f"New user registered: {user.username} with role {user.role}",
                payload={'email': user.email, 'role': user.role},
                request_obj=request # Pass the request object to capture IP
            )

            # Send a welcome email asynchronously
            send_welcome_email(user.email, user.username)

            flash(f'Account created for {form.username.data}! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except ValidationError as e:
            flash(str(e), 'danger')
        except Exception as e:
            current_app.logger.error(f"Error during user registration: {e}")
            flash('An unexpected error occurred during registration. Please try again.', 'danger')
    return render_template('auth/register.html', title='Register', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handles user login.
    - Displays a login form on GET request.
    - Processes form submission on POST request:
      - Validates form data.
      - Authenticates user against MongoDB.
      - Logs in user using Flask-Login.
      - Flashes success/error messages.
      - Redirects to the next page or default dashboard.
    """
    # If a user is already logged in, redirect them away from the login page.
    if current_user.is_authenticated:
        flash('You are already logged in.', 'info')
        # Redirect based on role if a dashboard system is in place
        if current_user.has_role('admin'):
            return redirect(url_for('admin.dashboard'))
        elif current_user.has_role('school'):
            return redirect(url_for('listings.dashboard')) # Placeholder for school dashboard
        elif current_user.has_role('ngo'):
            return redirect(url_for('listings.ngo_dashboard')) # Placeholder for NGO dashboard
        else: # Default for parent
            return redirect(url_for('listings.dashboard'))


    form = LoginForm()
    if form.validate_on_submit():
        # Find user by email (as email is unique and used for login)
        user = User.objects(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            # Update last login time
            user.last_login = datetime.datetime.utcnow()
            user.save() 
            
            # Log user login activity
            log_activity(
                user_id=user.id,
                action_type='user_login',
                description=f"User logged in: {user.username}",
                payload={'email': user.email},
                request_obj=request # Pass the request object to capture IP
            )
            
            # Redirect to the 'next' page if it exists in the URL parameters,
            # otherwise redirect to the appropriate dashboard based on role.
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            
            if next_page:
                return redirect(next_page)
            elif user.has_role('admin'):
                return redirect(url_for('admin.dashboard'))
            elif user.has_role('school'):
                return redirect(url_for('listings.dashboard')) # Placeholder
            elif user.has_role('ngo'):
                return redirect(url_for('listings.dashboard')) # Placeholder
            else: # Default for parent
                return redirect(url_for('listings.dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
            # Log failed login attempt
            log_activity(
                user_id=None, # No user ID for failed attempt
                action_type='failed_login_attempt',
                description=f"Failed login attempt for email: {form.email.data}",
                payload={'email': form.email.data},
                request_obj=request
            )
    return render_template('auth/login.html', title='Login', form=form)

@auth_bp.route('/logout')
@login_required # Requires user to be logged in to log out
def logout():
    """
    Logs out the current user and redirects to the landing page.
    """
    # Log user logout activity before logging out the user from Flask-Login
    log_activity(
        user_id=current_user.id,
        action_type='user_logout',
        description=f"User logged out: {current_user.username}",
        request_obj=request
    )
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('landing_bp.index'))

@auth_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    """
    Handles requests for password reset.
    - Displays a form to request a reset link on GET.
    - Sends a password reset email on POST after validating email existence.
    """
    # If user is authenticated, they don't need to request a password reset.
    if current_user.is_authenticated:
        return redirect(url_for('landing_bp.index'))
    
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.objects(email=form.email.data).first()
        if user:
            # Log password reset request
            log_activity(
                user_id=user.id,
                action_type='password_reset_requested',
                description=f"Password reset requested for user: {user.username}",
                payload={'email': user.email},
                request_obj=request
            )
            # Send reset email asynchronously
            send_password_reset_email(user.email, user.get_reset_token())
            flash('An email has been sent with instructions to reset your password.', 'info')
        else:
            # Log password reset request for non-existent email (for auditing)
            log_activity(
                user_id=None,
                action_type='password_reset_request_non_existent_email',
                description=f"Password reset requested for non-existent email: {form.email.data}",
                payload={'email': form.email.data},
                request_obj=request
            )
            # Flash message even if email not found to prevent email enumeration attacks
            flash('If an account with that email exists, an email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_request.html', title='Reset Password', form=form)

@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    """
    Handles password reset using a token received via email.
    - Verifies the reset token.
    - Displays a form to set a new password on GET.
    - Updates the user's password on POST if the token is valid and passwords match.
    """
    # If user is authenticated, they don't need to reset password via token.
    if current_user.is_authenticated:
        return redirect(url_for('landing_bp.index'))
    
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token.', 'warning')
        # Log invalid/expired token usage
        log_activity(
            user_id=None, # Token is invalid, so user might not be identifiable
            action_type='invalid_or_expired_reset_token',
            description=f"Attempted password reset with invalid/expired token: {token}",
            request_obj=request
        )
        return redirect(url_for('auth.reset_request'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.save() # Save the user with the new hashed password
        # Log successful password reset
        log_activity(
            user_id=user.id,
            action_type='password_reset_successful',
            description=f"Password successfully reset for user: {user.username}",
            payload={'email': user.email},
            request_obj=request
        )
        flash('Your password has been updated! You are now able to log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_token.html', title='Reset Password', form=form)
