from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import mongo
from bson.objectid import ObjectId

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

@notifications_bp.route('/')
@login_required
def index():
    """
    Displays all of the current user's notifications, ordered by most recent.
    """
    notifications = mongo.db.notifications.find({'user_id': current_user.id}).sort('timestamp', -1)
    return render_template('notifications/index.html', notifications=notifications)

@notifications_bp.route('/mark-as-read/<notification_id>', methods=['POST'])
@login_required
def mark_as_read(notification_id):
    """
    Marks a specific notification as read.
    """
    notification = mongo.db.notifications.find_one_or_404({'_id': ObjectId(notification_id)})
    if notification['user_id'] != current_user.id:
        flash('You do not have permission to perform this action.', 'danger')
        return redirect(url_for('notifications.index'))

    mongo.db.notifications.update_one({'_id': ObjectId(notification_id)}, {'$set': {'is_read': True}})
    
    # Redirect to the notification's link if it exists
    if notification.get('link'):
        return redirect(notification['link'])
        
    return redirect(url_for('notifications.index'))

@notifications_bp.route('/mark-all-as-read', methods=['POST'])
@login_required
def mark_all_as_read():
    """
    Marks all of the current user's unread notifications as read.
    """
    mongo.db.notifications.update_many({'user_id': current_user.id, 'is_read': False}, {'$set': {'is_read': True}})
    flash('All notifications marked as read.', 'success')
    return redirect(url_for('notifications.index'))
