from flask import Blueprint, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.models.users import User
from app.models.reviews import Review
from app.models.notifications import Notification # Import Notification model
from app.blueprints.reviews.forms import ReviewForm # Ensure this is the correct import
from app.extensions import socketio # Import socketio for real-time updates
from datetime import datetime

reviews_bp = Blueprint('reviews', __name__, url_prefix='/reviews')

@reviews_bp.route('/add/<string:user_id>', methods=['POST'])
@login_required
def add_review(user_id):
    """
    Handles the submission of a new review for a user.
    This route is typically called from a user's profile page.
    """
    form = ReviewForm()
    reviewed_user = User.objects(id=user_id).first()

    if not reviewed_user:
        flash("User to be reviewed not found.", "danger")
        return redirect(url_for('listings.marketplace')) # Redirect to a safe place

    # Prevent a user from reviewing themselves
    if str(reviewed_user.id) == str(current_user.id):
        flash("You cannot review yourself.", "warning")
        return redirect(url_for('listings.user_profile', user_id=user_id))

    if form.validate_on_submit():
        try:
            # Check if the current user has already reviewed this user
            existing_review = Review.objects(reviewer=current_user.id, reviewed_user=reviewed_user.id).first()
            if existing_review:
                flash("You have already submitted a review for this user.", "info")
                return redirect(url_for('listings.user_profile', user_id=user_id))

            # Create a new Review instance
            review = Review(
                rating=form.rating.data,
                comment=form.comment.data,
                reviewer=current_user.id, # MongoEngine will link this to the User object
                reviewed_user=reviewed_user.id # MongoEngine will link this to the User object
            )
            review.save() # Save the review to MongoDB
            
            # Create a notification for the reviewed user
            notification_message = f"{current_user.username} left you a {review.rating}-star review."
            notification_link = url_for('listings.user_profile', user_id=str(reviewed_user.id), _external=True)

            Notification.create_notification(
                recipient_user=reviewed_user,
                notification_type='new_review',
                message_content=notification_message,
                sender_user=current_user,
                link=notification_link
            )

            # Emit real-time notification to the reviewed user
            socketio.emit('new_notification', {
                'message': notification_message,
                'link': notification_link,
                'timestamp': datetime.utcnow().isoformat(),
                'type': 'new_review'
            }, room=str(reviewed_user.id))

            # Update reviewed user's unread count via SocketIO
            reviewed_user_unread_count = Notification.objects(recipient=reviewed_user.id, read=False).count()
            socketio.emit('update_notification_count', {'count': reviewed_user_unread_count}, room=str(reviewed_user.id))

            flash("Your review has been submitted successfully!", "success")
            return redirect(url_for('listings.user_profile', user_id=user_id))

        except Exception as e:
            current_app.logger.error(f"Error adding review: {e}")
            flash("An error occurred while submitting your review. Please try again.", "danger")
    else:
        # If form validation fails, flash all errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", "danger")

    # Redirect back to the user's profile page, even if validation failed, to show errors
    return redirect(url_for('listings.user_profile', user_id=user_id))

