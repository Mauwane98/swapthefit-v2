# app/models/wishlist.py
from datetime import datetime
from app.extensions import db
from mongoengine.fields import ReferenceField, IntField, DateTimeField

class WishlistItem(db.Document):
    user = ReferenceField('User', required=True)
    listing = ReferenceField('Listing', required=True)
    date_added = DateTimeField(default=datetime.utcnow)

    def __repr__(self):
        """
        String representation of the WishlistItem object.
        """
        return f"WishlistItem(User: {self.user.username}, Listing: {self.listing.title})"

    def to_dict(self):
        """
        Converts the WishlistItem object to a dictionary.
        """
        return {
            'id': str(self.id),
            'user_id': str(self.user.id),
            'listing_id': str(self.listing.id),
            'date_added': self.date_added.isoformat() + 'Z',
            'listing_title': self.listing.title,
            'listing_price': self.listing.price,
            'listing_condition': self.listing.condition,
            'listing_image': self.listing.image_file,
            'listing_is_available': self.listing.is_available,
            'listing_url': f'/listings/{self.listing.id}' # Example URL
        }