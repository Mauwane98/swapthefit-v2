# app/blueprints/notifications/routes.py
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.notifications import Notification
from app.models.users import User # Needed to get user info if displaying sender of a message notification
from app.extensions import db
import json
from app.blueprints.notifications.forms import NotificationSettingsForm

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/notifications')
@login_required
def index():
    """
    Displays the current user's notifications.
    Supports filtering by read status (all, unread).
    """
    filter_status = request.args.get('filter', 'all') # 'all' or 'unread'

    if filter_status == 'unread':
        notifications = Notification.objects(user=current_user.id, is_read=False).order_by('-timestamp')
    else:
        notifications = Notification.objects(user=current_user.id).order_by('-timestamp')
    
    return render_template('notifications/index.html', notifications=notifications, filter_status=filter_status, title="My Notifications")

@notifications_bp.route('/notifications/mark_read/<notification_id>', methods=['POST'])
@login_required
def mark_read(notification_id):
    """
    Marks a specific notification as read.
    """
    notification = Notification.objects(id=notification_id, user=current_user.id).first()
    if notification:
        notification.is_read = True
        notification.save()
        flash('Notification marked as read.', 'success')
    else:
        flash('Notification not found or unauthorized.', 'danger')
    return redirect(url_for('notifications.index'))

@notifications_bp.route('/notifications/mark_all_read', methods=['POST'])
@login_required
def mark_all_read():
    """
    Marks all of the current user's unread notifications as read.
    """
    Notification.objects(user=current_user.id, is_read=False).update(set__is_read=True)
    flash('All notifications marked as read.', 'success')
    return redirect(url_for('notifications.index'))

@notifications_bp.route('/notifications/delete/<notification_id>', methods=['POST'])
@login_required
def delete_notification(notification_id):
    """
    Deletes a specific notification for the current user.
    """
    notification = Notification.objects(id=notification_id, user=current_user.id).first()
    if notification:
        notification.delete()
        flash('Notification deleted.', 'success')
    else:
        flash('Notification not found or unauthorized.', 'danger')
    return redirect(url_for('notifications.index'))

@notifications_bp.route('/api/notifications/unread_count')
@login_required
def api_unread_count():
    """
    API endpoint to get the count of unread notifications for the current user.
    """
    unread_count = Notification.objects(user=current_user.id, is_read=False).count()
    return jsonify({'unread_count': unread_count})

# Helper function to create and add a notification
def add_notification(user_id, message, notification_type='general', payload=None):
    """
    Creates and adds a new notification to the database.
    Emits a SocketIO event to the recipient for real-time updates.
    
    Args:
        user_id (str): The ID of the user to notify.
        message (str): The display message for the notification.
        notification_type (str): Category of the notification (e.g., 'wishlist_update', 'new_message').
        payload (dict, optional): A dictionary of additional data to store with the notification.
    """
    from flask import current_app
    from app.extensions import socketio

    user = User.objects(id=user_id).first()
    if not user:
        current_app.logger.warning(f"Attempted to add notification for non-existent user ID: {user_id}")
        return

    new_notification = Notification(
        user=user,
        message=message,
        notification_type=notification_type,
        payload=payload
    )
    new_notification.save()

    # Emit SocketIO event for real-time notification
    try:
        unread_count = Notification.objects(user=user.id, is_read=False).count()
        socketio.emit(
            'new_notification',
            {'message': message, 'count': unread_count, 'notification_type': notification_type, 'payload': payload},
            room=str(user.id)
        )
        current_app.logger.info(f"Emitted new_notification to user {user.username} (ID: {user.id})")
    except Exception as e:
        current_app.logger.error(f"Error emitting SocketIO notification for user {user.id}: {e}")

    return new_notification

@notifications_bp.route('/notifications/settings', methods=['GET', 'POST'])
@login_required
def notification_settings():
    form = NotificationSettingsForm()
    if form.validate_on_submit():
        current_user.notify_new_message = form.notify_new_message.data
        current_user.notify_listing_update = form.notify_listing_update.data
        current_user.notify_swap_request = form.notify_swap_request.data
        current_user.notify_forum_reply = form.notify_forum_reply.data
        current_user.notify_new_follower = form.notify_new_follower.data
        current_user.notify_admin_announcement = form.notify_admin_announcement.data
        current_user.save()
        flash('Your notification preferences have been updated!', 'success')
        return redirect(url_for('notifications.notification_settings'))
    elif request.method == 'GET':
        form.notify_new_message.data = current_user.notify_new_message
        form.notify_listing_update.data = current_user.notify_listing_update
        form.notify_swap_request.data = current_user.notify_swap_request
        form.notify_forum_reply.data = current_user.notify_forum_reply
        form.notify_new_follower.data = current_user.notify_new_follower
        form.notify_admin_announcement.data = current_user.notify_admin_announcement
    return render_template('notifications/settings.html', title='Notification Settings', form=form)
