from datetime import datetime
from app.extensions import db
from mongoengine.fields import ReferenceField, StringField, IntField, FloatField, DateTimeField, BooleanField, ListField
from mongoengine.errors import DoesNotExist

class Listing(db.Document):
    meta = {'strict': False}
    """
    Listing Model: Represents an item posted for swap, sale, or donation.
    This model captures all relevant details about the item, including its
    condition, size, price, and associated user.
    """
    title = StringField(max_length=100, required=True)
    description = StringField(required=True)
    price = FloatField() # Price for sale, None for swap/donation
    uniform_type = StringField(max_length=50, required=True) # e.g., "school uniform", "sports kit"
    condition = StringField(max_length=50, required=True) # e.g., "New", "Used - Good", "Used - Fair"
    size = StringField(max_length=20, required=True) # e.g., "Small", "Medium", "Large", "Age 8-9"
    gender = StringField(max_length=10) # e.g., "Male", "Female", "Unisex"
    school_name = StringField(max_length=100)
    location = StringField(max_length=100, required=True) # e.g., City, Suburb, or specific pickup point
    image_files = ListField(StringField(max_length=120), default=['default.jpg']) # List of filenames of the item images
    date_posted = db.DateTimeField(required=True, default=datetime.utcnow)
    is_available = db.BooleanField(default=True) # True if available, False if swapped/sold/donated
    listing_type = StringField(max_length=20, required=True) # 'swap', 'sale', 'donation'
    donation_recipient_type = StringField(max_length=20, choices=('ngo', 'school', 'parent', 'any'), default='any')
    is_premium = BooleanField(default=False) # Field for premium listings

    # New fields for more granular filtering
    brand = StringField(max_length=50) # e.g., "Nike", "Adidas", "School Brand"
    color = StringField(max_length=50) # e.g., "Blue", "Red", "White"

    # New field for Premium Listings
    premium_expiry_date = DateTimeField() # Date when premium status expires

    user = ReferenceField('User')

    def __repr__(self):
        """
        String representation of the Listing object.
        """
        return f"Listing('{self.title}', '{self.date_posted}', '{self.listing_type}', '{self.is_available}')"

    def to_dict(self):
        """
        Converts the Listing object to a dictionary, useful for JSON serialization.
        """
        data = {
            'id': str(self.id),
            'title': self.title,
            'description': self.description,
            'price': self.price,
            'uniform_type': self.uniform_type,
            'condition': self.condition,
            'size': self.size,
            'gender': self.gender,
            'school_name': self.school_name,
            'location': self.location,
            'image_files': self.image_files,
            'date_posted': self.date_posted.isoformat() + 'Z',
            'is_available': self.is_available,
            'listing_type': self.listing_type,
            'is_premium': self.is_premium,
            'brand': self.brand,
            'color': self.color,
            'premium_expiry_date': self.premium_expiry_date.isoformat() + 'Z' if self.premium_expiry_date else None,
            'user_id': None,
            'username': None
        }
        try:
            if self.user:
                data['user_id'] = str(self.user.id)
                data['username'] = self.user.username
        except DoesNotExist:
            # If the user does not exist, user_id and username will remain None
            pass
        return data