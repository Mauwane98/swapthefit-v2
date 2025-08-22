# app/models/payments.py
from datetime import datetime
from app.extensions import db
from mongoengine.fields import ReferenceField, IntField, FloatField, StringField, DateTimeField, BooleanField

class Order(db.Document):
    buyer = ReferenceField('User', required=True)
    seller = ReferenceField('User', required=True)
    listing = ReferenceField('Listing', required=True)
    price_at_purchase = FloatField(required=True)
    status = StringField(max_length=50, default='pending')
    order_type = StringField(max_length=50, choices=('sale_listing', 'premium_purchase', 'credit_top_up'), default='sale_listing')
    
    # New fields for delivery tracking
    delivery_status = StringField(max_length=50, choices=('pending', 'shipped', 'delivered', 'cancelled'), default='pending')
    delivery_method = StringField(max_length=50)
    tracking_number = StringField(max_length=100)
    delivery_date = DateTimeField()

    order_date = DateTimeField(default=datetime.utcnow)
    transaction_id_gateway = StringField(max_length=100, unique=True)
    payment_gateway = StringField(max_length=50)
    amount_paid_total = FloatField(required=True)
    platform_fee = FloatField(default=0.0)
    seller_payout_amount = FloatField(default=0.0)
    payout_status = StringField(max_length=50, default='pending')
    payout_date = DateTimeField()
    is_premium_listing_purchase = BooleanField(default=False)
    premium_listing_ref = ReferenceField('Listing')

    def __repr__(self):
        """
        String representation of the Order object.
        """
        return f"Order(ID: {self.id}, Listing: {self.listing.title}, Buyer: {self.buyer.username}, Status: {self.status})"

    def to_dict(self):
        """
        Converts the Order object to a dictionary.
        """
        return {
            'id': str(self.id),
            'buyer_id': str(self.buyer.id),
            'buyer_username': self.buyer.username,
            'seller_id': str(self.seller.id),
            'seller_username': self.seller.username,
            'listing_id': str(self.listing.id),
            'listing_title': self.listing.title,
            'price_at_purchase': self.price_at_purchase,
            'status': self.status,
            'order_type': self.order_type,
            'delivery_status': self.delivery_status,
            'delivery_method': self.delivery_method,
            'tracking_number': self.tracking_number,
            'delivery_date': self.delivery_date.isoformat() + 'Z' if self.delivery_date else None,
            'order_date': self.order_date.isoformat() + 'Z',
            'transaction_id_gateway': self.transaction_id_gateway,
            'payment_gateway': self.payment_gateway,
            'amount_paid_total': self.amount_paid_total,
            'platform_fee': self.platform_fee,
            'seller_payout_amount': self.seller_payout_amount,
            'payout_status': self.payout_status,
            'payout_date': self.payout_date.isoformat() + 'Z' if self.payout_date else None,
            'is_premium_listing_purchase': self.is_premium_listing_purchase,
            'premium_listing_id': str(self.premium_listing_ref.id) if self.premium_listing_ref else None,
            'premium_listing_title': self.premium_listing_ref.title if self.premium_listing_ref else None
        }