# app/models/reports.py
from datetime import datetime
from app.extensions import db
from app.models.users import User # Import User model
from mongoengine.fields import ReferenceField # Add this import

class Report(db.Document):
    # MongoEngine automatically creates an _id field as primary key
    # If you need a custom ID, you can define it, e.g., report_id = db.StringField(primary_key=True)
    # For simplicity, we'll let MongoEngine manage the primary key (_id)

    reporter = ReferenceField(User, required=True) # Reference to the User who submitted the report

    reported_entity_type = db.StringField(max_length=20, required=True)
    reported_entity_id = db.StringField(required=True) # Storing as StringField as it could be ObjectId or other ID
    reason_category = db.StringField(max_length=100, required=True)
    description = db.StringField(required=True) # Text field
    status = db.StringField(max_length=50, required=True, default='pending')
    date_reported = db.DateTimeField(required=True, default=datetime.utcnow)
    date_resolved = db.DateTimeField() # Nullable by default
    admin_notes = db.StringField() # Nullable by default

    meta = {'collection': 'reports'} # Optional: specify collection name

    def __repr__(self):
        return f"Report(ID: {self.id}, Type: {self.reported_entity_type}, Entity ID: {self.reported_entity_id}, Status: {self.status})"

    def to_dict(self):
        return {
            'id': str(self.id), # Convert ObjectId to string
            'reporter_id': str(self.reporter.id) if self.reporter else None,
            'reporter_username': self.reporter.username if self.reporter else None,
            'reported_entity_type': self.reported_entity_type,
            'reported_entity_id': self.reported_entity_id,
            'reason_category': self.reason_category,
            'description': self.description,
            'status': self.status,
            'date_reported': self.date_reported.isoformat() + 'Z',
            'date_resolved': self.date_resolved.isoformat() + 'Z' if self.date_resolved else None,
            'admin_notes': self.admin_notes
        }
