# app/models/saved_search.py
from datetime import datetime
from app.extensions import db
from mongoengine.fields import ReferenceField, IntField, StringField, DateTimeField

class SavedSearch(db.Document):
    user = ReferenceField('User', required=True)
    search_query_params = StringField(required=True)
    date_saved = DateTimeField(default=datetime.utcnow)
    name = StringField(max_length=100)

    def __repr__(self):
        """
        String representation of the SavedSearch object.
        """
        return f"SavedSearch('{self.name or 'Unnamed'}', User: {self.user.username}, '{self.search_query_params}')"

    def to_dict(self):
        """
        Converts the SavedSearch object to a dictionary.
        """
        return {
            'id': str(self.id),
            'user_id': str(self.user.id),
            'name': self.name,
            'search_query_params': self.search_query_params,
            'date_saved': self.date_saved.isoformat() + 'Z'
        }