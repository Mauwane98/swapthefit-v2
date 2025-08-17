from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.models.notifications import Notification
from app.extensions import socketio # Import socketio for real-time updates
from datetime import datetime

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications', template_folder='templates')

@notifications_bp.route('/')
@login_required
def index():
    """
    Displays all of the current user's notifications, ordered by most recent.
    Also ensures that the unread count is updated after viewing the page.
    """
    # Fetch all notifications for the current user, newest first
    notifications = Notification.objects(recipient=current_user.id).order_by('-created_at').all()

    # Mark all *currently displayed* unread notifications as read
    # This happens when the user visits their notifications inbox.
    unread_on_page = Notification.objects(recipient=current_user.id, read=False)
    for notification in unread_on_page:
        notification.read = True
        notification.read_at = datetime.utcnow()
        notification.save()
    
    # After marking as read, update the global unread count for the user via SocketIO
    # This ensures the badge in the navbar updates immediately.
    total_unread_count = Notification.objects(recipient=current_user.id, read=False).count()
    socketio.emit('update_notification_count', {'count': total_unread_count}, room=str(current_user.id))

    return render_template('notifications/index.html', notifications=notifications)

@notifications_bp.route('/mark-as-read/<string:notification_id>', methods=['POST'])
@login_required
def mark_as_read(notification_id):
    """
    Marks a specific notification as read.
    This route is typically called via AJAX or a form submission from the UI.
    """
    notification = Notification.objects(id=notification_id).first()
    
    if not notification:
        flash('Notification not found.', 'danger')
        return redirect(url_for('notifications.index'))

    # Ensure the current user is the recipient of this notification
    if str(notification.recipient.id) != str(current_user.id):
        flash('You do not have permission to mark this notification as read.', 'danger')
        return redirect(url_for('notifications.index'))

    if not notification.read:
        notification.read = True
        notification.read_at = datetime.utcnow()
        notification.save()
        flash('Notification marked as read.', 'success')
        
        # Emit updated unread count to the user via SocketIO
        total_unread_count = Notification.objects(recipient=current_user.id, read=False).count()
        socketio.emit('update_notification_count', {'count': total_unread_count}, room=str(current_user.id))

    # Redirect to the notification's link if it exists, otherwise back to inbox
    if notification.link:
        return redirect(notification.link)
        
    return redirect(url_for('notifications.index'))

@notifications_bp.route('/delete/<string:notification_id>', methods=['POST'])
@login_required
def delete_notification(notification_id):
    """
    Deletes a specific notification.
    """
    notification = Notification.objects(id=notification_id).first()
    
    if not notification:
        flash('Notification not found.', 'danger')
        return redirect(url_for('notifications.index'))

    # Ensure the current user is the recipient of this notification
    if str(notification.recipient.id) != str(current_user.id):
        flash('You do not have permission to delete this notification.', 'danger')
        return redirect(url_for('notifications.index'))

    try:
        notification.delete()
        flash('Notification deleted.', 'success')
        
        # Emit updated unread count (if a read notification was deleted, count won't change, but it's good practice)
        total_unread_count = Notification.objects(recipient=current_user.id, read=False).count()
        socketio.emit('update_notification_count', {'count': total_unread_count}, room=str(current_user.id))

    except Exception as e:
        current_app.logger.error(f"Error deleting notification {notification_id}: {e}")
        flash('An error occurred while deleting the notification. Please try again.', 'danger')

    return redirect(url_for('notifications.index'))

@notifications_bp.route('/mark-all-as-read', methods=['POST'])
@login_required
def mark_all_as_read():
    """
    Marks all of the current user's unread notifications as read.
    """
    try:
        unread_notifications = Notification.objects(recipient=current_user.id, read=False)
        for notification in unread_notifications:
            notification.read = True
            notification.read_at = datetime.utcnow()
            notification.save()

        flash('All notifications marked as read.', 'success')
        
        # Emit updated unread count to the user via SocketIO
        socketio.emit('update_notification_count', {'count': 0}, room=str(current_user.id))

    except Exception as e:
        current_app.logger.error(f"Error marking all notifications as read for user {current_user.id}: {e}")
        flash('An error occurred while marking all notifications as read. Please try again.', 'danger')

    return redirect(url_for('notifications.index'))
