from datetime import datetime
from app.extensions import db
from mongoengine import CASCADE
from mongoengine.fields import ReferenceField

class Referral(db.Document):
    referrer = ReferenceField('User', required=True, reverse_delete_rule=CASCADE)
    referred_user = ReferenceField('User', unique=True, sparse=True, reverse_delete_rule=CASCADE)
    referral_code = db.StringField(required=True, unique=True, max_length=20)
    status = db.StringField(choices=('pending', 'completed', 'cancelled'), default='pending')
    created_at = db.DateTimeField(default=datetime.utcnow)
    completed_at = db.DateTimeField()

    meta = {
        'collection': 'referrals',
        'indexes': [
            'referral_code',
            'referrer',
            'referred_user',
            'status'
        ]
    }

    def to_dict(self):
        data = {
            'id': str(self.id),
            'referrer_id': str(self.referrer.id) if self.referrer else None,
            'referrer_username': self.referrer.username if self.referrer else None,
            'referred_user_id': str(self.referred_user.id) if self.referred_user else None,
            'referred_user_username': self.referred_user.username if self.referred_user else None,
            'referral_code': self.referral_code,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
        return data