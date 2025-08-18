from app.extensions import db
from datetime import datetime

class Message(db.Document):
    """
    Represents a message sent between users in the SwapTheFit application.
    This model uses MongoEngine to interact with MongoDB.
    """
    # Reference to the User who sent the message.
    sender = db.ReferenceField(document_type='User', required=True, help_text="The user who sent this message.")

    # Reference to the User who received the message.
    recipient = db.ReferenceField(document_type='User', required=True, help_text="The user who received this message.")

    # Reference to the Listing that the message pertains to.
    # This allows conversations to be tied to specific items.
    listing = db.ReferenceField(document_type='Listing', required=True, help_text="The listing this message is about.")

    # The actual content of the message.
    content = db.StringField(required=True, help_text="The text content of the message.")

    # Boolean to track if the message has been read by the recipient.
    is_read = db.BooleanField(default=False, help_text="True if the message has been read by the recipient, False otherwise.")

    # Timestamp for when the message was sent.
    sent_at = db.DateTimeField(default=datetime.utcnow, help_text="Timestamp when the message was sent.")

    # Define a Meta class for MongoEngine specific configurations.
    meta = {
        'collection': 'messages',  # Explicitly set the collection name in MongoDB
        'indexes': [
            {'fields': ('sender',)},     # Index by sender for faster lookup of sent messages
            {'fields': ('recipient',)},  # Index by recipient for faster inbox retrieval
            {'fields': ('listing',)},    # Index by listing for conversation context
            {'fields': ('-sent_at',)}  # Descending index on sent_at for chronological order
        ],
        'strict': False # Allows for dynamic fields not explicitly defined in the schema
    }

    def __repr__(self):
        """
        String representation of the Message object, useful for debugging.
        """
        sender_name = self.sender.username if self.sender else "Unknown Sender"
        recipient_name = self.recipient.username if self.recipient else "Unknown Recipient"
        listing_title = self.listing.title if self.listing else "Unknown Listing"
        return f"Message from '{sender_name}' to '{recipient_name}' about '{listing_title}': '{self.content[:30]}...'"
