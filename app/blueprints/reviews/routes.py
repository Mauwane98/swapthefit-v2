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
from sqlalchemy import or_

reviews_bp = Blueprint('reviews', __name__)

# Helper function to update user's trust score
def update_user_trust_score(user_id):
    """
    Recalculates and updates a user's trust score based on their reviews.
    This is a simplified calculation; a more complex one might involve
    transaction volume, dispute history, and recency of reviews.
    """
    user = User.query.get(user_id)
    if not user:
        return

    # Get all reviews received by this user
    received_reviews = Review.query.filter_by(reviewed_user_id=user.id).all()
    
    # Reset counts before recalculating
    user.positive_reviews_count = 0
    user.negative_reviews_count = 0
    
    total_ratings = 0
    sum_of_ratings = 0

    for review in received_reviews:
        if review.is_positive:
            user.positive_reviews_count += 1
        else:
            user.negative_reviews_count += 1
        
        total_ratings += 1
        sum_of_ratings += review.rating
    
    # Update total transactions (this should ideally be incremented upon transaction completion)
    # For now, we'll assume a review implies a completed transaction.
    # A more accurate way is to increment total_transactions in swap/payment/donation routes.
    # user.total_transactions = len(received_reviews) # This might overcount if multiple reviews per transaction

    if total_ratings > 0:
        # Simple average for trust score (scaled to 0-100)
        user.trust_score = (sum_of_ratings / total_ratings) * 20 # Max rating 5 * 20 = 100
    else:
        user.trust_score = 50.0 # Default if no reviews

    db.session.commit()


@reviews_bp.route("/review/submit/<int:reviewed_user_id>", methods=['GET', 'POST'])
@login_required
def submit_review(reviewed_user_id):
    """
    Allows the current user to submit a review for another user.
    """
    reviewed_user = User.query.get_or_404(reviewed_user_id)

    # Prevent reviewing oneself
    if current_user.id == reviewed_user.id:
        flash('You cannot review yourself.', 'danger')
        return redirect(url_for('listings.user_profile', user_id=reviewed_user.id))

    form = ReviewForm()
    if form.validate_on_submit():
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
        swap = SwapRequest.query.filter(
            SwapRequest.id == transaction_id,
            or_(
                (SwapRequest.initiator_id == current_user.id) & (SwapRequest.respondent_id == reviewed_user.id),
                (SwapRequest.initiator_id == reviewed_user.id) & (SwapRequest.respondent_id == current_user.id)
            ),
            SwapRequest.status == 'completed' # Only allow reviews for completed swaps
        ).first()
        if swap:
            transaction_exists = True
            transaction_type = 'swap'
            # Assuming a swap involves listings, pick one for review context
            related_listing_id = swap.offered_listing_id or swap.requested_listing_id

        # Example: Check in Order model (for sales)
        if not transaction_exists:
            order = Order.query.filter(
                Order.id == transaction_id,
                or_(
                    (Order.buyer_id == current_user.id) & (Order.seller_id == reviewed_user.id),
                    (Order.buyer_id == reviewed_user.id) & (Order.seller_id == current_user.id)
                ),
                Order.status == 'completed' # Only allow reviews for completed orders
            ).first()
            if order:
                transaction_exists = True
                transaction_type = 'sale'
                related_listing_id = order.listing_id
        
        # Example: Check in Donation model
        if not transaction_exists:
            donation = Donation.query.filter(
                Donation.id == transaction_id,
                or_(
                    (Donation.donor_id == current_user.id) & (Donation.recipient_id == reviewed_user.id),
                    (Donation.donor_id == reviewed_user.id) & (Donation.recipient_id == current_user.id)
                ),
                Donation.status == 'completed' # Only allow reviews for completed donations
            ).first()
            if donation:
                transaction_exists = True
                transaction_type = 'donation'
                related_listing_id = donation.listing_id

        if not transaction_exists:
            flash('Invalid or uncompleted transaction ID. You can only review completed transactions.', 'danger')
            return render_template('reviews/submit_review.html', title='Submit Review', form=form, reviewed_user=reviewed_user)

        # Check if a review already exists for this specific transaction by this reviewer
        existing_review = Review.query.filter_by(
            reviewer_id=current_user.id,
            reviewed_user_id=reviewed_user_id,
            # Assuming transaction_id is stored in Review model or a new linking model
            # For now, we'll assume review is unique per transaction.
            # You might need a more complex check if 'transaction_id' is not directly on Review
        ).first() # This check needs refinement if multiple reviews per transaction are possible, or if transaction_id isn't directly on Review

        # If you add transaction_id to Review model:
        existing_review_for_transaction = Review.query.filter_by(
            reviewer_id=current_user.id,
            reviewed_user_id=reviewed_user_id,
            transaction_id=transaction_id # Assuming you add this to Review model
        ).first()

        if existing_review_for_transaction:
             flash('You have already submitted a review for this transaction.', 'info')
             return redirect(url_for('listings.user_profile', user_id=reviewed_user.id))


        # Determine if the overall review is positive
        is_positive = (rating >= 3) # Define your threshold for positive review

        review = Review(
            reviewer_id=current_user.id,
            reviewed_user_id=reviewed_user_id,
            comment=comment,
            rating=rating,
            is_positive=is_positive,
            listing_id=related_listing_id, # Link to a relevant listing if found
            # Store other specific ratings if you want to save them in the Review model
            # communication_rating=communication_rating,
            # logistics_rating=logistics_rating,
            # item_as_described=item_as_described,
            # transaction_id=transaction_id # You might want to add this to Review model
        )
        db.session.add(review)
        db.session.commit()

        # --- Update Reviewed User's Reputation Metrics ---
        # Increment total transactions (if not already done in transaction completion logic)
        # reviewed_user.total_transactions += 1 # This should be done when transaction completes, not on review submission
        
        if is_positive:
            reviewed_user.positive_reviews_count += 1
        else:
            reviewed_user.negative_reviews_count += 1
        
        db.session.commit() # Commit user changes

        # Recalculate trust score after review
        update_user_trust_score(reviewed_user.id)

        flash('Your review has been submitted!', 'success')

        # Notify the reviewed user about the new review
        add_notification(
            user_id=reviewed_user.id,
            message=f"You received a new { 'positive' if is_positive else 'negative' } review from {current_user.username}.",
            notification_type='new_review',
            payload={'reviewer_id': current_user.id, 'review_id': review.id, 'rating': rating}
        )

        return redirect(url_for('listings.user_profile', user_id=reviewed_user.id))
    
    return render_template('reviews/submit_review.html', title='Submit Review', form=form, reviewed_user=reviewed_user)

@reviews_bp.route("/reviews/user/<int:user_id>")
def user_reviews(user_id):
    """
    Displays all reviews received by a specific user.
    """
    user = User.query.get_or_404(user_id)
    reviews = Review.query.filter_by(reviewed_user_id=user.id).order_by(Review.date_posted.desc()).all()
    return render_template('reviews/user_reviews.html', title=f"{user.username}'s Reviews", user=user, reviews=reviews)

@reviews_bp.route("/reviews/listing/<int:listing_id>")
def listing_reviews(listing_id):
    """
    Displays all reviews associated with a specific listing.
    """
    listing = Listing.query.get_or_404(listing_id)
    reviews = Review.query.filter_by(listing_id=listing.id).order_by(Review.date_posted.desc()).all()
    return render_template('reviews/listing_reviews.html', title=f"Reviews for {listing.title}", listing=listing, reviews=reviews)

