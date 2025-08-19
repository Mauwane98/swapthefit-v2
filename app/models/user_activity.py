# app/models/user_activity.py
from datetime import datetime
from app.extensions import db
from mongoengine.fields import ReferenceField, IntField, StringField, DateTimeField, DictField
import json # Import json for handling payload

class UserActivity(db.Document):
    id = IntField(primary_key=True)
    user = ReferenceField('User', required=False)
    action_type = StringField(max_length=100, required=True)
    description = StringField(required=True)
    timestamp = DateTimeField(default=datetime.utcnow)
    ip_address = StringField(max_length=45)
    payload = DictField()

    def __repr__(self):
        """
        String representation of the UserActivity object.
        """
        return f"UserActivity(User: {self.user.username}, Action: {self.action_type}, Time: {self.timestamp})"

    def to_dict(self):
        """
        Converts the UserActivity object to a dictionary, useful for JSON serialization.
        """
        return {
            'id': self.id,
            'user_id': str(self.user.id),
            'username': self.user.username,
            'action_type': self.action_type,
            'description': self.description,
            'timestamp': self.timestamp.isoformat() + 'Z',
            'ip_address': self.ip_address,
            'payload': self.payload
        }