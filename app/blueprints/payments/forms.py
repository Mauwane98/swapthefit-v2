# app/blueprints/payments/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError
from datetime import datetime

class ProcessPaymentForm(FlaskForm):
    """
    Form for processing a payment for a listing.
    Now integrates with Paystack by redirecting to their secure payment page.
    """
    # No direct card details collected here for PCI compliance.
    # Paystack handles secure collection on their hosted page.
    
    payment_gateway = SelectField('Payment Method', choices=[
        ('Paystack', 'Paystack (Card, EFT, Mobile Wallet)'),
        ('Platform_Credits', 'Platform Credits (if available)') # Placeholder for future
    ], validators=[DataRequired()])

    delivery_method = SelectField('Delivery Method', choices=[
        ('pickup', 'Pickup'),
        ('courier', 'Courier')
    ], validators=[DataRequired()])

    submit = SubmitField('Proceed to Payment')

class PremiumListingPurchaseForm(FlaskForm):
    """
    Form for a user to purchase premium visibility for one of their listings.
    Now integrates with Paystack by redirecting to their secure payment page.
    """
    listing_id = StringField('Select Listing to Make Premium', validators=[DataRequired()],
                              render_kw={"placeholder": "Enter the ID of your listing"})
    
    premium_package = SelectField('Premium Package', choices=[
        ('7_days_50', '7 Days - R50'),
        ('14_days_90', '14 Days - R90'),
        ('30_days_150', '30 Days - R150')
    ], validators=[DataRequired()])

    payment_gateway = SelectField('Payment Method', choices=[
        ('Paystack', 'Paystack (Card, EFT, Mobile Wallet)'),
        ('Platform_Credits', 'Platform Credits (if available)') # Placeholder for future
    ], validators=[DataRequired()])

    submit = SubmitField('Proceed to Payment')

class TopUpCreditsForm(FlaskForm):
    """
    Form for users to top up their platform credit balance.
    """
    amount = FloatField(
        'Amount to Top Up (ZAR)',
        validators=[DataRequired(), NumberRange(min=10.0, message="Minimum top-up amount is R10.00.")],
        render_kw={"placeholder": "e.g., 50.00, 100.00", "class": "block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm"}
    )
    submit = SubmitField('Top Up Credits', render_kw={"class": "w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"})

