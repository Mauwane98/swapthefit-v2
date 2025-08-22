import sys
import os
from datetime import datetime, timedelta
from urllib.parse import parse_qs
from flask import url_for

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models.saved_search import SavedSearch
from app.models.listings import Listing
from app.models.notifications import Notification
from app.extensions import db
from app.services.email_service import send_email

def check_saved_searches():
    app = create_app()
    with app.app_context():
        print("Starting saved search check...")

        # Define the time window for new listings (e.g., last 24 hours)
        time_window = datetime.utcnow() - timedelta(hours=24)
        new_listings = Listing.objects(date_posted__gte=time_window)

        saved_searches = SavedSearch.objects.all()

        for search in saved_searches:
            user = search.user
            search_params = parse_qs(search.search_query_params)
            
            # Convert list values from parse_qs to single values for easier comparison
            for key, value in search_params.items():
                if isinstance(value, list) and len(value) == 1:
                    search_params[key] = value[0]
                elif isinstance(value, list) and len(value) > 1:
                    # For now, we'll just take the first, but this could be expanded
                    search_params[key] = value[0]

            matching_listings = []
            for listing in new_listings:
                is_match = True
                
                # Apply filters based on search_params
                if 'uniform_type' in search_params and search_params['uniform_type'] != 'All':
                    if listing.uniform_type != search_params['uniform_type']:
                        is_match = False
                
                if 'size' in search_params and search_params['size'] != 'All':
                    if listing.size != search_params['size']:
                        is_match = False
                
                if 'school' in search_params and search_params['school'] != 'All':
                    if listing.school_name != search_params['school']:
                        is_match = False
                
                if 'brand' in search_params and search_params['brand'] != 'All':
                    if listing.brand != search_params['brand']:
                        is_match = False

                if 'condition' in search_params and search_params['condition'] != 'All':
                    if listing.condition != search_params['condition']:
                        is_match = False

                if 'color' in search_params and search_params['color'] != 'All':
                    if listing.color != search_params['color']:
                        is_match = False
                
                # Price range filtering
                if 'min_price' in search_params and listing.price is not None:
                    try:
                        min_price = float(search_params['min_price'])
                        if listing.price < min_price:
                            is_match = False
                    except ValueError:
                        pass # Ignore invalid price values
                
                if 'max_price' in search_params and listing.price is not None:
                    try:
                        max_price = float(search_params['max_price'])
                        if listing.price > max_price:
                            is_match = False
                    except ValueError:
                        pass # Ignore invalid price values

                if is_match:
                    matching_listings.append(listing)
            
            for matched_listing in matching_listings:
                # Check if notification already exists for this user, listing, and search
                existing_notification = Notification.objects(
                    user=user,
                    notification_type='new_listing_match',
                    payload__listing_id=str(matched_listing.id)
                ).first()

                if not existing_notification:
                    listing_url = url_for('listings.listing_detail', listing_id=str(matched_listing.id), _external=True)
                    message = f"New listing matching your saved search '{search.name}': {matched_listing.title}. View here: {listing_url}"
                    notification = Notification(
                        user=user,
                        message=message,
                        notification_type='new_listing_match',
                        payload={'listing_id': str(matched_listing.id), 'search_id': str(search.id), 'listing_url': listing_url}
                    )
                    notification.save()
                    print(f"Notification created for {user.username}: {message}")

                    # Send email notification
                    if user.email:
                        send_email(
                            to=user.email,
                            subject=f"New Listing Match: {matched_listing.title}",
                            template='emails/new_listing_match.html',
                            user=user,
                            search=search,
                            listing=matched_listing,
                            listing_url=listing_url
                        )
                else:
                    print(f"Notification already exists for {user.username} for listing {matched_listing.id}")

        print("Saved search check completed.")

if __name__ == "__main__":
    check_saved_searches()