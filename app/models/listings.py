from app.extensions import db
from datetime import datetime

class Listing(db.Document):
    """
    Represents a clothing item listing available for swap in the system.
    This model uses MongoEngine to interact with MongoDB.
    """
    # Reference to the User who created this listing.
    # 'User' is implicitly linked as it's another MongoEngine Document.
    owner = db.ReferenceField('User', required=True, help_text="The user who owns this listing.")

    # Title of the listing, required field.
    title = db.StringField(required=True, max_length=150, help_text="A concise title for the listing.")

    # Detailed description of the clothing item.
    description = db.StringField(required=True, help_text="A detailed description of the clothing item.")

    # Category of the clothing (e.g., "Tops", "Bottoms", "Dresses", "Outerwear").
    category = db.StringField(required=True, max_length=50, help_text="Category of the clothing (e.g., 'Tops', 'Dresses').")

    # Size of the clothing (e.g., "S", "M", "L", "XL", "One Size").
    size = db.StringField(required=True, max_length=20, help_text="Size of the clothing (e.g., 'M', 'L').")

    # Condition of the clothing (e.g., "New with tags", "Like new", "Good", "Used").
    condition = db.StringField(required=True, max_length=50, help_text="Condition of the item (e.g., 'Like new', 'Good').")

    # List of image URLs for the listing.
    # Default placeholder image if no images are provided.
    school_name = db.StringField(max_length=100, help_text="Name of the school if the item is uniform specific.")

    # List of image URLs for the listing.
    # Default placeholder image if no images are provided.
    images = db.ListField(db.StringField(), default=['https://placehold.co/400x300/CCCCCC/333333?text=No+Image'])

    # Desired swap items or categories the owner is looking for.
    # This helps in matching potential swaps.
    desired_swap_items = db.StringField(max_length=500, help_text="What items the owner is looking for in exchange.")

    # Status of the listing (e.g., "available", "pending_swap", "swapped", "unavailable").
    status = db.StringField(
        required=True,
        default='available',
        choices=('available', 'pending_swap', 'swapped', 'unavailable'),
        help_text="Current status of the listing."
    )

    # Timestamp for when the listing was created.
    created_at = db.DateTimeField(default=datetime.utcnow, help_text="Timestamp when the listing was created.")

    # Timestamp for when the listing was last updated.
    updated_at = db.DateTimeField(default=datetime.utcnow, help_text="Timestamp when the listing was last updated.")

    # Boolean to indicate if the listing is currently active and visible.
    is_active = db.BooleanField(default=True, help_text="Whether the listing is active and visible on the marketplace.")

    # Define a Meta class for MongoEngine specific configurations.
    meta = {
        'collection': 'listings',  # Explicitly set the collection name in MongoDB
        'indexes': [
            {'fields': ('owner',)},        # Index by owner for faster user-specific queries
            {'fields': ('status',)},       # Index by status for marketplace filtering
            {'fields': ('category',)},     # Index by category for filtering
            {'fields': ('size',)},         # Index by size for filtering
                        {'fields': ('-created_at',)} # Descending index on creation date for latest listings # Descending index on creation date for latest listings
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
        String representation of the Listing object, useful for debugging.
        """
        return f"Listing('{self.title}', Owner: {self.owner.username if self.owner else 'N/A'})"
