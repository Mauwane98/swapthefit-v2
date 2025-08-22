from app.models.users import User
from app.models.disputes import Dispute
from app.models.listings import Listing
from app.models.payments import Order
from app.models.fraud_alerts import FraudAlert
from app.models.reviews import Review
from app.models.swaps import SwapRequest
from app.models.wishlist import WishlistItem
from mongoengine.queryset.visitor import Q
from datetime import datetime, timedelta

class FraudDetectionService:

    @staticmethod
    def _create_fraud_alert(user=None, listing=None, order=None, alert_type="", description="", severity="medium"):
        """
        Helper function to create and save a FraudAlert.
        """
        alert = FraudAlert(
            user=user,
            listing=listing,
            order=order,
            alert_type=alert_type,
            description=description,
            severity=severity
        )
        alert.save()
        return alert

    @staticmethod
    def check_user_dispute_volume(user_id):
        """
        Checks a user's dispute volume and flags if it's unusually high.
        This function should be called when a dispute is created or updated.
        """
        user = User.objects(id=user_id).first()
        if not user:
            return

        # Update dispute counts
        user.dispute_initiator_count = Dispute.objects(initiator=user).count()
        user.dispute_respondent_count = Dispute.objects(respondent=user).count()
        user.save()

        # Example rule: Flag if user is involved in more than 5 disputes in the last 30 days
        # (This is a placeholder, actual thresholds should be data-driven)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_disputes_as_initiator = Dispute.objects(initiator=user, date_raised__gte=thirty_days_ago).count()
        recent_disputes_as_respondent = Dispute.objects(respondent=user, date_raised__gte=thirty_days_ago).count()

        if recent_disputes_as_initiator > 5 or recent_disputes_as_respondent > 5:
            description = f"User {user.username} has been involved in a high volume of disputes recently."
            FraudDetectionService._create_fraud_alert(
                user=user,
                alert_type="high_dispute_volume",
                description=description,
                severity="high"
            )

    @staticmethod
    def analyze_listing_for_suspicion(listing_id):
        """
        Analyzes a listing for suspicious patterns (e.g., fake content, rapid posting).
        This function should be called when a listing is created or updated.
        """
        listing = Listing.objects(id=listing_id).first()
        if not listing:
            return

        user = listing.user
        if not user:
            return

        # Update total listings created by user
        user.total_listings_created = Listing.objects(user=user).count()
        user.save()

        # Example rule 1: Flag if description is too short or contains suspicious keywords
        # (Placeholder: actual keywords/length thresholds need to be defined)
        if len(listing.description) < 20 or "spam_keyword" in listing.description.lower():
            description = f"Listing '{listing.title}' has a suspicious description or is too short."
            FraudDetectionService._create_fraud_alert(
                user=user,
                listing=listing,
                alert_type="suspicious_listing_content",
                description=description,
                severity="medium"
            )
            user.flagged_listings_count += 1
            user.save()

        # Example rule 2: Flag if user posts too many listings in a short period
        # (Placeholder: define time window and count)
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        recent_listings_by_user = Listing.objects(user=user, date_posted__gte=one_day_ago).count()
        if recent_listings_by_user > 10: # More than 10 listings in 24 hours
            description = f"User {user.username} posted a high volume of listings recently."
            FraudDetectionService._create_fraud_alert(
                user=user,
                alert_type="rapid_listing_creation",
                description=description,
                severity="medium"
            )
            user.flagged_listings_count += 1
            user.save()


    @staticmethod
    def monitor_payment_transaction(order_id):
        """
        Monitors a payment transaction for unusual patterns (e.g., high frequency of failed payments).
        This function should be called after a payment attempt (success or failure).
        """
        order = Order.objects(id=order_id).first()
        if not order:
            return

        buyer = order.buyer
        if not buyer:
            return

        # Example rule: Flag if a user has a high number of failed payment attempts
        # (This requires tracking failed attempts, which is not directly in the Order model yet)
        # For now, we'll just increment a counter if the order status indicates failure.
        if order.status == 'failed': # Assuming 'failed' is a possible status for Order
            buyer.failed_payment_attempts += 1
            buyer.save()

            if buyer.failed_payment_attempts > 3: # More than 3 failed attempts
                description = f"User {buyer.username} has a high number of failed payment attempts."
                FraudDetectionService._create_fraud_alert(
                    user=buyer,
                    order=order,
                    alert_type="high_failed_payments",
                    description=description,
                    severity="high"
                )

        # Example rule: Flag unusually large/small transactions for certain listing types
        # (Placeholder: define thresholds and listing types)
        if order.listing and order.listing.listing_type == 'sale':
            if order.amount_paid_total > 10000 or order.amount_paid_total < 10: # Arbitrary thresholds
                description = f"Unusual transaction amount for listing '{order.listing.title}'."
                FraudDetectionService._create_fraud_alert(
                    user=buyer,
                    listing=order.listing,
                    order=order,
                    alert_type="unusual_transaction_amount",
                    description=description,
                    severity="medium"
                )

    @staticmethod
    def delete_listing_and_related_data(listing_id):
        """
        Deletes a listing and all its related data, such as reviews,
        swap requests, and wishlist items.
        """
        listing = Listing.objects(id=listing_id).first()
        if not listing:
            return

        # Delete reviews associated with the listing
        Review.objects(listing=listing).delete()

        # Delete swap requests associated with the listing
        SwapRequest.objects(Q(requester_listing=listing) | Q(responder_listing=listing)).delete()

        # Delete wishlist items for this listing
        WishlistItem.objects(listing=listing).delete()

        # Finally, delete the listing itself
        listing.delete()