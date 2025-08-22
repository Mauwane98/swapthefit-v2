from app.extensions import db
from datetime import datetime

class Donation(db.Document):
    """
    Represents a donation transaction in the system.
    This model tracks items being donated, the donor, and the recipient (School/NGO).
    It now includes fields to quantify the impact for reporting.
    """
    # Reference to the user who is making the donation.
    donor = db.ReferenceField(document_type='User', required=True, help_text="The user making the donation.")

    # Reference to the listing being donated.
    donated_listing = db.ReferenceField(document_type='Listing', required=True, help_text="The listing being donated.")

    # Reference to the recipient of the donation (a User with role 'school' or 'ngo').
    recipient = db.ReferenceField(document_type='User', required=True, help_text="The school or NGO receiving the donation.")

    # Status of the donation (e.g., 'pending_pickup', 'received', 'distributed').
    # 'pending_pickup': Donor has initiated donation, awaiting pickup/drop-off.
    # 'received': Recipient has confirmed receipt of the item.
    # 'distributed': Recipient has distributed the item to a learner/individual.
    status = db.StringField(
        required=True,
        default='pending_pickup',
        choices=('pending_pickup', 'received', 'distributed'),
        help_text="Current status of the donation."
    )

    # New fields for NGO Impact Reports
    # Quantity of items in this specific donation (e.g., 1 uniform set, 5 shirts)
    quantity = db.IntField(required=True, min_value=1, default=1, help_text="Number of items in the donation.")
    # Estimated monetary value of the donated items (e.g., for reporting total value of donations)
    estimated_value = db.FloatField(required=True, min_value=0.0, default=0.0, help_text="Estimated monetary value of the donated items.")
    # Optional: Number of families/individuals supported by this specific donation
    families_supported = db.IntField(min_value=0, default=0, help_text="Number of families/individuals directly supported by this donation.")


    # Timestamp for when the donation was initiated.
    donation_date = db.DateTimeField(default=datetime.utcnow, help_text="Date when the donation was initiated.")

    # Timestamp for when the donation status was last updated.
    updated_date = db.DateTimeField(default=datetime.utcnow, help_text="Date when the donation was last updated.")

    # Optional notes about the donation (e.g., condition on receipt, distribution details).
    notes = db.StringField(max_length=500, help_text="Optional notes about the donation.", null=True)

    # Define a Meta class for MongoEngine specific configurations.
    meta = {
        'collection': 'donations', # Explicitly set the collection name
        'indexes': [
            {'fields': ('donor',)},
            {'fields': ('donated_listing',)},
            {'fields': ('recipient',)},
            {'fields': ('status',)},
            {'fields': ('-donation_date',)}
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
        String representation of the Donation object.
        """
        return f"Donation(Listing: {self.donated_listing.title}, Donor: {self.donor.username}, Recipient: {self.recipient.username}, Status: {self.status})"

    def to_dict(self):
        """
        Converts the Donation object to a dictionary.
        """
        return {
            'id': str(self.id), # Convert ObjectId to string
            'donor_id': str(self.donor.id) if self.donor else None,
            'donor_username': self.donor.username if self.donor else None,
            'donated_listing_id': str(self.donated_listing.id) if self.donated_listing else None,
            'donated_listing_title': self.donated_listing.title if self.donated_listing else None,
            'recipient_id': str(self.recipient.id) if self.recipient else None,
            'recipient_username': self.recipient.username if self.recipient else None,
            'status': self.status,
            'quantity': self.quantity,
            
'estimated_value': self.estimated_value,
            'families_supported': self.families_supported,
            'donation_date': self.donation_date.isoformat() + 'Z',
            'updated_date': self.updated_date.isoformat() + 'Z',
            'notes': self.notes
        }
