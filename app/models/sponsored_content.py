from datetime import datetime
from app.extensions import db

class SponsoredContent(db.Document):
    title = db.StringField(required=True, max_length=120)
    content = db.StringField(required=True, max_length=500)
    image_url = db.StringField(max_length=200)  # URL to the sponsored image/banner
    target_url = db.StringField(required=True, max_length=200)  # URL to redirect to
    start_date = db.DateTimeField(required=True, default=datetime.utcnow)
    end_date = db.DateTimeField(required=True)
    is_active = db.BooleanField(default=True)
    created_at = db.DateTimeField(default=datetime.utcnow)
    updated_at = db.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'sponsored_content',
        'indexes': [
            'is_active',
            'start_date',
            'end_date'
        ]
    }

    def to_dict(self):
        return {
            'id': str(self.id),
            'title': self.title,
            'content': self.content,
            'image_url': self.image_url,
            'target_url': self.target_url,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
