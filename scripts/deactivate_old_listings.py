import sys
import os
from datetime import datetime, timedelta
from flask import url_for

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models.listings import Listing
from app.models.notifications import Notification
from app.extensions import db
from app.services.email_service import send_email

# Configuration for listing deactivation
LISTING_ACTIVE_PERIOD_DAYS = 90
NOTIFICATION_BEFORE_DEACTIVATION_DAYS = 7

def deactivate_old_listings():
    app = create_app()
    with app.app_context():
        print("Starting old listing deactivation check...")

        # Calculate deactivation threshold
        deactivation_threshold = datetime.utcnow() - timedelta(days=LISTING_ACTIVE_PERIOD_DAYS)
        
        # Find listings that are active and older than the deactivation threshold
        old_active_listings = Listing.objects(
            date_posted__lt=deactivation_threshold,
            is_available=True
        )

        for listing in old_active_listings:
            print(f"Deactivating listing: {listing.title} (ID: {listing.id})")
            listing.is_available = False
            listing.save()

            # Send notification to owner about deactivation
            notification_message = f"Your listing '{listing.title}' has been automatically deactivated due to inactivity ({LISTING_ACTIVE_PERIOD_DAYS} days). You can reactivate it from your dashboard."
            notification = Notification(
                user=listing.user,
                message=notification_message,
                notification_type='listing_deactivated',
                payload={'listing_id': str(listing.id)}
            )
            notification.save()
            print(f"Notification sent to {listing.user.username} for deactivation of {listing.title}")

            if listing.user.email:
                send_email(
                    to=listing.user.email,
                    subject=f"Your Listing Deactivated: {listing.title}",
                    template='emails/listing_deactivated.html',
                    user=listing.user,
                    listing=listing
                )

        # Calculate notification threshold
        notification_threshold_start = datetime.utcnow() - timedelta(days=LISTING_ACTIVE_PERIOD_DAYS - NOTIFICATION_BEFORE_DEACTIVATION_DAYS)
        notification_threshold_end = datetime.utcnow() - timedelta(days=LISTING_ACTIVE_PERIOD_DAYS - NOTIFICATION_BEFORE_DEACTIVATION_DAYS - 1) # To catch listings within a 24-hour window

        # Find listings that are active and within the notification window
        listings_for_notification = Listing.objects(
            date_posted__lt=notification_threshold_start,
            date_posted__gte=notification_threshold_end,
            is_available=True
        )

        for listing in listings_for_notification:
            # Check if a notification for this specific pre-deactivation has already been sent
            existing_notification = Notification.objects(
                user=listing.user,
                notification_type='listing_pre_deactivation_warning',
                payload__listing_id=str(listing.id)
            ).first()

            if not existing_notification:
                print(f"Sending pre-deactivation warning for listing: {listing.title} (ID: {listing.id})")
                notification_message = f"Your listing '{listing.title}' will be automatically deactivated in {NOTIFICATION_BEFORE_DEACTIVATION_DAYS} days due to inactivity. Please update it to keep it active."
                notification = Notification(
                    user=listing.user,
                    message=notification_message,
                    notification_type='listing_pre_deactivation_warning',
                    payload={'listing_id': str(listing.id)}
                )
                notification.save()
                print(f"Notification sent to {listing.user.username} for pre-deactivation of {listing.title}")

                if listing.user.email:
                    send_email(
                        to=listing.user.email,
                        subject=f"Upcoming Listing Deactivation: {listing.title}",
                        template='emails/listing_pre_deactivation_warning.html',
                        user=listing.user,
                        listing=listing,
                        days_left=NOTIFICATION_BEFORE_DEACTIVATION_DAYS
                    )
            else:
                print(f"Pre-deactivation warning already sent for {listing.title}")

        print("Old listing deactivation check completed.")

if __name__ == "__main__":
    deactivate_old_listings()
