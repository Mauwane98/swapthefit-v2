# app/blueprints/logistics/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, DateTimeLocalField
from wtforms.validators import DataRequired, Length, Optional, URL, ValidationError
from datetime import datetime

class SetupLogisticsForm(FlaskForm):
    """
    Form for setting up initial logistics details for a transaction.
    This form will be used by the sender (seller/swap initiator).
    """
    shipping_method = SelectField('Shipping Method', choices=[
        ('pickup_dropoff', 'PUDO Locker Pickup/Dropoff'),
        ('courier', 'Courier Delivery'),
        ('in_person', 'In-Person Exchange')
    ], validators=[DataRequired()])

    # Fields for Courier Delivery
    courier_name = StringField('Courier Name (Optional)', validators=[Optional(), Length(max=100)],
                               render_kw={"placeholder": "e.g., DHL, FedEx"})
    tracking_number = StringField('Tracking Number (Optional)', validators=[Optional(), Length(max=100)],
                                  render_kw={"placeholder": "e.g., TRK123456789"})
    tracking_url = StringField('Tracking URL (Optional)', validators=[Optional(), URL(), Length(max=255)],
                               render_kw={"placeholder": "e.g., https://track.example.com/TRK123"})

    # Fields for PUDO Locker
    pudo_location_name = StringField('PUDO Location Name (Optional)', validators=[Optional(), Length(max=255)],
                                     render_kw={"placeholder": "e.g., LockerXYZ at Mall ABC"})
    pudo_address = StringField('PUDO Address (Optional)', validators=[Optional(), Length(max=255)],
                               render_kw={"placeholder": "e.g., 123 Main St, City"})
    pudo_code = StringField('PUDO Collection Code (Optional)', validators=[Optional(), Length(max=50)],
                            render_kw={"placeholder": "e.g., ABC123DEF"})

    # Fields for In-Person / Courier Addresses
    pickup_address = StringField('Pickup Address (Optional)', validators=[Optional(), Length(max=255)],
                                 render_kw={"placeholder": "e.g., Your address for pickup"})
    delivery_address = StringField('Delivery Address (Optional)', validators=[Optional(), Length(max=255)],
                                  render_kw={"placeholder": "e.g., Recipient's delivery address"})

    # Scheduled dates (optional, can be set by sender or courier)
    scheduled_pickup_date = DateTimeLocalField('Scheduled Pickup Date/Time (Optional)', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    scheduled_delivery_date = DateTimeLocalField('Scheduled Delivery Date/Time (Optional)', format='%Y-%m-%dT%H:%M', validators=[Optional()])

    notes = TextAreaField('Additional Notes (Optional)', validators=[Optional(), Length(max=500)],
                          render_kw={"rows": 3, "placeholder": "Any specific instructions or details."})

    submit = SubmitField('Setup Logistics')

    def validate_shipping_method(self, field):
        """Custom validation to ensure required fields for selected method are present."""
        if field.data == 'courier':
            if not self.courier_name.data and not self.tracking_number.data:
                raise ValidationError('Courier Name or Tracking Number is recommended for Courier method.')
            if not self.delivery_address.data:
                raise ValidationError('Delivery Address is required for Courier method.')
        elif field.data == 'pickup_dropoff':
            if not self.pudo_location_name.data and not self.pudo_address.data:
                raise ValidationError('PUDO Location Name or Address is required for PUDO method.')
        elif field.data == 'in_person':
            if not self.pickup_address.data and not self.delivery_address.data:
                raise ValidationError('Pickup or Delivery Address is recommended for In-Person method.')


class UpdateLogisticsStatusForm(FlaskForm):
    """
    Form for updating the status of an existing logistics record.
    Can be used by sender, receiver, or admin.
    """
    status = SelectField('Logistics Status', choices=[
        ('pending_pickup', 'Pending Pickup'),
        ('in_transit', 'In Transit'),
        ('ready_for_collection', 'Ready for Collection'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed')
    ], validators=[DataRequired()])
    
    # Actual dates (optional, updated as events occur)
    actual_pickup_date = DateTimeLocalField('Actual Pickup Date/Time (Optional)', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    actual_delivery_date = DateTimeLocalField('Actual Delivery Date/Time (Optional)', format='%Y-%m-%dT%H:%M', validators=[Optional()])

    notes = TextAreaField('Status Update Notes (Optional)', validators=[Optional(), Length(max=500)],
                          render_kw={"rows": 3, "placeholder": "Add any notes related to this status update."})

    submit = SubmitField('Update Logistics Status')

