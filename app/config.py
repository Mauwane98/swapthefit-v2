import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration settings."""
    # Secret key for signing cookies and JWTs. It's crucial to change this
    # to a strong, randomly generated value in production.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-very-secret-key-that-you-should-change-in-production-!!!!'

    # MongoDB settings
    # Ensure MONGO_URI is set in your .env file, e.g., MONGO_URI="mongodb://localhost:27017/swapthefit_db"
    # Replace 'localhost:27017' with your MongoDB host if it's remote.
    # 'swapthefit_db' is the default database name if not specified in MONGO_URI.
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/swapthefit_db'

    # Flask-Mail settings for sending notifications and password resets
    # These details are specific to the provided SMTP configuration.
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'mail.riseandshinechess.co.za'
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 465))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'false').lower() in ['true', 'on', '1'] # Use TLS if true
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'true').lower() in ['true', 'on', '1'] # Use SSL if true (often mutually exclusive with TLS)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'olerato@riseandshinechess.co.za'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'wszxderfc1'
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'olerato@riseandshinechess.co.za' # Default sender email address

    # Google OAuth settings for social login
    # You need to obtain these from the Google API Console.
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

    # JWT settings (for API authentication, if applicable)
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'another-super-secret-jwt-key-for-api-tokens'

    # Session and Cookie Security Enhancements
    # Forces cookies to be sent over HTTPS only, enhancing security.
    SESSION_COOKIE_SECURE = True
    # Prevents client-side JavaScript from accessing the session cookie, reducing XSS risks.
    SESSION_COOKIE_HTTPONLY = True
    # Prevents "remember me" cookies from being accessed by client-side scripts.
    REMEMBER_COOKIE_HTTPONLY = True
    # Forces "remember me" cookies to be sent over HTTPS.
    REMEMBER_COOKIE_SECURE = True
    # Set the SameSite attribute for cookies for CSRF protection (e.g., 'Lax', 'Strict', 'None').
    # 'Lax' is often a good default that balances security and usability.
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_SAMESITE = 'Lax'

    # Flask-WTF CSRF Protection
    # Enables CSRF protection for all forms.
    CSRF_ENABLED = True
    # Secret key for CSRF tokens. Should be different from SECRET_KEY.
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY') or 'a-unique-csrf-secret-key'

    # Pagination settings (example, adjust as needed)
    POSTS_PER_PAGE = 10
