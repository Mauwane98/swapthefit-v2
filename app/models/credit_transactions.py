# app/models/credit_transactions.py
from datetime import datetime
from app.extensions import db
from mongoengine.fields import ReferenceField

class CreditTransaction(db.Document):
    """
    CreditTransaction Model: Records all credit earning and spending activities.
    """
    user = ReferenceField('User', required=True, reverse_delete_rule=db.CASCADE)
    amount = db.FloatField(required=True) # Positive for earned, negative for spent
    transaction_type = db.StringField(max_length=20, choices=('earn', 'spend'), required=True)
    source_type = db.StringField(max_length=50, required=True) # e.g., 'donation', 'swap', 'listing_purchase'
    source_id = db.StringField(max_length=100, required=False) # ID of the related object (Listing, Swap, etc.)
    timestamp = db.DateTimeField(required=True, default=datetime.utcnow)

    meta = {
        'indexes': [
            {'fields': ('user', 'timestamp'), 'unique': False},
            {'fields': ('source_type', 'source_id'), 'unique': False}
        ]
    }

    def __repr__(self):
        return f"CreditTransaction(User: {self.user.username}, Amount: {self.amount}, Type: {self.transaction_type}, Source: {self.source_type}-{self.source_id})"
