from app.extensions import db
from datetime import datetime
from mongoengine import ReferenceField

class Order(db.Document):
    """
    Represents an order placed by a user.
    """
    buyer = ReferenceField('User', required=True, help_text="The user who placed the order.")
    seller = ReferenceField('User', required=True, help_text="The user selling the item(s).")
    listing = ReferenceField('Listing', required=True, help_text="The listing associated with this order.")
    quantity = db.IntField(required=True, min_value=1, help_text="Quantity of the item ordered.")
    total_amount = db.FloatField(required=True, min_value=0.0, help_text="Total amount of the order.")
    status = db.StringField(
        required=True,
        default='pending',
        choices=('pending', 'completed', 'cancelled', 'shipped', 'delivered'),
        help_text="Current status of the order."
    )
    delivery_method = db.StringField(
        required=True,
        choices=('pickup', 'courier'),
        help_text="Method chosen for delivery."
    )
    payout_status = db.StringField(
        required=True,
        default='pending',
        choices=('pending', 'paid', 'failed'),
        help_text="Status of the payout to the seller."
    )
    payout_transaction_id = db.StringField(max_length=100, required=False, help_text="Paystack transfer ID for the payout.")
    order_date = db.DateTimeField(default=datetime.utcnow, help_text="Date when the order was placed.")
    updated_date = db.DateTimeField(default=datetime.utcnow, help_text="Date when the order was last updated.")

    meta = {
        'collection': 'orders',
        'indexes': [
            {'fields': ('buyer',)},
            {'fields': ('seller',)},
            {'fields': ('listing',)},
            {'fields': ('status',)},
            {'fields': ('-order_date',)}
        ]
    }

    def clean(self):
        """
        Custom validation or data cleaning hook.
        Ensures updated_date is current before saving.
        """
        self.updated_date = datetime.utcnow()

    def __repr__(self):
        """
        String representation of the Order object.
        """
        return f"Order(ID: {self.id}, Buyer: {self.buyer.username}, Status: {self.status})"

    def to_dict(self):
        """
        Converts the Order object to a dictionary.
        """
        return {
            'id': str(self.id),
            'buyer_id': str(self.buyer.id) if self.buyer else None,
            'buyer_username': self.buyer.username if self.buyer else None,
            'seller_id': str(self.seller.id) if self.seller else None,
            'seller_username': self.seller.username if self.seller else None,
            'listing_id': str(self.listing.id) if self.listing else None,
            'listing_title': self.listing.title if self.listing else None,
            'quantity': self.quantity,
            'total_amount': self.total_amount,
            'status': self.status,
            'order_date': self.order_date.isoformat() + 'Z',
            'updated_date': self.updated_date.isoformat() + 'Z'
        }
