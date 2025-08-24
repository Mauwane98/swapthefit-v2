from app.extensions import db
from datetime import datetime
from mongoengine.fields import ReferenceField, DateTimeField

class Follow(db.Document):
    follower = ReferenceField('User', required=True, help_text="The user who is following")
    followed = ReferenceField('User', required=True, help_text="The user being followed")
    timestamp = DateTimeField(default=datetime.utcnow)

    meta = {
        'indexes': [
            {'fields': ('follower', 'followed'), 'unique': True}, # A user can only follow another user once
            'follower',
            'followed'
        ]
    }

    def __repr__(self):
        return f"<Follow {self.follower.username} follows {self.followed.username}>"
