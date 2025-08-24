# app/models/logistics.py
from datetime import datetime
from app.extensions import db
from app.models.users import User # Import User model
from mongoengine.fields import ReferenceField # Add this import

class Logistics(db.Document):
    """
    Logistics Model: Represents the shipping and delivery details for a transaction.
    This model tracks the movement of items, especially for sales and swaps,
    and integrates with potential PUDO/courier services.
    """
    # MongoEngine automatically creates an _id field as primary key
    # If you need a custom ID, you can define it, e.g., logistics_id = db.StringField(primary_key=True)

    transaction_id = db.StringField(required=True) # Link to the transaction (Order ID for sales, SwapRequest ID for swaps)
    transaction_type = db.StringField(max_length=20, required=True) # 'sale', 'swap'

    # Parties involved (for easy lookup)
    sender = ReferenceField(User, required=True)
    receiver = ReferenceField(User, required=True)

    # Shipping method: 'pickup_dropoff' (PUDO), 'courier', 'in_person'
    shipping_method = db.StringField(max_length=50, required=True)

    # Status of the logistics: 'pending_pickup', 'in_transit', 'ready_for_collection', 'delivered', 'cancelled', 'failed'
    status = db.StringField(max_length=50, required=True, default='pending_pickup')

    # Courier details (if applicable)
    courier_name = db.StringField(max_length=100)
    tracking_number = db.StringField(max_length=100, unique=True)
    tracking_url = db.StringField(max_length=255) # URL to courier's tracking page

    # PUDO locker details (if applicable)
    pudo_location_name = db.StringField(max_length=255)
    pudo_address = db.StringField(max_length=255)
    pudo_code = db.StringField(max_length=50) # Code for collection from locker

    # Pickup/Delivery addresses (for courier or in-person)
    pickup_address = db.StringField(max_length=255)
    delivery_address = db.StringField(max_length=255)

    # Timestamps
    created_at = db.DateTimeField(required=True, default=datetime.utcnow)
    scheduled_pickup_date = db.DateTimeField()
    actual_pickup_date = db.DateTimeField()
    scheduled_delivery_date = db.DateTimeField()
    actual_delivery_date = db.DateTimeField()
    last_status_update = db.DateTimeField(required=True, default=datetime.utcnow)

    # Optional notes from sender/receiver/courier
    notes = db.StringField() # Text field

    meta = {'collection': 'logistics'} # Optional: specify collection name

    def __repr__(self):
        """
        String representation of the Logistics object.
        """
        return f"Logistics(ID: {self.id}, Transaction: {self.transaction_type}-{self.transaction_id}, Status: {self.status})"

    def to_dict(self):
        """
        Converts the Logistics object to a dictionary.
        """
        return {
            'id': str(self.id), # Convert ObjectId to string
            'transaction_id': self.transaction_id,
            'transaction_type': self.transaction_type,
            'sender_user_id': str(self.sender.id) if self.sender else None,
            'sender_username': self.sender.username if self.sender else None,
            'receiver_user_id': str(self.receiver.id) if self.receiver else None,
            'receiver_username': self.receiver.username if self.receiver else None,
            'shipping_method': self.shipping_method,
            'status': self.status,
            'courier_name': self.courier_name,
            'tracking_number': self.tracking_number,
            'tracking_url': self.tracking_url,
            'pudo_location_name': self.pudo_location_name,
            'pudo_address': self.pudo_address,
            'pudo_code': self.pudo_code,
            'pickup_address': self.pickup_address,
            'delivery_address': self.delivery_address,
            'created_at': self.created_at.isoformat() + 'Z',
            'scheduled_pickup_date': self.scheduled_pickup_date.isoformat() + 'Z' if self.scheduled_pickup_date else None,
            'actual_pickup_date': self.actual_pickup_date.isoformat() + 'Z' if self.actual_pickup_date else None,
            'scheduled_delivery_date': self.scheduled_delivery_date.isoformat() + 'Z' if self.scheduled_delivery_date else None,
            'actual_delivery_date': self.actual_delivery_date.isoformat() + 'Z' if self.actual_delivery_date else None,
            'last_status_update': self.last_status_update.isoformat() + 'Z',
            'notes': self.notes
        }
