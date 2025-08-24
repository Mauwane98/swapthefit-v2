from datetime import datetime
from app.extensions import db
from mongoengine.fields import ReferenceField, StringField, IntField, DateTimeField, ListField, DictField

class BulkRequest(db.Document):
    """
    Represents a bulk request for items made by a school or NGO.
    """
    requester = ReferenceField('User', required=True)
    item_description = StringField(max_length=500, required=True)
    quantity_needed = IntField(required=True, min_value=1)
    urgency = StringField(max_length=20, choices=('low', 'medium', 'high'), default='medium')
    status = StringField(max_length=50, choices=('pending', 'fulfilled', 'partially_fulfilled', 'cancelled'), default='pending')
    notes = StringField()
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    fulfilled_quantity = IntField(default=0)
    fulfillment_details = ListField(DictField()) # Stores details of donations fulfilling this request

    meta = {
        'collection': 'bulk_requests',
        'indexes': [
            {'fields': ('requester',)},
            {'fields': ('status',)}
        ]
    }

    def clean(self):
        self.updated_at = datetime.utcnow()

    def __repr__(self):
        return f"BulkRequest(ID: {self.id}, Requester: {self.requester.username}, Item: {self.item_description[:30]}, Status: {self.status})"
