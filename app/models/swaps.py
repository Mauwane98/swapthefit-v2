from app.extensions import db
from datetime import datetime

class SwapRequest(db.Document):
    """
    Represents a swap request between two users for their listings.
    This model tracks the items involved, the request status, and timestamps.
    """
    # Reference to the user who initiated the swap request.
    requester = db.ReferenceField(document_type='User', required=True, help_text="The user who initiated the swap request.")

    # Reference to the listing owned by the requester that they are offering.
    requester_listing = db.ReferenceField(document_type='Listing', required=True, help_text="The listing offered by the requester.")

    # Reference to the user who is the owner of the desired listing.
    responder = db.ReferenceField(document_type='User', required=True, help_text="The user who is the recipient of the swap request.")

    # Reference to the listing owned by the responder that the requester desires.
    responder_listing = db.ReferenceField(document_type='Listing', required=True, help_text="The listing desired from the responder.")

    # Status of the swap request.
    # 'pending': Request sent, awaiting response.
    # 'accepted': Responder has accepted the swap.
    # 'rejected': Responder has rejected the swap.
    # 'cancelled': Requester has cancelled the request.
    # 'completed': Both parties have confirmed completion (after logistics).
    status = db.StringField(
        required=True,
        default='pending',
        choices=('pending', 'accepted', 'rejected', 'cancelled', 'completed'),
        help_text="Current status of the swap request."
    )

    # Timestamp for when the swap request was initiated.
    requested_date = db.DateTimeField(default=datetime.utcnow, help_text="Date when the swap request was initiated.")

    # Timestamp for when the swap request was last updated (e.g., accepted, rejected).
    updated_date = db.DateTimeField(default=datetime.utcnow, help_text="Date when the swap request was last updated.")

    # Optional message from the requester to the responder.
    message = db.StringField(max_length=500, help_text="Optional message from requester.", null=True)

    # --- Logistics Fields (New) ---
    delivery_method = db.StringField(
        choices=('pickup', 'pudo_locker', 'courier_delivery'),
        help_text="Method chosen for item delivery.",
        null=True
    )
    logistics_status = db.StringField(
        choices=('awaiting_setup', 'awaiting_pickup', 'in_transit', 'ready_for_collection', 'delivered', 'failed'),
        default='awaiting_setup',
        help_text="Current status of the item's logistics."
    )
    pickup_location_details = db.StringField(max_length=255, help_text="Details for pickup location (e.g., address, PUDO locker ID).", null=True)
    delivery_address_details = db.StringField(max_length=255, help_text="Details for delivery address.", null=True)
    tracking_number = db.StringField(max_length=100, help_text="Tracking number for courier or PUDO.", null=True)
    logistics_provider = db.StringField(max_length=50, help_text="Name of the logistics provider (e.g., PUDO, DHL).", null=True)
    
    # Define a Meta class for MongoEngine specific configurations.
    meta = {
        'collection': 'swap_requests', # Explicitly set the collection name
        'indexes': [
            {'fields': ('requester',)},
            {'fields': ('responder',)},
            {'fields': ('requester_listing',)},
            {'fields': ('responder_listing',)},
            {'fields': ('status',)},
            {'fields': ('logistics_status',)}, # Index new logistics status
            {'fields': ('-requested_date',)}
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
        String representation of the SwapRequest object.
        """
        return f"SwapRequest(Requester: {self.requester.username}, Responder: {self.responder.username}, Status: {self.status}, Logistics: {self.logistics_status})"

