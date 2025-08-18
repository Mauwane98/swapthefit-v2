from flask_wtf import FlaskForm
from wtforms import SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError, Optional
from app.models.users import User
from app.models.listings import Listing # Assuming Listing model is accessible
from flask_login import current_user

class ProposeDonationForm(FlaskForm):
    """
    Form for proposing a donation for a specific listing to a school or NGO.
    The user selects the recipient school/NGO.
    """
    # This field will be dynamically populated in the route with available schools/NGOs.
    recipient_id = SelectField(
        'Choose Recipient School or NGO',
        validators=[DataRequired(message="Please select a recipient for your donation.")],
        choices=[], # Choices will be populated dynamically in the route
        render_kw={"class": "block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm"}
    )
    
    message = TextAreaField(
        'Message to Recipient (Optional)',
        validators=[Length(max=500)],
        render_kw={"placeholder": "Add any special instructions or notes about the donation.", "rows": 4, "class": "block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm"}
    )
    
    submit = SubmitField('Propose Donation', render_kw={"class": "w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"})

    def __init__(self, *args, **kwargs):
        super(ProposeDonationForm, self).__init__(*args, **kwargs)
        # Populate choices with active 'school' and 'ngo' users
        recipients = User.objects(roles__in=['school', 'ngo'], active=True)
        self.recipient_id.choices = [
            (str(user.id), user.username) # Use username as display, ID as value
            for user in recipients
        ]
        self.recipient_id.choices.insert(0, ('', 'Select a recipient'))

class ConfirmDonationReceiptForm(FlaskForm):
    """
    Form for schools/NGOs to confirm receipt of a donated item.
    """
    notes = TextAreaField(
        'Notes (Optional)',
        validators=[Optional(), Length(max=500)],
        render_kw={"placeholder": "Add any notes about the condition or specifics of the received item.", "rows": 4, "class": "block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm"}
    )
    submit = SubmitField('Confirm Receipt', render_kw={"class": "w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"})

class MarkDonationDistributedForm(FlaskForm):
    """
    Form for schools/NGOs to mark a donated item as distributed.
    """
    distribution_notes = TextAreaField(
        'Distribution Notes (Optional)',
        validators=[Optional(), Length(max=500)],
        render_kw={"placeholder": "Add details about when and to whom the item was distributed.", "rows": 4, "class": "block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm"}
    )
    submit = SubmitField('Mark as Distributed', render_kw={"class": "w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"})

