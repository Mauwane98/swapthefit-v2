from flask_wtf import FlaskForm
from wtforms import SelectField, TextAreaField, SubmitField, IntegerField, FloatField
from wtforms.validators import DataRequired, Length, ValidationError, Optional, NumberRange
from app.models.users import User
from app.models.listings import Listing # Assuming Listing model is accessible
from flask_login import current_user

class ProposeDonationForm(FlaskForm):
    """
    Form for proposing a donation for a specific listing to a school or NGO.
    Includes fields for quantity and estimated value.
    """
    # This field will be dynamically populated in the route with available schools/NGOs.
    recipient_id = SelectField(
        'Choose Recipient School or NGO',
        validators=[DataRequired(message="Please select a recipient for your donation.")],
        choices=[], # Choices will be populated dynamically in the route
        render_kw={"class": "block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm"}
    )
    
    quantity = IntegerField(
        'Quantity of Items',
        validators=[DataRequired(), NumberRange(min=1, message="Quantity must be at least 1.")],
        default=1,
        render_kw={"placeholder": "e.g., 1 (for one uniform set), 3 (for three shirts)", "class": "block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm"}
    )

    estimated_value = FloatField(
        'Estimated Value (ZAR)',
        validators=[DataRequired(), NumberRange(min=0.0, message="Value cannot be negative.")],
        default=0.0,
        render_kw={"placeholder": "e.g., 150.00 (estimated value of the donation)", "class": "block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm"}
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
        # Assuming User.objects is for MongoEngine, for SQLAlchemy it would be User.query.filter()
        recipients = User.query.filter(User.role.in_(['school', 'ngo'])).all() # For SQLAlchemy
        self.recipient_id.choices = [
            (str(user.id), user.username) 
            for user in recipients
        ]
        self.recipient_id.choices.insert(0, ('', 'Select a recipient'))

class ConfirmDonationReceiptForm(FlaskForm):
    """
    Form for schools/NGOs to confirm receipt of a donated item.
    Allows for confirmation/adjustment of quantity and value.
    """
    quantity_received = IntegerField(
        'Quantity Received',
        validators=[DataRequired(), NumberRange(min=1, message="Quantity must be at least 1.")],
        render_kw={"placeholder": "Confirm quantity received", "class": "block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm"}
    )
    estimated_value_received = FloatField(
        'Estimated Value Received (ZAR)',
        validators=[DataRequired(), NumberRange(min=0.0, message="Value cannot be negative.")],
        render_kw={"placeholder": "Confirm estimated value received", "class": "block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm"}
    )
    notes = TextAreaField(
        'Notes (Optional)',
        validators=[Optional(), Length(max=500)],
        render_kw={"placeholder": "Add any notes about the condition or specifics of the received item.", "rows": 4, "class": "block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm"}
    )
    submit = SubmitField('Confirm Receipt', render_kw={"class": "w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"})

class MarkDonationDistributedForm(FlaskForm):
    """
    Form for schools/NGOs to mark a donated item as distributed.
    Includes field for families supported.
    """
    families_supported = IntegerField(
        'Number of Families/Individuals Supported',
        validators=[DataRequired(), NumberRange(min=0, message="Number of families supported cannot be negative.")],
        default=0,
        render_kw={"placeholder": "e.g., 1, 2, 5", "class": "block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm"}
    )
    distribution_notes = TextAreaField(
        'Distribution Notes (Optional)',
        validators=[Optional(), Length(max=500)],
        render_kw={"placeholder": "Add details about when and to whom the item was distributed.", "rows": 4, "class": "block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm"}
    )
    submit = SubmitField('Mark as Distributed', render_kw={"class": "w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"})

