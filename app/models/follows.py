from datetime import datetime
from app.extensions import db # Keep db import for db.Document
from mongoengine import Document, ReferenceField, DateTimeField, CASCADE # Import directly from mongoengine

class Follow(Document): # Use Document directly
    follower = ReferenceField('User', required=True, reverse_delete_rule=CASCADE) # Use CASCADE directly
    followed = ReferenceField('User', required=True, reverse_delete_rule=CASCADE) # Use CASCADE directly
    timestamp = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'follows',
        'indexes': [
            {'fields': ('follower', 'followed'), 'unique': True} # Ensure a user can only follow another user once
        ]
    }

    def __repr__(self):
        return f"Follow(follower={self.follower.username}, followed={self.followed.username})"