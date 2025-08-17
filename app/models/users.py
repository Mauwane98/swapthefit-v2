from app.extensions import db, bcrypt, login_manager # Import db (MongoEngine) and bcrypt
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer as Serializer, SignatureExpired, BadTimeSignature
from flask import current_app
from datetime import datetime

# Define available roles for the application.
# These roles will be used for role-based access control (RBAC).
ROLES = ('parent', 'school', 'ngo', 'admin')

class User(db.Document, UserMixin):
    """
    Represents a user in the system, interacting with MongoDB via MongoEngine.
    Inherits from db.Document for MongoEngine integration and UserMixin for Flask-Login compatibility.
    """
    # Unique username for the user, required.
    username = db.StringField(required=True, unique=True, max_length=80)
    # Unique email address for the user, required.
    email = db.StringField(required=True, unique=True, max_length=120)
    # Hashed password for security, required.
    password_hash = db.StringField(required=True)
    # Profile picture URL, optional, with a default placeholder.
    profile_pic = db.StringField(default='https://placehold.co/150x150/E0BBE4/FFFFFF?text=Profile')
    # List of roles assigned to the user, defaulting to 'parent'.
    # This allows for flexible role assignment (e.g., a user can be both 'parent' and 'admin').
    roles = db.ListField(db.StringField(choices=ROLES), default=['parent'])
    # Timestamp for when the user account was created.
    date_joined = db.DateTimeField(default=datetime.utcnow)
    # Boolean to indicate if the user account is active.
    active = db.BooleanField(default=True)
    # Last login timestamp, optional.
    last_login = db.DateTimeField()

    # Define a Meta class for MongoEngine specific configurations.
    meta = {
        'collection': 'users',  # Explicitly set the collection name in MongoDB
        'indexes': [
            {'fields': ('email',), 'unique': True},
            {'fields': ('username',), 'unique': True},
            {'fields': ('roles',)}, # Indexing roles for faster queries on user types
        ],
        'strict': False # Allows for dynamic fields not explicitly defined in the schema
    }

    def set_password(self, password):
        """
        Hashes the provided password and stores it in password_hash.
        """
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """
        Checks if the provided password matches the stored hash.
        """
        return bcrypt.check_password_hash(self.password_hash, password)

    def get_reset_token(self, expires_sec=1800):
        """
        Generates a URL-safe signed token for password reset.
        The token expires after 'expires_sec' seconds.
        """
        s = Serializer(current_app.config['SECRET_KEY'])
        # Store user ID in the token payload.
        return s.dumps({'user_id': str(self.id)}) # Ensure self.id is a string

    @staticmethod
    def verify_reset_token(token):
        """
        Verifies and decodes a password reset token.
        Returns the User object if the token is valid and not expired, otherwise None.
        """
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            # Load the token, checking for expiration and signature validity.
            user_id = s.loads(token, max_age=1800)['user_id']
        except (SignatureExpired, BadTimeSignature):
            return None # Token is invalid or expired
        except Exception as e:
            current_app.logger.error(f"Error verifying reset token: {e}")
            return None
        # Find the user by the extracted user_id.
        return User.objects(id=user_id).first()

    def has_role(self, role):
        """
        Checks if the user has a specific role.
        """
        return role in self.roles

    def __repr__(self):
        """
        String representation of the User object, useful for debugging.
        """
        return f"User('{self.username}', '{self.email}', Roles: {self.roles})"

# The user_loader callback is defined in app/extensions.py and uses this User model.
