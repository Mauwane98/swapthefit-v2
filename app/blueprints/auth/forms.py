from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, RadioField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Optional
from app.models.users import User

class RegistrationForm(FlaskForm):
    """
    Form for users to create a new account.
    """
    # Renamed for clarity - will be either parent's name or organization's name
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = RadioField('I am a', choices=[('parent', 'Parent'), ('school_ngo', 'School or NGO')], default='parent', validators=[DataRequired()])
    
    # New field, optional since it only applies to NGOs/Schools
    contact_person = StringField('Contact Person Name', validators=[Optional()])
    
    submit = SubmitField('Create Account')

    def validate_name(self, name):
        # The 'name' field maps to the 'username' column in the database
        user = User.find_by_username(name.data)
        if user:
            raise ValidationError('That name is already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.find_by_email(email.data)
        if user:
            raise ValidationError('That email is already in use. Please choose a different one.')

class LoginForm(FlaskForm):
    """
    Form for users to login.
    """
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RequestResetForm(FlaskForm):
    """
    Form for users to request a password reset email.
    """
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = User.find_by_email(email.data)
        if user is None:
            raise ValidationError('There is no account with that email. You must register first.')

class ResetPasswordForm(FlaskForm):
    """
    Form for users to reset their password.
    """
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')
