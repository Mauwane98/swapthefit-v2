# app/models/messages.py
from datetime import datetime
from app.extensions import db
from mongoengine.fields import ReferenceField, StringField, BooleanField, DateTimeField

class Message(db.Document):
    sender = ReferenceField('User', required=True)
    receiver = ReferenceField('User', required=True)
    content = StringField(required=True)
    timestamp = DateTimeField(default=datetime.utcnow)
    read_status = BooleanField(default=False) # True if the receiver has read it
    swap_request = ReferenceField('SwapRequest') # Optional: Link to a SwapRequest
    order = ReferenceField('Order') # Optional: Link to an Order
    donation = ReferenceField('Donation') # Optional: Link to a Donation

    def __repr__(self):
        """
        String representation of the Message object.
        """
        return f'<Message {self.id} from {self.sender.username} to {self.receiver.username} at {self.timestamp}>'

    def to_dict(self):
        """
        Converts the Message object to a dictionary, useful for JSON serialization.
        """
        data = {
            'id': self.id,
            'sender_id': str(self.sender.id),
            'receiver_id': str(self.receiver.id),
            'content': self.content,
            'timestamp': self.timestamp.isoformat() + 'Z', # ISO 8601 format with Z for UTC
            'read_status': self.read_status,
            'sender_username': self.sender.username, # Include sender's username for display
            'receiver_username': self.receiver.username # Include receiver's username for display
        }
        if self.swap_request:
            data['swap_request_id'] = str(self.swap_request.id)
            data['swap_request_title'] = f"Swap: {self.swap_request.requester_listing.title} <-> {self.swap_request.responder_listing.title}"
        if self.order:
            data['order_id'] = str(self.order.id)
            data['order_title'] = f"Order: {self.order.listing.title} (R{self.order.listing.price})"
        if self.donation:
            data['donation_id'] = str(self.donation.id)
            data['donation_title'] = f"Donation: {self.donation.listing.title}"
        return data