# app/services/user_reputation_service.py
from app.models.users import User
from app.models.reviews import Review
from app.models.disputes import Dispute # Assuming Dispute model is used for dispute-based score
from app.extensions import db # Assuming db is needed for queries

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

def increment_transaction_count(user_id):
    """
    Increments the total_transactions count for a user.
    """
    user = User.objects.get(id=user_id)
    if user:
        user.total_transactions += 1
        user.save()
        update_user_trust_score(user_id) # Recalculate trust score after transaction

def update_dispute_counts(user_id, resolution_status):
    """
    Updates dispute counts for a user based on the resolution status.
    'resolved_in_favor_of_initiator' or 'resolved_in_favor_of_respondent'
    """
    user = User.objects.get(id=user_id)
    if user:
        if resolution_status == 'resolved_in_favor_of_initiator':
            # If user is initiator and it's in their favor, or user is respondent and it's against them
            # This logic needs to be carefully applied based on who the user_id refers to to (initiator or respondent of the dispute)
            # For simplicity, let's assume this function is called for the user whose counts are being updated.
            user.resolved_disputes_count += 1
        elif resolution_status == 'resolved_in_favor_of_respondent':
            user.fault_disputes_count += 1 # Assuming this means the user was at fault
        user.save()
        update_user_trust_score(user_id) # Recalculate trust score after dispute update