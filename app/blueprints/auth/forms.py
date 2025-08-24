from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, RadioField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, Optional
from app.models.users import User

class RegistrationForm(FlaskForm):
    """
    Form for users to create a new account.
    This form collects necessary information for a new user registration,
    including their username, email, password, and chosen role.
    """
    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=2, max=50)],
        render_kw={"placeholder": "Choose a unique username"}
    )
    email = StringField(
        'Email',
        validators=[DataRequired(), Email()],
        render_kw={"placeholder": "Enter your email address"}
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired(), Length(min=6)],
        render_kw={"placeholder": "Create a strong password"}
    )
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[DataRequired(), EqualTo('password', message='Passwords must match')],
        render_kw={"placeholder": "Confirm your password"}
    )
    # Radio buttons for selecting user role.
    # The choices are aligned with the ROLES defined in the User model.
    role = RadioField(
        'I am a',
        choices=[
            ('parent', 'Parent (Individual User)'),
            ('school', 'School (Organization)'),
            ('ngo', 'NGO (Non-profit Organization)')
        ],
        default='parent', # Default selection for convenience
        validators=[DataRequired()]
    )
    
    # This field is optional and can be used for additional details depending on the role.
    # For now, it's a general contact person field, but can be expanded.
    contact_person = StringField(
        'Contact Person Name (Optional)',
        validators=[Optional(), Length(max=100)],
        render_kw={"placeholder": "If applicable (e.g., for schools/NGOs)"}
    )

    referral_code = StringField(
        'Referral Code (Optional)',
        validators=[Optional(), Length(max=20)],
        render_kw={"placeholder": "Enter a referral code if you have one"}
    )
    
    submit = SubmitField('Register')

    def validate_username(self, username):
        """
        Custom validator to check if the username already exists in the database.
        Uses MongoEngine's query method.
        """
        user = User.objects(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')

    def validate_email(self, email):
        """
        Custom validator to check if the email already exists in the database.
        Uses MongoEngine's query method.
        """
        user = User.objects(email=email.data).first()
        if user:
            raise ValidationError('That email is already in use. Please choose a different one.')

class LoginForm(FlaskForm):
    """
    Form for users to log into their existing accounts.
    """
    email = StringField(
        'Email',
        validators=[DataRequired(), Email()],
        render_kw={"placeholder": "Enter your email address"}
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired()],
        render_kw={"placeholder": "Enter your password"}
    )
    remember = BooleanField('Remember Me') # Option to keep the user logged in
    submit = SubmitField('Login')

class RequestResetForm(FlaskForm):
    """
    Form for users to request a password reset email.
    """
    email = StringField(
        'Email',
        validators=[DataRequired(), Email()],
        render_kw={"placeholder": "Enter your registered email"}
    )
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        """
        Custom validator to ensure the email exists in the database before sending a reset link.
        """
        user = User.objects(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account with that email. Please check your spelling or register.')

class ResetPasswordForm(FlaskForm):
    """
    Form for users to set a new password after requesting a reset.
    """
    password = PasswordField(
        'New Password',
        validators=[DataRequired(), Length(min=6)],
        render_kw={"placeholder": "Enter your new password"}
    )
    confirm_password = PasswordField(
        'Confirm New Password',
        validators=[DataRequired(), EqualTo('password', message='Passwords must match')],
        render_kw={"placeholder": "Confirm your new password"}
    )
    submit = SubmitField('Reset Password')
