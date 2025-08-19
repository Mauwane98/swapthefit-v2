# app/utils/activity_logger.py
from flask import request, current_app
from app.models.user_activity import UserActivity
from app.extensions import db
import json
from datetime import datetime
from app.models.users import User # Import User model

def log_activity(user_id, action_type, description, payload=None, request_obj=None):
    """
    Logs a user's activity to the database.

    Args:
        user_id (int): The ID of the user performing the action.
        action_type (str): A categorized string describing the action (e.g., 'login', 'listing_created').
        description (str): A human-readable summary of the action.
        payload (dict, optional): Additional structured data related to the action. Defaults to None.
        request_obj (flask.Request, optional): The Flask request object to extract IP address. Defaults to None.
    """
    ip_address = None
    if request_obj:
        # Attempt to get the real IP address, considering proxies
        ip_address = request_obj.headers.get('X-Forwarded-For', request_obj.remote_addr)
        # If X-Forwarded-For contains multiple IPs, take the first one
        if ip_address and ',' in ip_address:
            ip_address = ip_address.split(',')[0].strip()

    # Fetch the User object if user_id is provided
    user_obj = None
    if user_id:
        try:
            user_obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            current_app.logger.warning(f"User with ID {user_id} not found for activity logging.")
            user_obj = None # Ensure user_obj is None if user not found

    try:
        activity = UserActivity(
            user=user_obj, # Pass the User object here
            action_type=action_type,
            description=description,
            timestamp=datetime.utcnow(),
            ip_address=ip_address,
            payload=payload
        )
        activity.save()
        current_app.logger.debug(f"Activity logged: User {user_id}, Type: {action_type}, Desc: {description}")
    except Exception as e:
        current_app.logger.error(f"Failed to log user activity for user {user_id}, action {action_type}: {e}")

