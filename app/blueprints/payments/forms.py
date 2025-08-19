# app/blueprints/payments/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError
from datetime import datetime

class ProcessPaymentForm(FlaskForm):
    """
    Form for processing a payment for a listing.
    Includes fields for credit card details (simulated) and payment gateway selection.
    """
    card_number = StringField('Card Number', validators=[DataRequired(), Length(min=16, max=16, message="Card number must be 16 digits.")],
                              render_kw={"placeholder": "e.g., 4111222233334444"})
    expiry_date = StringField('Expiry Date (MM/YY)', validators=[DataRequired(), Length(min=5, max=5, message="Format: MM/YY")],
                              render_kw={"placeholder": "e.g., 12/25"})
    cvv = StringField('CVV', validators=[DataRequired(), Length(min=3, max=4, message="CVV must be 3 or 4 digits.")],
                      render_kw={"placeholder": "e.g., 123"})
    card_holder_name = StringField('Card Holder Name', validators=[DataRequired(), Length(min=3, max=100)])
    
    # Simulate payment gateway selection (in a real app, this might be dynamic or hidden)
    payment_gateway = SelectField('Payment Gateway', choices=[
        ('PayFast', 'PayFast (Simulated)'),
        ('PayPal', 'PayPal (Simulated)'),
        ('Stripe', 'Stripe (Simulated)')
    ], validators=[DataRequired()])

    submit = SubmitField('Pay Now')

    def validate_expiry_date(self, field):
        """Custom validator for expiry date format and future date."""
        try:
            month, year = map(int, field.data.split('/'))
            current_year = datetime.now().year % 100 # Get last two digits of current year
            current_month = datetime.now().month

            if not (1 <= month <= 12):
                raise ValidationError('Invalid month.')
            if year < current_year or (year == current_year and month < current_month):
                raise ValidationError('Card has expired.')
        except ValueError:
            raise ValidationError('Invalid date format. Use MM/YY.')

class PremiumListingPurchaseForm(FlaskForm):
    """
    Form for a user to purchase premium visibility for one of their listings.
    """
    listing_id = IntegerField('Select Listing to Make Premium', validators=[DataRequired(), NumberRange(min=1)],
                              render_kw={"placeholder": "Enter the ID of your listing"})
    
    # Options for premium duration/cost (can be dynamic from config)
    premium_package = SelectField('Premium Package', choices=[
        ('7_days_50', '7 Days - R50'),
        ('14_days_90', '14 Days - R90'),
        ('30_days_150', '30 Days - R150')
    ], validators=[DataRequired()])

    # Re-use payment fields from ProcessPaymentForm
    card_number = StringField('Card Number', validators=[DataRequired(), Length(min=16, max=16, message="Card number must be 16 digits.")],
                              render_kw={"placeholder": "e.g., 4111222233334444"})
    expiry_date = StringField('Expiry Date (MM/YY)', validators=[DataRequired(), Length(min=5, max=5, message="Format: MM/YY")],
                              render_kw={"placeholder": "e.g., 12/25"})
    cvv = StringField('CVV', validators=[DataRequired(), Length(min=3, max=4, message="CVV must be 3 or 4 digits.")],
                      render_kw={"placeholder": "e.g., 123"})
    card_holder_name = StringField('Card Holder Name', validators=[DataRequired(), Length(min=3, max=100)])
    payment_gateway = SelectField('Payment Gateway', choices=[
        ('PayFast', 'PayFast (Simulated)'),
        ('PayPal', 'PayPal (Simulated)'),
        ('Stripe', 'Stripe (Simulated)')
    ], validators=[DataRequired()])

    submit = SubmitField('Purchase Premium')

    def validate_expiry_date(self, field):
        """Custom validator for expiry date format and future date."""
        try:
            month, year = map(int, field.data.split('/'))
            current_year = datetime.now().year % 100 # Get last two digits of current year
            current_month = datetime.now().month

            if not (1 <= month <= 12):
                raise ValidationError('Invalid month.')
            if year < current_year or (year == current_year and month < current_month):
                raise ValidationError('Card has expired.')
        except ValueError:
            raise ValidationError('Invalid date format. Use MM/YY.')

