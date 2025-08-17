from app.extensions import db
from datetime import datetime

class Notification(db.Document):
    """
    Represents a notification for a user in the SwapTheFit application.
    This model uses MongoEngine to interact with MongoDB.
    """
    # Reference to the User who is the recipient of this notification.
    recipient = db.ReferenceField('User', required=True, help_text="The user who receives this notification.")

    # Reference to the User who initiated the event that caused this notification (optional).
    # E.g., the sender of a message, or the proposer of a swap.
    sender = db.ReferenceField('User', help_text="The user who triggered this notification (optional).")

    # The type of notification (e.g., 'message', 'swap_request', 'listing_update', 'admin_alert').
    # This helps in rendering different notification types in the UI.
    notification_type = db.StringField(required=True, max_length=50, help_text="Type of notification (e.g., 'message', 'swap_request').")

    # The actual message content of the notification.
    message = db.StringField(required=True, help_text="The content of the notification message.")

    # Optional URL that the user can click to navigate to related content (e.g., a message thread, listing detail).
    link = db.StringField(help_text="Optional URL to direct the user to relevant content.")

    # Boolean to track if the notification has been read by the recipient.
    read = db.BooleanField(default=False, help_text="True if the notification has been read, False otherwise.")

    # Timestamp for when the notification was created.
    created_at = db.DateTimeField(default=datetime.utcnow, help_text="Timestamp when the notification was created.")

    # Timestamp for when the notification was read (optional).
    read_at = db.DateTimeField(help_text="Timestamp when the notification was marked as read.")

    # Define a Meta class for MongoEngine specific configurations.
    meta = {
        'collection': 'notifications',  # Explicitly set the collection name in MongoDB
        'indexes': [
            {'fields': ('recipient',)},     # Index by recipient for faster retrieval of user's notifications
            {'fields': ('read',)},          # Index by read status for fetching unread notifications efficiently
            {'fields': ('-created_at',)}, # Descending index on creation date for latest notifications
            {'fields': ('notification_type',)}, # Index by type for filtering
        ],
        'strict': False # Allows for dynamic fields not explicitly defined in the schema
    }

    def __repr__(self):
        """
        String representation of the Notification object, useful for debugging.
        """
        recipient_name = self.recipient.username if self.recipient else "Unknown Recipient"
        return f"Notification for '{recipient_name}' (Type: {self.notification_type}, Read: {self.read}): '{self.message[:50]}...'"

    # Helper method to create and save a new notification.
    @classmethod
    def create_notification(cls, recipient_user, notification_type, message_content, sender_user=None, link=None):
        """
        Creates and saves a new notification in the database.
        :param recipient_user: The User object who will receive the notification.
        :param notification_type: The type of notification (e.g., 'message', 'swap_request').
        :param message_content: The content of the notification message.
        :param sender_user: Optional. The User object who triggered the notification.
        :param link: Optional. A URL for the user to navigate to.
        :return: The created Notification object.
        """
        notification = cls(
            recipient=recipient_user,
            sender=sender_user,
            notification_type=notification_type,
            message=message_content,
            link=link,
            created_at=datetime.utcnow()
        )
        notification.save()
        return notification
