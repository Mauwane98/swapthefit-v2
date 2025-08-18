from flask_wtf import FlaskForm
from wtforms import SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError
from app.models.listings import Listing
from flask_login import current_user

class ProposeSwapForm(FlaskForm):
    """
    Form for proposing a swap for a specific listing.
    The user selects one of their own active listings to offer in exchange.
    """
    # This field will be dynamically populated in the route.
    # It shows the user's available listings.
    your_listing_id = SelectField(
        'Your Item to Offer for Swap',
        validators=[DataRequired(message="Please select an item you wish to offer.")],
        choices=[], # Choices will be populated dynamically in the route
        render_kw={"class": "block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"}
    )
    
    message = TextAreaField(
        'Message to Seller (Optional)',
        validators=[Length(max=500)],
        render_kw={"placeholder": "Add a message about why you want to swap or any details.", "rows": 4, "class": "block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"}
    )
    
    submit = SubmitField('Propose Swap', render_kw={"class": "w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"})

    def __init__(self, *args, **kwargs):
        super(ProposeSwapForm, self).__init__(*args, **kwargs)
        if current_user.is_authenticated:
            # Populate choices with the user's own active listings
            # Only listings that are 'available' and not premium (as premium implies sale)
            # and are not themselves donation listings (donations are one-way)
            # Listings that are for 'sale' cannot be offered for swap either.
            user_active_listings = Listing.objects(
                owner=current_user.id,
                is_active=True,
                status='available',
                listing_type='swap' # Only allow 'swap' type listings to be offered
            )
            self.your_listing_id.choices = [
                (str(listing.id), f"{listing.title} ({listing.size}) - {listing.condition}")
                for listing in user_active_listings
            ]
            # Add a default empty choice if no listings are available or as a prompt
            if not self.your_listing_id.choices:
                self.your_listing_id.choices.insert(0, ('', 'You have no available swap items'))
            else:
                self.your_listing_id.choices.insert(0, ('', 'Select an item to offer'))

