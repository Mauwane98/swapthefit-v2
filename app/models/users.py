# app/models/users.py
from datetime import datetime
from app.extensions import db, login_manager, bcrypt
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
import json # For handling blocked_users_json

@login_manager.user_loader
def load_user(user_id):
    """
    Loads a user from the database given their ID.
    Required by Flask-Login.
    """
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None

class User(db.Document, UserMixin):
    """
    User Model: Represents a user of the application.
    Includes authentication details, profile information, and relationships
    to listings, messages, and other user-specific data.
    """
    
    username = db.StringField(max_length=20, unique=True, required=True)
    email = db.StringField(max_length=120, unique=True, required=True)
    image_file = db.StringField(max_length=120, required=True, default='default.jpg') # Profile picture filename
    password = db.StringField(max_length=60, required=True) # Hashed password
    date_joined = db.DateTimeField(required=True, default=datetime.utcnow)
    active = db.BooleanField(default=True) # Field to indicate if user account is active
    
    # User roles: 'parent', 'school', 'ngo', 'admin'
    role = db.StringField(max_length=20, required=True, default='parent') 

    # Fields for User Reputation/Rating System Expansion
    trust_score = db.FloatField(required=True, default=50.0) 
    total_transactions = db.IntField(required=True, default=0)
    positive_reviews_count = db.IntField(required=True, default=0)
    negative_reviews_count = db.IntField(required=True, default=0)
    resolved_disputes_count = db.IntField(required=True, default=0)
    fault_disputes_count = db.IntField(required=True, default=0)

    # Field for User Blocking Feature
    blocked_users_json = db.StringField(required=True, default='[]') 

    # New fields for NGO Impact Reports (only relevant for users with role='ngo')
    total_donations_received_count = db.IntField(required=True, default=0) # Total items received
    total_donations_value = db.FloatField(required=True, default=0.0) # Total estimated value of items
    total_families_supported_ytd = db.IntField(required=True, default=0) # Total families supported (Year-To-Date)

    # Field for contact person for school/NGO roles
    contact_person = db.StringField(max_length=100, required=False)


    # Relationships to other models
    # saved_searches = db.relationship('SavedSearch', backref='user_saver', lazy=True)
    # wishlist_items = db.relationship('WishlistItem', backref='user_wisher', lazy=True)


    def get_reset_token(self, expires_sec=1800):
        """
        Generates a signed token for password reset functionality.
        The token expires after a specified number of seconds.
        """
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id}, expires_in=expires_sec).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        """
        Verifies a password reset token and returns the user if valid.
        """
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
            return User.objects.get(id=user_id)
        except (
            BadSignature, 
            SignatureExpired, 
            KeyError, 
            User.DoesNotExist # Catch if user_id from token doesn't exist
        ) as e:
            current_app.logger.warning(f"Password reset token verification failed: {e}")
            return None

    def get_blocked_users(self):
        """
        Retrieves the list of user IDs blocked by this user.
        """
        try:
            return json.loads(self.blocked_users_json)
        except json.JSONDecodeError:
            return []

    def add_blocked_user(self, user_id_to_block):
        """
        Adds a user ID to the list of blocked users.
        """
        blocked_users = self.get_blocked_users()
        if user_id_to_block not in blocked_users:
            blocked_users.append(user_id_to_block)
            self.blocked_users_json = json.dumps(blocked_users)

    def remove_blocked_user(self, user_id_to_unblock):
        """
        Removes a user ID from the list of blocked users.
        """
        blocked_users = self.get_blocked_users()
        if user_id_to_unblock in blocked_users:
            blocked_users.remove(user_id_to_unblock)
            self.blocked_users_json = json.dumps(blocked_users)

    def is_blocking(self, user_id_to_check):
        """
        Checks if this user is blocking a given user ID.
        """
        return user_id_to_check in self.get_blocked_users()

    def is_blocked_by(self, user_id_checking):
        """
        Checks if this user is blocked by another user.
        Requires querying the other user's blocked list.
        """
        other_user = User.objects(id=user_id_checking).first()
        if other_user:
            return self.id in other_user.get_blocked_users()
        return False


    def set_password(self, password):
        """
        Hashes the given password using bcrypt and stores it.
        """
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """
        Checks if the given password matches the stored hashed password.
        """
        return bcrypt.check_password_hash(self.password, password)

    def has_role(self, role_name):
        """
        Checks if the user has the specified role.
        """
        return self.role == role_name

    def __repr__(self):
        """
        String representation of the User object.
        """
        return f"User('{self.username}', '{self.email}', '{self.image_file}', '{self.role}')"

    def to_dict(self):
        """
        Converts the User object to a dictionary, useful for JSON serialization.
        """
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'image_file': self.image_file,
            'date_joined': self.date_joined.isoformat() + 'Z',
            'role': self.role,
            'trust_score': self.trust_score,
            'total_transactions': self.total_transactions,
            'positive_reviews_count': self.positive_reviews_count,
            'negative_reviews_count': self.negative_reviews_count,
            'resolved_disputes_count': self.resolved_disputes_count,
            'fault_disputes_count': self.fault_disputes_count,
            'blocked_users': self.get_blocked_users(), # Include blocked users in dict representation
            'total_donations_received_count': self.total_donations_received_count,
            'total_donations_value': self.total_donations_value,
            'total_families_supported_ytd': self.total_families_supported_ytd
        }
