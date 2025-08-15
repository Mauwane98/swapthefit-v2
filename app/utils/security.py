from functools import wraps
from flask import abort
from flask_jwt_extended import get_jwt_identity
from app.extensions import mongo
from bson.objectid import ObjectId

def admin_required():
    """
    A decorator factory to protect routes that require admin privileges.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            current_user_id = get_jwt_identity()
            if not current_user_id:
                abort(401)  # Unauthorized

            user = mongo.db.users.find_one({'_id': ObjectId(current_user_id)})
            
            if not user or user.get('role') != 'admin':
                abort(403)  # Forbidden

            return fn(*args, **kwargs)
        return wrapper
    return decorator
