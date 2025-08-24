from flask import Blueprint, flash, redirect, url_for, render_template
from flask_login import login_required, current_user
from app.models.users import User
from app.models.follows import Follow
from mongoengine.errors import NotUniqueError

follows_bp = Blueprint('follows', __name__)

@follows_bp.route('/follow/<string:user_id>')
@login_required
def follow_user(user_id):
    user_to_follow = User.objects.get_or_404(id=user_id)

    if current_user.id == user_to_follow.id:
        flash('You cannot follow yourself!', 'danger')
        return redirect(url_for('listings.user_profile', user_id=user_id))

    try:
        follow = Follow(follower=current_user.id, followed=user_to_follow.id)
        follow.save()
        flash(f'You are now following {user_to_follow.username}!', 'success')
    except NotUniqueError:
        flash(f'You are already following {user_to_follow.username}.', 'info')
    except Exception as e:
        flash(f'Error following user: {e}', 'danger')
    
    return redirect(url_for('listings.user_profile', user_id=user_id))

@follows_bp.route('/unfollow/<string:user_id>')
@login_required
def unfollow_user(user_id):
    user_to_unfollow = User.objects.get_or_404(id=user_id)

    if current_user.id == user_to_unfollow.id:
        flash('You cannot unfollow yourself!', 'danger')
        return redirect(url_for('listings.user_profile', user_id=user_id))

    try:
        follow = Follow.objects(follower=current_user.id, followed=user_to_unfollow.id).first()
        if follow:
            follow.delete()
            flash(f'You have unfollowed {user_to_unfollow.username}.', 'success')
        else:
            flash(f'You are not following {user_to_unfollow.username}.', 'info')
    except Exception as e:
        flash(f'Error unfollowing user: {e}', 'danger')
    
    return redirect(url_for('listings.user_profile', user_id=user_id))

@follows_bp.route('/feed')
@login_required
def feed():
    listings = current_user.get_followed_users_listings()
    return render_template('follows/feed.html', listings=listings, title='Your Feed')