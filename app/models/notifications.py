# app/models/notifications.py
from datetime import datetime
from app.extensions import db
from mongoengine.fields import ReferenceField, IntField, StringField, BooleanField, DateTimeField, DictField
import json # Import json for handling payload

class Notification(db.Document):
    id = IntField(primary_key=True)
    user = ReferenceField('User', required=True)
    message = StringField(max_length=255, required=True)
    timestamp = DateTimeField(default=datetime.utcnow)
    is_read = BooleanField(default=False)
    notification_type = StringField(max_length=50, required=True, default='general')
    payload = DictField() # Stored as a dictionary directly

    # app/models/notifications.py
from datetime import datetime
from app.extensions import db
from mongoengine.fields import ReferenceField, StringField, BooleanField, DateTimeField, DictField
import json # Import json for handling payload

class Notification(db.Document):
    user = ReferenceField('User', required=True)
    message = StringField(max_length=255, required=True)
    timestamp = DateTimeField(default=datetime.utcnow)
    is_read = BooleanField(default=False)
    notification_type = StringField(max_length=50, required=True, default='general')
    payload = DictField() # Stored as a dictionary directly

    def __repr__(self):
        """
        String representation of the Notification object.
        """
        return f"Notification('{self.user.username}', '{self.message}', '{self.timestamp}', '{self.notification_type}')"

    def to_dict(self):
        """
        Converts the Notification object to a dictionary, useful for JSON serialization.
        """
        return {
            'id': str(self.id), # Use str(self.id) as id will now be ObjectId
            'user_id': str(self.user.id),
            'message': self.message,
            'timestamp': self.timestamp.isoformat() + 'Z',
            'is_read': self.is_read,
            'notification_type': self.notification_type,
            'payload': self.payload
        }

    def to_dict(self):
        """
        Converts the Notification object to a dictionary, useful for JSON serialization.
        """
        return {
            'id': self.id,
            'user_id': str(self.user.id),
            'message': self.message,
            'timestamp': self.timestamp.isoformat() + 'Z',
            'is_read': self.is_read,
            'notification_type': self.notification_type,
            'payload': self.payload
        }