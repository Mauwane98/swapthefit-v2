from app.extensions import db
from datetime import datetime

class Review(db.Document):
    """
    Represents a review given by one user to another within the SwapTheFit application.
    This model uses MongoEngine to interact with MongoDB.
    """
    # Reference to the User who provided the review.
    reviewer = db.ReferenceField('User', required=True, help_text="The user who wrote this review.")

    # Reference to the User who is being reviewed.
    reviewed_user = db.ReferenceField('User', required=True, help_text="The user who is being reviewed.")

    # Numerical rating given by the reviewer (e.g., 1 to 5 stars).
    # Choices enforce valid rating values.
    rating = db.IntField(required=True, min_value=1, max_value=5, help_text="The numerical rating (1-5 stars).")

    # Optional text comment accompanying the review.
    comment = db.StringField(max_length=500, help_text="Optional text comment for the review.")

    # Timestamp for when the review was posted.
    date_posted = db.DateTimeField(default=datetime.utcnow, help_text="Timestamp when the review was posted.")

    # Define a Meta class for MongoEngine specific configurations.
    meta = {
        'collection': 'reviews',  # Explicitly set the collection name in MongoDB
        'indexes': [
            {'fields': ('reviewer',)},      # Index by reviewer for faster lookup of reviews given by a user
            {'fields': ('reviewed_user',)}, # Index by reviewed user for faster retrieval of reviews for a user
            {'fields': ('-date_posted',)} # Descending index on date_posted for latest reviews
        ],
        'strict': False # Allows for dynamic fields not explicitly defined in the schema
    }

    @staticmethod
    def get_average_rating(user_id):
        reviews = Review.objects(reviewed_user=user_id)
        if reviews:
            total_rating = sum(review.rating for review in reviews)
            return total_rating / len(reviews)
        return 0

    @staticmethod
    def has_reviewed(reviewer_id, reviewed_user_id):
        return Review.objects(reviewer=reviewer_id, reviewed_user=reviewed_user_id).first() is not None

    def __repr__(self):
        """
        String representation of the Review object, useful for debugging.
        """
        reviewer_name = self.reviewer.username if self.reviewer else "Unknown Reviewer"
        reviewed_name = self.reviewed_user.username if self.reviewed_user else "Unknown Reviewed User"
        return f"Review by '{reviewer_name}' for '{reviewed_name}': {self.rating} stars"

