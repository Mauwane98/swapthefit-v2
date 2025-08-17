from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models.users import User
from app.blueprints.auth.forms import LoginForm, RegistrationForm, RequestResetForm, ResetPasswordForm
# Utilities are imported inside functions to prevent circular import errors.

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('listings.marketplace'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.name.data, email=form.email.data, password_hash="", role='user')
        user.set_password(form.password.data)
        user.save()
        flash('Your account has been created! You are now able to log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('listings.marketplace'))
    form = LoginForm()
    if form.validate_on_submit():
        print(f"Attempting login for email: {form.email.data}")
        user = User.find_by_email(form.email.data)
        if user:
            print(f"User found: {user.email}")
            if user.check_password(form.password.data):
                print("Password check successful.")
                login_user(user, remember=form.remember.data)
                return redirect(url_for('listings.dashboard'))
            else:
                print("Password check failed.")
                flash('Login Unsuccessful. Please check email and password.', 'danger')
        else:
            print("User not found.")
            flash('Login Unsuccessful. Please check email and password.', 'danger')
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('landing_bp.index'))

@auth_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    from app.utils.emails import send_password_reset_email
    if current_user.is_authenticated:
        return redirect(url_for('listings.marketplace'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.find_by_email(form.email.data)
        send_password_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_request.html', title='Reset Password', form=form)

@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('listings.marketplace'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('auth.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.save()
        flash('Your password has been updated! You are now able to log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_token.html', title='Reset Password', form=form)
