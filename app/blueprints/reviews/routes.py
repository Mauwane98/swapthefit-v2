# app/blueprints/reviews/routes.py
from flask import Blueprint, render_template, url_for, flash, redirect, request, abort
from flask_login import login_required, current_user
from app.models.reviews import Review
from app.models.users import User
from app.models.listings import Listing # Needed for linking reviews to listings
# Assuming you have models for SwapRequest, Order, Donation to validate transaction_id
from app.models.swaps import SwapRequest # Example for transaction validation
from app.models.payments import Order # Example for transaction validation
from app.models.donations import Donation # Example for transaction validation
from app.blueprints.reviews.forms import ReviewForm
from app.extensions import db
from app.blueprints.notifications.routes import add_notification # Import for review notifications
from mongoengine.queryset.visitor import Q


reviews_bp = Blueprint('reviews', __name__)

def update_user_trust_score(user_id):
    """
    Recalculates and updates a user's trust score based on their reviews,
    transaction history, and dispute resolution.
    """
    user = User.objects.get(id=user_id)
    if not user:
        return

    # 1. Review-based score
    received_reviews = Review.objects(reviewed_user=user.id)
    user.positive_reviews_count = 0
    user.negative_reviews_count = 0
    sum_of_ratings = 0
    total_reviews = 0

    for review in received_reviews:
        if review.is_positive:
            user.positive_reviews_count += 1
        else:
            user.negative_reviews_count += 1
        sum_of_ratings += review.rating
        total_reviews += 1

    review_score = 50.0 # Default if no reviews
    if total_reviews > 0:
        review_score = (sum_of_ratings / total_reviews) * 20 # Scale to 0-100

    # 2. Transaction-based score
    # Assuming total_transactions is updated when orders/swaps/donations complete
    # This is a placeholder; actual implementation needs to increment this counter
    # in the respective blueprints (payments, swaps, donations).
    transaction_score = 0.0
    if user.total_transactions > 0:
        # Simple linear scaling: more transactions = higher score, up to a cap
        transaction_score = min(user.total_transactions / 10.0, 1.0) * 100 # Max 100 for 10+ transactions

    # 3. Dispute-based score
    # Assuming resolved_disputes_count and fault_disputes_count are updated when disputes are resolved
    dispute_score = 50.0 # Default
    total_disputes = user.resolved_disputes_count + user.fault_disputes_count
    if total_disputes > 0:
        # Higher score for more resolved disputes vs. fault disputes
        dispute_ratio = user.resolved_disputes_count / total_disputes
        dispute_score = dispute_ratio * 100 # Scale to 0-100

    # Combine scores with weights (adjust weights as needed)
    # Example weights: reviews (60%), transactions (20%), disputes (20%)
    user.trust_score = (
        (review_score * 0.6) +
        (transaction_score * 0.2) +
        (dispute_score * 0.2)
    )
    
    # Ensure trust score is within 0-100 range
    user.trust_score = max(0.0, min(100.0, user.trust_score))

    user.save()


from flask import Blueprint, render_template, url_for, flash, redirect, request, abort, current_app # Added current_app
from flask_login import login_required, current_user
from app.models.reviews import Review
from app.models.users import User
from app.models.listings import Listing # Needed for linking reviews to listings
# Assuming you have models for SwapRequest, Order, Donation to validate transaction_id
from app.models.swaps import SwapRequest # Example for transaction validation
from app.models.payments import Order # Example for transaction validation
from app.models.donations import Donation # Example for transaction validation
from app.blueprints.reviews.forms import ReviewForm
from app.extensions import db
from app.blueprints.notifications.routes import add_notification # Import for review notifications
from mongoengine.queryset.visitor import Q
# Import the save_pictures function from listings blueprint
from app.blueprints.listings.routes import save_pictures # Import save_pictures


reviews_bp = Blueprint('reviews', __name__)

def update_user_trust_score(user_id):
    """
    Recalculates and updates a user's trust score based on their reviews,
    transaction history, and dispute resolution.
    """
    user = User.objects.get(id=user_id)
    if not user:
        return

    # 1. Review-based score
    received_reviews = Review.objects(reviewed_user=user.id)
    user.positive_reviews_count = 0
    user.negative_reviews_count = 0
    sum_of_ratings = 0
    total_reviews = 0

    for review in received_reviews:
        if review.is_positive:
            user.positive_reviews_count += 1
        else:
            user.negative_reviews_count += 1
        sum_of_ratings += review.rating
        total_reviews += 1

    review_score = 50.0 # Default if no reviews
    if total_reviews > 0:
        review_score = (sum_of_ratings / total_reviews) * 20 # Scale to 0-100

    # 2. Transaction-based score
    # Assuming total_transactions is updated when orders/swaps/donations complete
    # This is a placeholder; actual implementation needs to increment this counter
    # in the respective blueprints (payments, swaps, donations).
    transaction_score = 0.0
    if user.total_transactions > 0:
        # Simple linear scaling: more transactions = higher score, up to a cap
        transaction_score = min(user.total_transactions / 10.0, 1.0) * 100 # Max 100 for 10+ transactions

    # 3. Dispute-based score
    # Assuming resolved_disputes_count and fault_disputes_count are updated when disputes are resolved
    dispute_score = 50.0 # Default
    total_disputes = user.resolved_disputes_count + user.fault_disputes_count
    if total_disputes > 0:
        # Higher score for more resolved disputes vs. fault disputes
        dispute_ratio = user.resolved_disputes_count / total_disputes
        dispute_score = dispute_ratio * 100 # Scale to 0-100

    # Combine scores with weights (adjust weights as needed)
    # Example weights: reviews (60%), transactions (20%), disputes (20%)
    user.trust_score = (
        (review_score * 0.6) +
        (transaction_score * 0.2) +
        (dispute_score * 0.2)
    )
    
    # Ensure trust score is within 0-100 range
    user.trust_score = max(0.0, min(100.0, user.trust_score))

    user.save()


@reviews_bp.route("/review/submit/<string:reviewed_user_id>", methods=['GET', 'POST'])
@login_required
def submit_review(reviewed_user_id):
    """
    Allows the current user to submit a review for another user.
    Handles image uploads for the review.
    """
    reviewed_user = User.objects.get_or_404(id=reviewed_user_id)

    # Prevent reviewing oneself
    if current_user.id == reviewed_user.id:
        flash('You cannot review yourself.', 'danger')
        return redirect(url_for('listings.user_profile', user_id=str(reviewed_user.id)))

    form = ReviewForm()
    if form.validate_on_submit():
        # Handle image uploads for the review
        review_image_files = []
        if form.review_images.data:
            review_image_files = save_pictures(form.review_images.data)
            if not review_image_files:
                flash('Failed to save review images. Please try again.', 'danger')
                return render_template('reviews/submit_review.html', title='Submit Review', form=form, reviewed_user=reviewed_user)

        transaction_id = form.transaction_id.data
        rating = form.rating.data
        communication_rating = form.communication_rating.data
        logistics_rating = form.logistics_rating.data
        item_as_described = form.item_as_described.data
        comment = form.comment.data

        # --- Transaction Validation (Crucial for legitimate reviews) ---
        # You need to verify that a completed transaction (swap, sale, or donation)
        # with the given transaction_id exists between current_user and reviewed_user.
        # This is a placeholder; actual logic depends on your transaction models.
        transaction_exists = False
        transaction_type = None # 'swap', 'order', 'donation'
        related_listing_id = None

        # Example: Check in SwapRequest model
        swap = SwapRequest.objects(
            Q(id=transaction_id) &
            (
                (Q(initiator=current_user.id) & Q(respondent=reviewed_user.id)) |
                (Q(initiator=reviewed_user.id) & Q(respondent=current_user.id))
            ) &
            Q(status='completed') # Only allow reviews for completed swaps
        ).first()
        if swap:
            transaction_exists = True
            transaction_type = 'swap'
            # Assuming a swap involves listings, pick one for review context
            related_listing_id = swap.offered_listing.id if swap.offered_listing else (swap.requested_listing.id if swap.requested_listing else None)

        # Example: Check in Order model (for sales)
        if not transaction_exists:
            order = Order.objects(
                Q(id=transaction_id) &
                (
                    (Q(buyer=current_user.id) & Q(seller=reviewed_user.id)) |
                    (Q(buyer=reviewed_user.id) & Q(seller=current_user.id))
                ) &
                Q(status='completed') # Only allow reviews for completed orders
            ).first()
            if order:
                transaction_exists = True
                transaction_type = 'sale'
                related_listing_id = order.listing.id if order.listing else None
        
        # Example: Check in Donation model
        if not transaction_exists:
            donation = Donation.objects(
                Q(id=transaction_id) &
                (
                    (Q(donor=current_user.id) & Q(recipient=reviewed_user.id)) |
                    (Q(donor=reviewed_user.id) & Q(recipient=current_user.id))
                ) &
                Q(status='completed') # Only allow reviews for completed donations
            ).first()
            if donation:
                transaction_exists = True
                transaction_type = 'donation'
                related_listing_id = donation.listing.id if donation.listing else None

        if not transaction_exists:
            flash('Invalid or uncompleted transaction ID. You can only review completed transactions.', 'danger')
            return render_template('reviews/submit_review.html', title='Submit Review', form=form, reviewed_user=reviewed_user)

        # Check if a review already exists for this specific transaction by this reviewer
        existing_review_for_transaction = Review.objects(
            reviewer=current_user.id,
            reviewed_user=reviewed_user.id,
            transaction_id=transaction_id # Assuming you add this to Review model
        ).first()

        if existing_review_for_transaction:
             flash('You have already submitted a review for this transaction.', 'info')
             return redirect(url_for('listings.user_profile', user_id=str(reviewed_user.id)))


        # Determine if the overall review is positive
        is_positive = (rating >= 3) # Define your threshold for positive review

        review = Review(
            reviewer=current_user.id,
            reviewed_user=reviewed_user.id,
            comment=comment,
            rating=rating,
            is_positive=is_positive,
            listing=related_listing_id, # Link to a relevant listing if found
            transaction_id=transaction_id, # Add transaction_id to Review model
            communication_rating=communication_rating,
            logistics_rating=logistics_rating,
            item_as_described=item_as_described,
            image_files=review_image_files # Save image filenames
        )
        review.save()

        # --- Update Reviewed User's Reputation Metrics ---
        # Increment total transactions (if not already done in transaction completion logic)
        # reviewed_user.total_transactions += 1 # This should be done when transaction completes, not on review submission
        
        if is_positive:
            reviewed_user.positive_reviews_count += 1
        else:
            reviewed_user.negative_reviews_count += 1
        
        reviewed_user.save() # Commit user changes

        # Recalculate trust score after review
        update_user_trust_score(reviewed_user.id)

        flash('Your review has been submitted!', 'success')

        # Notify the reviewed user about the new review (in-app notification)
        add_notification(
            user_id=reviewed_user.id,
            message=f"You received a new { 'positive' if is_positive else 'negative' } review from {current_user.username}.",
            notification_type='new_review',
            payload={'reviewer_id': str(current_user.id), 'review_id': str(review.id), 'rating': rating}
        )

        # Send email/SMS alert for new review
        subject = f"New Review for Your Profile ({rating}/5 Stars)"
        email_template = "emails/new_review.html" # You'll need to create this template
        sms_message = f"Hi {reviewed_user.username}, you received a new review with {rating}/5 stars from {current_user.username} on SwapTheFit."
        send_user_alert(
            user_id=reviewed_user.id,
            subject=subject,
            email_template=email_template,
            sms_message=sms_message,
            reviewer_username=current_user.username,
            rating=rating,
            comment=comment,
            review_link=url_for('listings.user_profile', user_id=str(reviewed_user.id), _external=True)
        )

        return redirect(url_for('listings.user_profile', user_id=str(reviewed_user.id)))
    
    return render_template('reviews/submit_review.html', title='Submit Review', form=form, reviewed_user=reviewed_user)

@reviews_bp.route("/reviews/user/<string:user_id>")
@login_required
def user_reviews(user_id):
    """
    Displays all reviews received by a specific user.
    """
    user = User.objects.get_or_404(id=user_id)
    reviews = Review.objects(reviewed_user=user.id).order_by('-date_posted')
    return render_template('reviews/user_reviews.html', title=f"{user.username}'s Reviews", user=user, reviews=reviews)

@reviews_bp.route("/reviews/listing/<string:listing_id>")
@login_required
def listing_reviews(listing_id):
    """
    Displays all reviews associated with a specific listing.
    """
    listing = Listing.objects.get_or_404(id=listing_id)
    reviews = Review.objects(listing=listing.id).order_by('-date_posted')
    return render_template('reviews/listing_reviews.html', title=f"Reviews for {listing.title}", listing=listing, reviews=reviews)

