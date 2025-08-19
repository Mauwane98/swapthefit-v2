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

    def __repr__(self):
        """
        String representation of the Message object.
        """
        return f'<Message {self.id} from {self.sender.username} to {self.receiver.username} at {self.timestamp}>'

    def to_dict(self):
        """
        Converts the Message object to a dictionary, useful for JSON serialization.
        """
        return {
            'id': self.id,
            'sender_id': str(self.sender.id),
            'receiver_id': str(self.receiver.id),
            'content': self.content,
            'timestamp': self.timestamp.isoformat() + 'Z', # ISO 8601 format with Z for UTC
            'read_status': self.read_status,
            'sender_username': self.sender.username, # Include sender's username for display
            'receiver_username': self.receiver.username # Include receiver's username for display
        }