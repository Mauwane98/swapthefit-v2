from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, ValidationError

class SetLogisticsDetailsForm(FlaskForm):
    """
    Form for sellers/donors to set up logistics details for an item.
    """
    delivery_method = SelectField(
        'Delivery Method',
        choices=[
            ('', 'Select Delivery Method'),
            ('pickup', 'Local Pickup (Arrange directly)'),
            ('pudo_locker', 'PUDO Locker'),
            ('courier_delivery', 'Courier Delivery')
        ],
        validators=[DataRequired(message="Please select a delivery method.")],
        render_kw={"class": "block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"}
    )
    
    pickup_location_details = TextAreaField(
        'Pickup Location Details (if Local Pickup)',
        validators=[Optional(), Length(max=255)],
        render_kw={"placeholder": "e.g., Your address for pickup, or specific instructions.", "rows": 3, "class": "block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"}
    )
    
    delivery_address_details = TextAreaField(
        'Delivery Address (if Courier Delivery)',
        validators=[Optional(), Length(max=255)],
        render_kw={"placeholder": "e.g., Recipient's full address for courier delivery.", "rows": 3, "class": "block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"}
    )

    pudo_locker_id = StringField(
        'PUDO Locker ID (if PUDO Locker)',
        validators=[Optional(), Length(max=50)],
        render_kw={"placeholder": "Enter the PUDO Locker ID (e.g., PUDO-XYZ)", "class": "block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"}
    )

    logistics_provider = StringField(
        'Logistics Provider (e.g., PUDO, DHL, Aramex)',
        validators=[Optional(), Length(max=50)],
        render_kw={"placeholder": "e.g., PUDO, DHL, Aramex", "class": "block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"}
    )

    submit = SubmitField('Save Logistics Details', render_kw={"class": "w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"})

    def validate(self):
        """
        Custom validation to ensure correct fields are filled based on delivery method.
        """
        if not super().validate():
            return False
        
        if self.delivery_method.data == 'pickup':
            if not self.pickup_location_details.data:
                self.pickup_location_details.errors.append("Pickup location details are required for local pickup.")
                return False
        elif self.delivery_method.data == 'pudo_locker':
            if not self.pudo_locker_id.data:
                self.pudo_locker_id.errors.append("PUDO Locker ID is required for PUDO delivery.")
                return False
            if not self.logistics_provider.data:
                self.logistics_provider.errors.append("Logistics provider (e.g., PUDO) is required.")
                return False
        elif self.delivery_method.data == 'courier_delivery':
            if not self.delivery_address_details.data:
                self.delivery_address_details.errors.append("Delivery address is required for courier delivery.")
                return False
            if not self.logistics_provider.data:
                self.logistics_provider.errors.append("Logistics provider (e.g., DHL) is required.")
                return False
        
        return True


class UpdateLogisticsStatusForm(FlaskForm):
    """
    Form for updating the logistics status and adding a tracking number.
    """
    tracking_number = StringField(
        'Tracking Number (Optional)',
        validators=[Optional(), Length(max=100)],
        render_kw={"placeholder": "Enter tracking number if applicable.", "class": "block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"}
    )
    
    submit_shipped = SubmitField('Mark as Shipped/Ready for Pickup', render_kw={"class": "w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"})
    submit_received = SubmitField('Confirm Received', render_kw={"class": "w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"})
    submit_cancel_logistics = SubmitField('Cancel Logistics', render_kw={"class": "w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"})

