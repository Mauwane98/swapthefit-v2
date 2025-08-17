from app.extensions import db
from datetime import datetime

class SwapRequest(db.Document):
    """
    Represents a swap request between two users for two listings in the SwapTheFit application.
    This model uses MongoEngine to interact with MongoDB.
    """
    # Reference to the User who initiated the swap request.
    proposer = db.ReferenceField('User', required=True, help_text="The user who proposed the swap.")

    # Reference to the User who received the swap request.
    recipient = db.ReferenceField('User', required=True, help_text="The user who received the swap request.")

    # Reference to the Listing that the proposer is requesting from the recipient.
    requested_listing = db.ReferenceField('Listing', required=True, help_text="The listing the proposer wants from the recipient.")

    # Reference to the Listing that the proposer is offering in exchange.
    offered_listing = db.ReferenceField('Listing', required=True, help_text="The listing the proposer is offering in exchange.")

    # Status of the swap request (e.g., 'pending', 'accepted', 'rejected', 'cancelled', 'completed').
    status = db.StringField(
        required=True,
        default='pending',
        choices=('pending', 'accepted', 'rejected', 'cancelled', 'completed'),
        help_text="Current status of the swap request."
    )

    # Timestamp for when the swap request was proposed.
    date_proposed = db.DateTimeField(default=datetime.utcnow, help_text="Timestamp when the swap request was proposed.")

    # Timestamp for when the swap request was last updated (e.g., status change).
    updated_at = db.DateTimeField(default=datetime.utcnow, help_text="Timestamp when the swap request was last updated.")

    # Define a Meta class for MongoEngine specific configurations.
    meta = {
        'collection': 'swap_requests',  # Explicitly set the collection name in MongoDB
        'indexes': [
            {'fields': ('proposer',)},          # Index by proposer for quick lookup of initiated swaps
            {'fields': ('recipient',)},         # Index by recipient for quick lookup of received swaps
            {'fields': ('requested_listing',)}, # Index by requested listing
            {'fields': ('offered_listing',)},   # Index by offered listing
            {'fields': ('status',)},            # Index by status for filtering pending/accepted swaps
            {'fields': ('-date_proposed',)}   # Descending index on proposal date for latest requests
        ],
        'strict': False # Allows for dynamic fields not explicitly defined in the schema
    }

    def clean(self):
        """
        Custom validation or data cleaning hook provided by MongoEngine.
        This method is called automatically before saving the document.
        Here, we ensure `updated_at` is always current when the document is modified.
        """
        self.updated_at = datetime.utcnow()

    def __repr__(self):
        """
        String representation of the SwapRequest object, useful for debugging.
        """
        proposer_name = self.proposer.username if self.proposer else "Unknown Proposer"
        recipient_name = self.recipient.username if self.recipient else "Unknown Recipient"
        requested_title = self.requested_listing.title if self.requested_listing else "Unknown Requested Listing"
        offered_title = self.offered_listing.title if self.offered_listing else "Unknown Offered Listing"
        return (f"Swap Request (ID: {self.id}) from '{proposer_name}' to '{recipient_name}' "
                f"for '{requested_title}' offering '{offered_title}' (Status: {self.status})")
