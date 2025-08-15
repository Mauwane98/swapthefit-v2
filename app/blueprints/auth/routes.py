from flask import Blueprint, render_template, redirect, url_for, flash
from app.blueprints.auth.forms import RegistrationForm
from app.models.users import User

# Create a Blueprint for authentication
auth_bp = Blueprint('auth_bp', __name__,
                    template_folder='templates',
                    static_folder='static')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Create a new user instance
        new_user = User(
            name=form.name.data,
            email=form.email.data,
            role=form.role.data
        )
        new_user.set_password(form.password.data)
        new_user.save()
        
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('auth_bp.login')) # Redirect to login page after
        
    return render_template('auth/register.html', title='Register', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # We will build the login logic here in the next step
    return "Login Page - Coming Soon"
