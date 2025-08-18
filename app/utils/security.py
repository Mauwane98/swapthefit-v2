from functools import wraps
from flask import redirect, url_for, flash, request, abort
from flask_login import current_user
from app.models.users import User # Import User model to access roles

def roles_required(*roles):
    """
    Custom decorator to restrict access to a route based on user roles.
    Example: @roles_required('admin', 'school')
    This decorator checks if the current_user is authenticated and has
    at least one of the specified roles.
    """
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            # Check if the user is authenticated
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'info')
                # Redirect to login page, passing the current URL as 'next'
                return redirect(url_for('auth.login', next=request.url))
            
            # Check if the user has any of the required roles
            # The User model's has_role method is used for this check.
            if not any(current_user.has_role(role) for role in roles):
                flash('You do not have permission to access this page.', 'danger')
                abort(403) # Forbidden: User does not have the necessary role(s)
            
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper

