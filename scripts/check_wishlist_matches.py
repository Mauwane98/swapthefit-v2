import sys
import os
from datetime import datetime, timedelta
from flask import url_for

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models.wishlist import WishlistItem
from app.models.listings import Listing
from app.models.notifications import Notification
from app.services.notification_service import add_notification
from app.extensions import db

def check_wishlist_matches():
    app = create_app()
    with app.app_context():
        print("Starting wishlist match check...")

        # Define the time window for new listings (e.g., last 24 hours)
        # This ensures we only check against recently added listings
        time_window = datetime.utcnow() - timedelta(hours=24)
        new_listings = Listing.objects(date_posted__gte=time_window).all()

        wishlist_items = WishlistItem.objects(notification_sent=False).all()

        for wishlist_item in wishlist_items:
            user = wishlist_item.user
            
            # Skip if the wishlist item is for a specific listing that already exists
            if wishlist_item.listing and wishlist_item.listing in new_listings:
                # If it's a specific listing and it's new, we should notify
                # But we also need to ensure we don't notify the listing owner about their own listing
                if wishlist_item.listing.user.id != user.id:
                    # Check if notification already exists for this user and specific listing
                    existing_notification = Notification.objects(
                        user=user,
                        notification_type='wishlist_match',
                        payload__wishlist_item_id=str(wishlist_item.id),
                        payload__listing_id=str(wishlist_item.listing.id)
                    ).first()

                    if not existing_notification:
                        listing_url = url_for('listings.listing_detail', listing_id=str(wishlist_item.listing.id), _external=True)
                        message = f"A listing matching your wishlist is available: {wishlist_item.listing.title}. View here: {listing_url}"
                        
                        send_notification(
                            user=user,
                            message=message,
                            notification_type='wishlist_match',
                            payload={
                                'wishlist_item_id': str(wishlist_item.id),
                                'listing_id': str(wishlist_item.listing.id),
                                'listing_url': listing_url
                            }
                        )
                        wishlist_item.notification_sent = True
                        wishlist_item.save()
                        print(f"Notification created for {user.username} for specific listing: {wishlist_item.listing.title}")
                continue # Move to the next wishlist item

            # For general wishlist items (not tied to a specific listing)
            matching_listings = []
            for listing in new_listings:
                # Skip if the listing is by the same user who created the wishlist
                if listing.user.id == user.id:
                    continue

                is_match = True
                
                if wishlist_item.item_category and listing.uniform_type != wishlist_item.item_category:
                    is_match = False
                if wishlist_item.item_type and listing.item_type != wishlist_item.item_type:
                    is_match = False
                if wishlist_item.item_size and listing.size != wishlist_item.item_size:
                    is_match = False
                if wishlist_item.school_name and listing.school_name != wishlist_item.school_name:
                    is_match = False
                if wishlist_item.condition and listing.condition != wishlist_item.condition:
                    is_match = False
                
                if is_match:
                    matching_listings.append(listing)
            
            for matched_listing in matching_listings:
                # Check if notification already exists for this user, wishlist item, and matched listing
                existing_notification = Notification.objects(
                    user=user,
                    notification_type='wishlist_match',
                    payload__wishlist_item_id=str(wishlist_item.id),
                    payload__listing_id=str(matched_listing.id)
                ).first()

                if not existing_notification:
                    listing_url = url_for('listings.listing_detail', listing_id=str(matched_listing.id), _external=True)
                    message = f"A new listing matching your wishlist is available: {matched_listing.title}. View here: {listing_url}"
                    
                    add_notification(
                        user_id=user.id,
                        message=message,
                        notification_type='wishlist_match',
                        payload={
                            'wishlist_item_id': str(wishlist_item.id),
                            'listing_id': str(matched_listing.id),
                            'listing_url': listing_url
                        }
                    )
                    # We don't set wishlist_item.notification_sent = True here
                    # because a general wishlist item can match multiple listings over time.
                    # The notification check above prevents duplicates for the same match.
                    print(f"Notification created for {user.username} for general wishlist item: {matched_listing.title}")
                else:
                    print(f"Notification already exists for {user.username} for wishlist item {wishlist_item.id} and listing {matched_listing.id}")

        print("Wishlist match check completed.")

if __name__ == "__main__":
    check_wishlist_matches()
