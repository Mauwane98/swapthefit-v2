from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from app.models.users import User

class RegistrationForm(FlaskForm):
    """User registration form."""
    name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', 
                                     validators=[DataRequired(), EqualTo('password')])
    role = SelectField('I am a', choices=[('parent', 'Parent'), ('ngo', 'NGO'), ('school', 'School')])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        """Check if the email is already registered."""
        user = User.find_by_email(email.data)
        if user:
            raise ValidationError('That email is already in use. Please choose a different one.')

class LoginForm(FlaskForm):
    """User login form."""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
