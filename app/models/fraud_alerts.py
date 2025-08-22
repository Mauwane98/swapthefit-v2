from datetime import datetime
from app.extensions import db
from mongoengine.fields import ReferenceField, StringField, DateTimeField, IntField

class FraudAlert(db.Document):
    """
    FraudAlert Model: Represents a flagged suspicious activity.
    """
    user = ReferenceField('User', required=False)
    listing = ReferenceField('Listing', required=False)
    order = ReferenceField('Order', required=False)
    alert_type = StringField(max_length=100, required=True) # e.g., 'high_dispute_volume', 'suspicious_listing', 'unusual_payment'
    description = StringField(required=True)
    severity = StringField(max_length=20, default='medium') # e.g., 'low', 'medium', 'high'
    date_raised = DateTimeField(default=datetime.utcnow)
    status = StringField(max_length=50, default='open') # e.g., 'open', 'reviewed', 'dismissed', 'action_taken'

    def __repr__(self):
        return f"FraudAlert(ID: {self.id}, Type: {self.alert_type}, Status: {self.status})"

    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user.id) if self.user else None,
            'listing_id': str(self.listing.id) if self.listing else None,
            'order_id': str(self.order.id) if self.order else None,
            'alert_type': self.alert_type,
            'description': self.description,
            'severity': self.severity,
            'date_raised': self.date_raised.isoformat() + 'Z',
            'status': self.status
        }