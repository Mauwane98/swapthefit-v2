# app/models/reviews.py
from datetime import datetime
from app.extensions import db
from mongoengine.fields import ReferenceField, IntField, StringField, BooleanField, DateTimeField

class Review(db.Document):
    reviewer = ReferenceField('User', required=True)
    reviewed_user = ReferenceField('User', required=True)
    comment = StringField(required=True)
    rating = IntField(required=True)
    is_positive = BooleanField(required=True)
    communication_rating = IntField(required=True)
    logistics_rating = IntField(required=True)
    item_as_described = BooleanField(default=True)
    date_posted = DateTimeField(default=datetime.utcnow)
    transaction_id = StringField(required=True)
    listing = ReferenceField('Listing')

    def __repr__(self):
        """
        String representation of the Review object.
        """
        return f"Review(ID: {self.id}, Reviewer: {self.reviewer.username}, Reviewed: {self.reviewed_user.username}, Rating: {self.rating})"

    def to_dict(self):
        """
        Converts the Review object to a dictionary.
        """
        return {
            'id': str(self.id),
            'reviewer_id': str(self.reviewer.id),
            'reviewer_username': self.reviewer.username,
            'reviewed_user_id': str(self.reviewed_user.id),
            'reviewed_user_username': self.reviewed_user.username,
            'comment': self.comment,
            'rating': self.rating,
            'is_positive': self.is_positive,
            'communication_rating': self.communication_rating,
            'logistics_rating': self.logistics_rating,
            'item_as_described': self.item_as_described,
            'transaction_id': self.transaction_id,
            'date_posted': self.date_posted.isoformat() + 'Z',
            'listing_id': str(self.listing.id) if self.listing else None,
            'listing_title': self.listing.title if self.listing else None
        }