from app.extensions import mongo
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer as Serializer, SignatureExpired, BadTimeSignature
from flask import current_app
from bson.objectid import ObjectId

class User(UserMixin):
    """
    Represents a user in the system, interacting with MongoDB.
    """
    def __init__(self, username, email, password_hash, _id=None, is_admin=False, role='parent'):
        self._id = _id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.is_admin = is_admin
        self.role = role

    @property
    def id(self):
        return str(self._id) # MongoDB _id is an ObjectId, convert to string for Flask-Login

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except (SignatureExpired, BadTimeSignature):
            return None
        return User.find_by_id(user_id)

    @staticmethod
    def find_by_email(email):
        print(f"Attempting to find user by email: {email}")
        user_data = mongo.db.users.find_one({'email': email})
        if user_data:
            print(f"Found user data: {user_data}")
            return User(
                _id=user_data['_id'],
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                is_admin=user_data.get('is_admin', False),
                role=user_data['role']
            )
        print("User data not found.")
        return None

    @staticmethod
    def find_by_username(username):
        print(f"Attempting to find user by username: {username}")
        user_data = mongo.db.users.find_one({'username': username})
        if user_data:
            print(f"Found user data: {user_data}")
            return User(
                _id=user_data['_id'],
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                is_admin=user_data.get('is_admin', False),
                role=user_data['role']
            )
        print("User data not found.")
        return None

    def save(self):
        print(f"Attempting to save user: {self.email}")
        user_data = {
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'is_admin': self.is_admin,
            'role': self.role
        }
        if self._id:
            print(f"Updating existing user with _id: {self.id}")
            mongo.db.users.update_one({'_id': ObjectId(self.id)}, {'$set': user_data})
        else:
            print("Inserting new user.")
            result = mongo.db.users.insert_one(user_data)
            self._id = result.inserted_id
            print(f"New user inserted with _id: {self._id}")

    @staticmethod
    def find_by_id(user_id):
        print(f"Attempting to find user by ID: {user_id}")
        try:
            # Ensure user_id is a valid ObjectId
            oid = ObjectId(user_id)
        except Exception:
            print("Invalid ObjectId format.")
            return None # Invalid ObjectId format

        user_data = mongo.db.users.find_one({'_id': oid})
        if user_data:
            print(f"Found user data: {user_data}")
            return User(
                _id=user_data['_id'],
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                is_admin=user_data.get('is_admin', False),
                role=user_data['role']
            )
        print("User data not found.")
        return None