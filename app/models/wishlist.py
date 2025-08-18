from app.extensions import db
from datetime import datetime

class Wishlist(db.Document):
    """
    Represents a user's wishlist in the SwapTheFit application, storing listings
    that a user is interested in. This model uses MongoEngine.
    """
    # Reference to the User who owns this wishlist.
    user = db.ReferenceField(document_type='User', required=True, help_text="The user who owns this wishlist.")

    # Reference to the Listing that is added to the wishlist.
    listing = db.ReferenceField(document_type='Listing', required=True, help_text="The listing added to the wishlist.")

    # Timestamp for when the listing was added to the wishlist.
    added_at = db.DateTimeField(default=datetime.utcnow, help_text="Timestamp when the listing was added to the wishlist.")

    # Define a Meta class for MongoEngine specific configurations.
    meta = {
        'collection': 'wishlist_items',  # Explicitly set the collection name in MongoDB
        'indexes': [
            # Compound index to ensure a user can only add a specific listing to their wishlist once.
            {'fields': ('user', 'listing'), 'unique': True},
            {'fields': ('user',)},        # Index by user for faster retrieval of a user's wishlist
            {'fields': ('listing',)},     # Index by listing for checking if a listing is wishlisted by anyone
            {'fields': ('-added_at',)}  # Descending index on added_at for showing recently added items
        ],
        'strict': False # Allows for dynamic fields not explicitly defined in the schema
    }

    def __repr__(self):
        """
        String representation of the Wishlist item, useful for debugging.
        """
        user_name = self.user.username if self.user else "Unknown User"
        listing_title = self.listing.title if self.listing else "Unknown Listing"
        return f"Wishlist item: User '{user_name}' added Listing '{listing_title}'"
