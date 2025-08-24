from datetime import datetime
from app.extensions import db
from mongoengine.fields import StringField, DateTimeField, BooleanField, DictField, ListField, ReferenceField

class Badge(db.Document):
    """
    Represents a badge that users can earn through various activities.
    """
    name = StringField(max_length=100, required=True, unique=True)
    description = StringField(required=True)
    image_url = StringField(max_length=200, required=True) # URL or path to the badge image
    criteria = DictField(required=True) # Defines the conditions for earning the badge
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'badges',
        'indexes': [
            {'fields': ('name',)}
        ]
    }

    def __repr__(self):
        return f"Badge(Name: {self.name}, Active: {self.is_active})"

class UserBadge(db.Document):
    """
    Represents a badge earned by a user.
    """
    user = ReferenceField('User', required=True)
    badge = ReferenceField('Badge', required=True)
    earned_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'user_badges',
        'indexes': [
            {'fields': ('user', 'badge'), 'unique': True}
        ]
    }

    def __repr__(self):
        return f"UserBadge(User: {self.user.username}, Badge: {self.badge.name}, Earned: {self.earned_at})"
