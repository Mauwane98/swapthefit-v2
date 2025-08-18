from app.extensions import db
from datetime import datetime

class Order(db.Document):
    """
    Represents an order/purchase transaction in the system.
    This model tracks items bought, the buyer, the seller, price, and payment status.
    """
    # Reference to the user who made the purchase.
    buyer = db.ReferenceField(document_type='User', required=True, help_text="The user who bought the item.")

    # Reference to the listing that was purchased.
    purchased_listing = db.ReferenceField(document_type='Listing', required=True, help_text="The listing that was purchased.")

    # Reference to the seller of the item (owner of the listing).
    seller = db.ReferenceField(document_type='User', required=True, help_text="The user who sold the item.")

    # The price at which the item was sold. Copied from listing to ensure historical accuracy.
    price_at_purchase = db.FloatField(required=True, min_value=0.01, help_text="The price of the item at the time of purchase.")

    # Status of the order (e.g., 'pending_payment', 'paid', 'pending_pickup', 'completed', 'cancelled').
    # 'pending_payment': Order initiated, awaiting payment confirmation.
    # 'paid': Payment confirmed, awaiting logistics.
    # 'pending_pickup': Payment received, item awaiting pickup/delivery.
    # 'completed': Item successfully delivered/received by buyer.
    # 'cancelled': Order cancelled before completion.
    status = db.StringField(
        required=True,
        default='pending_payment',
        choices=('pending_payment', 'paid', 'pending_pickup', 'completed', 'cancelled'),
        help_text="Current status of the order."
    )

    # Transaction ID from the payment gateway (e.g., PayFast, PayPal).
    transaction_id = db.StringField(max_length=255, help_text="Transaction ID from the payment gateway.", null=True)

    # Timestamp for when the order was created.
    order_date = db.DateTimeField(default=datetime.utcnow, help_text="Date when the order was initiated.")

    # Timestamp for when the order status was last updated.
    updated_date = db.DateTimeField(default=datetime.utcnow, help_text="Date when the order was last updated.")

    # Define a Meta class for MongoEngine specific configurations.
    meta = {
        'collection': 'orders', # Explicitly set the collection name
        'indexes': [
            {'fields': ('buyer',)},
            {'fields': ('seller',)},
            {'fields': ('purchased_listing',)},
            {'fields': ('status',)},
            {'fields': ('transaction_id',)},
            {'fields': ('-order_date',)}
        ],
        'strict': False # Allows for dynamic fields not explicitly defined in the schema
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
        return f"Order(Listing: {self.purchased_listing.title}, Buyer: {self.buyer.username}, Seller: {self.seller.username}, Status: {self.status}, Price: R{self.price_at_purchase})"

