# app/models/disputes.py
from datetime import datetime
from app.extensions import db
from mongoengine.fields import ReferenceField, IntField, StringField, DateTimeField, BooleanField

class Dispute(db.Document):
    initiator = ReferenceField('User', required=True)
    respondent = ReferenceField('User', required=True)
    listing = ReferenceField('Listing')
    reason = StringField(required=True)
    status = StringField(max_length=50, default='open')
    resolution = StringField(choices=('pending', 'resolved_in_favor_of_initiator', 'resolved_in_favor_of_respondent', 'mutually_resolved', 'rejected'), default='pending')
    date_raised = DateTimeField(default=datetime.utcnow)
    date_resolved = DateTimeField()
    resolution_notes = StringField()

    def __repr__(self):
        """
        String representation of the Dispute object.
        """
        return f"Dispute(ID: {self.id}, Status: {self.status}, Initiator: {self.initiator.username}, Respondent: {self.respondent.username})"

    def to_dict(self):
        """
        Converts the Dispute object to a dictionary.
        """
        return {
            'id': str(self.id),
            'initiator_id': str(self.initiator.id),
            'initiator_username': self.initiator.username,
            'respondent_id': str(self.respondent.id),
            'respondent_username': self.respondent.username,
            'listing_id': str(self.listing.id) if self.listing else None,
            'listing_title': self.listing.title if self.listing else None,
            'reason': self.reason,
            'status': self.status,
            'date_raised': self.date_raised.isoformat() + 'Z',
            'date_resolved': self.date_resolved.isoformat() + 'Z' if self.date_resolved else None,
            'resolution_notes': self.resolution_notes
        }