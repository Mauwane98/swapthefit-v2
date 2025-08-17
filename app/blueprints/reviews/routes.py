from flask import Blueprint, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.users import User
from app.models.reviews import Review
from app.models.notifications import Notification # Import Notification model
from .forms import ReviewForm
from app.extensions import mongo

reviews_bp = Blueprint('reviews', __name__, url_prefix='/reviews')

@reviews_bp.route('/add/<user_id>', methods=['POST'])
@login_required
def add_review(user_id):
    """
    Handles the submission of a new review for a user.
    """
    form = ReviewForm()
    reviewed_user = User.get(user_id)

    if reviewed_user.id == current_user.id:
        flash("You cannot review yourself.", "warning")
        return redirect(url_for('listings.user_profile', user_id=user_id))

    if form.validate_on_submit():
        # Check if the current user has already reviewed this user
        existing_review = mongo.db.reviews.find_one({'reviewer_id': current_user.id, 'reviewed_user_id': user_id})
        if existing_review:
            flash("You have already reviewed this user.", "info")
            return redirect(url_for('listings.user_profile', user_id=user_id))

        review = Review(
            rating=form.rating.data,
            comment=form.comment.data,
            reviewer_id=current_user.id,
            reviewed_user_id=user_id
        )
        review.save()
        
        # Create a notification for the reviewed user
        notification = Notification(
            user_id=user_id,
            message=f"{current_user.username} left you a {review.rating}-star review.",
            link=url_for('listings.user_profile', user_id=user_id, _external=True)
        )
        notification.save()
        
        flash("Your review has been submitted successfully!", "success")
    else:
        # Flash form errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", "danger")

    return redirect(url_for('listings.user_profile', user_id=user_id))

