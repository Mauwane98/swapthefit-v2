from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, SelectField, TextAreaField, HiddenField # Added SelectField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, Length, Optional, Email

# Assuming User and Listing models are available for choices or validation if needed
# from app.models.users import User
# from app.models.listings import Listing

class UserManagementForm(FlaskForm):
    """
    Form for managing user accounts by administrators.
    """
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Role', choices=[('parent', 'Parent'), ('school', 'School'), ('ngo', 'NGO'), ('admin', 'Admin')], validators=[DataRequired()]) # Added role field
    active = BooleanField('Is Active') # Added active field
    is_banned = BooleanField('Is Banned') # Added is_banned field
    ban_reason = TextAreaField('Ban/Suspension Reason', validators=[Optional(), Length(max=500)]) # Added ban_reason field
    submit = SubmitField('Update User')

class ListingModerationForm(FlaskForm):
    """
    Form for moderating listings by administrators.
    """
    # Example fields; customize based on actual listing moderation needs
    # status = SelectField('Status', choices=[('active', 'Active'), ('pending', 'Pending Review'), ('rejected', 'Rejected')])
    # reason = TextAreaField('Reason for Moderation', validators=[Optional(), Length(max=500)])
    # is_featured = BooleanField('Feature Listing')
    submit = SubmitField('Moderate Listing')

class SuspendUserForm(FlaskForm):
    """
    A simple form for suspending a user.
    """
    csrf_token = HiddenField()
    submit = SubmitField('Suspend')

class BanUserForm(FlaskForm):
    """
    A simple form for banning a user.
    """
    csrf_token = HiddenField()
    submit = SubmitField('Ban')

class DeleteUserForm(FlaskForm):
    """
    A simple form for deleting a user.
    """
    csrf_token = HiddenField()
    submit = SubmitField('Delete')

class ToggleListingStatusForm(FlaskForm):
    """
    A simple form for toggling a listing's active status.
    """
    csrf_token = HiddenField()
    submit = SubmitField('Toggle Status')

class DeleteListingForm(FlaskForm):
    """
    A simple form for deleting a listing.
    """
    csrf_token = HiddenField()
    submit = SubmitField('Delete Listing')