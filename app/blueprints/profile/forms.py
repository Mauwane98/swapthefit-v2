from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from app.models.users import User

class EditProfileForm(FlaskForm):
    """
    Form for users to edit their profile information.
    Includes fields for username, email, and an optional profile picture.
    """
    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=2, max=80)],
        render_kw={"placeholder": "Your unique username"}
    )
    email = StringField(
        'Email',
        validators=[DataRequired(), Email()],
        render_kw={"placeholder": "Your email address"}
    )
    profile_pic = FileField(
        'Update Profile Picture',
        validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only! Allowed formats: JPG, PNG, JPEG.')],
        render_kw={"accept": "image/*"} # Suggests image files
    )
    about_me = TextAreaField(
        'About Me (Optional)',
        validators=[Optional(), Length(max=500)],
        render_kw={"placeholder": "Tell us a little about yourself or your organization."}
    )
    submit = SubmitField('Update Profile')

    def validate_username(self, username):
        """
        Custom validator to ensure the chosen username is unique,
        unless it's the current user's existing username.
        """
        if username.data != current_user.username:
            user = User.objects(username=username.data).first()
            if user:
                raise ValidationError('That username is already taken. Please choose a different one.')

    def validate_email(self, email):
        """
        Custom validator to ensure the chosen email is unique,
        unless it's the current user's existing email.
        """
        if email.data != current_user.email:
            user = User.objects(email=email.data).first()
            if user:
                raise ValidationError('That email is already in use. Please choose a different one.')
