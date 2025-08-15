from app.extensions import mongo
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from flask import current_app
from itsdangerous import URLSafeTimedSerializer as Serializer

class User:
    """User Model"""

    def __init__(self, name, email, role="parent", school_name=None):
        self.name = name
        self.email = email
        self.password_hash = None
        self.role = role
        self.school_name = school_name
        self.verified = False
        self.created_at = datetime.datetime.utcnow()
        self.updated_at = datetime.datetime.utcnow()

    def set_password(self, password):
        """Hashes and sets the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks if the provided password matches the hash."""
        return check_password_hash(self.password_hash, password)

    def save(self):
        """Saves the user to the database."""
        user_data = {
            "name": self.name, "email": self.email, "password_hash": self.password_hash,
            "role": self.role, "school_name": self.school_name, "verified": self.verified,
            "created_at": self.created_at, "updated_at": datetime.datetime.utcnow()
        }
        mongo.db.users.insert_one(user_data)

    def get_reset_token(self, expires_sec=1800):
        """Generates a password reset token."""
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_email': self.email})

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        """Verifies the reset token and returns the user if valid."""
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, max_age=expires_sec)
            user_email = data.get('user_email')
        except:
            return None
        return User.find_by_email(user_email)

    @staticmethod
    def find_by_email(email):
        """Finds a user by their email address."""
        return mongo.db.users.find_one({"email": email})
