from flask_mongoengine import MongoEngine
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_socketio import SocketIO
from flask_wtf.csrf import CSRFProtect
from flask_moment import Moment

# Initialize extensions
db = MongoEngine()
login_manager = LoginManager()
bcrypt = Bcrypt()
mail = Mail()
socketio = SocketIO()
csrf = CSRFProtect()
moment = Moment() # Initialize Moment here

def init_app(app):
    """
    Initializes Flask extensions with the given Flask application instance.
    This function sets up the database, login manager, bcrypt for password hashing,
    mail for email sending, SocketIO for real-time communication, and CSRF protection.
    """
    # Configure MongoEngine with the Flask app
    db.init_app(app)

    # Configure LoginManager
    login_manager.init_app(app)
    # Set the view name for the login page. Flask-Login will redirect here
    # if an unauthenticated user tries to access a login-required page.
    login_manager.login_view = 'auth.login'
    # Set the message category for login required flashes.
    login_manager.login_message_category = 'info'
    # Custom message for unauthenticated users.
    login_manager.login_message = 'Please log in to access this page.'

    # Initialize Flask-Bcrypt for password hashing
    bcrypt.init_app(app)

    # Initialize Flask-Mail for email functionality
    mail.init_app(app)

    # Initialize Flask-SocketIO for real-time features.
    # 'async_mode' can be 'eventlet', 'gevent', 'threading', or 'auto'.
    # Using 'eventlet' or 'gevent' is recommended for production.
    socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')

    # Initialize CSRF protection for the application
    csrf.init_app(app)

    # Initialize Flask-Moment for time and date rendering
    moment.init_app(app)