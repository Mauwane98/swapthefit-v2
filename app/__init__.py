# app/__init__.py
from flask import Flask, render_template, current_app, session, redirect, url_for, flash, request
from flask_login import current_user, login_user
from app.config import Config
from app.extensions import db, login_manager, bcrypt, mail, socketio, csrf
from app.extensions import init_app as init_extensions # Import the init_app function from extensions
from oauthlib.oauth2 import WebApplicationClient
import requests
import json
import os
from datetime import datetime
from bson.objectid import ObjectId # Import ObjectId for MongoEngine user loading

# Google OAuth Configuration
# These are loaded from the Config object which gets values from .env
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

def create_app(config_class=Config):
    """
    Application factory function to create and configure the Flask app.
    Initializes extensions, registers blueprints, and sets up error handlers.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions with the app instance
    init_extensions(app) # Call the init_app function from extensions

    # User loader for Flask-Login
    from app.models.users import User # Import User model here for load_user
    
    @login_manager.user_loader
    def load_user(user_id):
        """
        Loads a user from the database given their ID.
        This function is used by Flask-Login to retrieve the user object
        from the user ID stored in the session.
        """
        try:
            # Ensure user_id is a valid ObjectId before querying
            return User.objects(id=ObjectId(user_id)).first()
        except Exception as e:
            current_app.logger.error(f"Error loading user {user_id}: {e}")
            return None

    # CRITICAL: Import models inside the factory function but outside app_context if needed globally.
    # Blueprints should be registered directly in the factory function.
    with app.app_context():
        # Models can be imported here if they depend on app context for setup (e.g., db.Document)
        # However, for simple field definitions, they can often be imported at the top of their own files.
        # This block is retained as per your original structure, but consider top-level imports in model files.
        from app.models.users import User
        from app.models.listings import Listing
        from app.models.messages import Message
        from app.models.wishlist import WishlistItem # Corrected from Wishlist
        from app.models.reviews import Review
        from app.models.notifications import Notification
        from app.models.swaps import SwapRequest
        from app.models.donations import Donation
        from app.models.payments import Order
        from app.models.saved_search import SavedSearch # Assuming this model exists for MongoEngine
        from app.models.disputes import Dispute # Assuming this model exists for MongoEngine
        # Add any other MongoEngine models here if they are not imported in their respective blueprints

        # Context processor to inject datetime into all templates
        @app.context_processor
        def inject_datetime():
            return dict(datetime=datetime)

        # Context processor to inject unread notification count into all templates
        @app.context_processor
        def inject_notifications():
            if current_user.is_authenticated:
                # Assuming Notification model has 'user_id' and 'is_read' fields for MongoEngine
                # If your MongoEngine model uses 'recipient' and 'read' as in your original code, adjust here.
                unread_count = Notification.objects(user=current_user.id, is_read=False).count()
                return dict(unread_notifications=unread_count)
            return dict(unread_notifications=0)

        # Basic error handlers (can be moved to a separate errors blueprint)
        @app.errorhandler(403)
        def forbidden_error(error):
            return render_template('errors/403.html'), 403

        @app.errorhandler(404)
        def not_found_error(error):
            return render_template('errors/404.html'), 404

        @app.errorhandler(500)
        def internal_error(error):
            current_app.logger.error(f"Internal Server Error: {error}")
            return render_template('errors/500.html'), 500

    # Register Blueprints - These MUST be outside the app_context block
    # Import blueprints here as well to ensure they are available for registration
    from app.blueprints.landing.routes import landing_bp
    from app.blueprints.auth.routes import auth_bp
    from app.blueprints.admin.routes import admin_bp
    from app.blueprints.listings.routes import listings_bp
    from app.blueprints.messaging.routes import messaging_bp
    from app.blueprints.wishlist.routes import wishlist_bp
    from app.blueprints.reviews.routes import reviews_bp
    from app.blueprints.notifications.routes import notifications_bp
    from app.blueprints.swaps.routes import swaps_bp
    from app.blueprints.profile.routes import profile_bp
    from app.blueprints.donations.routes import donations_bp
    from app.blueprints.payments.routes import payments_bp
    from app.blueprints.logistics.routes import logistics_bp # New logistics blueprint
    from app.blueprints.disputes.routes import disputes_bp # New disputes blueprint
    from app.blueprints.reports.routes import reports_bp

    app.register_blueprint(landing_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(listings_bp, url_prefix='/listings')
    app.register_blueprint(messaging_bp, url_prefix='/messaging')
    app.register_blueprint(wishlist_bp, url_prefix='/wishlist')
    app.register_blueprint(reviews_bp, url_prefix='/reviews')
    app.register_blueprint(notifications_bp, url_prefix='/notifications')
    app.register_blueprint(swaps_bp, url_prefix='/swaps')
    app.register_blueprint(profile_bp, url_prefix='/profile')
    app.register_blueprint(donations_bp, url_prefix='/donations')
    app.register_blueprint(payments_bp, url_prefix='/payments')
    app.register_blueprint(logistics_bp, url_prefix='/logistics')
    app.register_blueprint(disputes_bp, url_prefix='/disputes') # Register disputes blueprint
    app.register_blueprint(reports_bp, url_prefix='/reports')

    # Google OAuth Setup - These routes should ideally be in an auth blueprint
    # but are kept here as per your provided structure.
    client = WebApplicationClient(GOOGLE_CLIENT_ID)

    def get_google_provider_cfg():
        """Fetches Google's OpenID Connect discovery document."""
        return requests.get(GOOGLE_DISCOVERY_URL).json()

    @app.route("/auth/google/login")
    def google_login():
        """Initiates Google OAuth login flow."""
        google_provider_cfg = get_google_provider_cfg()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]

        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=request.base_url + "/callback",
            scope=["openid", "email", "profile"],
        )
        return redirect(request_uri)

    @app.route("/auth/google/login/callback")
    def google_callback():
        """Handles Google OAuth callback, processes user data, and logs in/registers."""
        code = request.args.get("code")

        google_provider_cfg = get_google_provider_cfg()
        token_endpoint = google_provider_cfg["token_endpoint"]

        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url,
            redirect_url=request.base_url,
            code=code
        )
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        )

        client.parse_request_body_response(json.dumps(token_response.json()))

        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        if userinfo_response.json().get("email_verified"):
            users_email = userinfo_response.json()["email"]
            picture = userinfo_response.json()["picture"]
            users_name = userinfo_response.json().get("given_name") or userinfo_response.json().get("name")
        else:
            flash("User email not available or not verified by Google.", 'danger')
            return redirect(url_for("auth.login"))

        existing_user = User.objects(email=users_email).first()

        if not existing_user:
            dummy_password = bcrypt.generate_password_hash(os.urandom(16)).decode('utf-8')
            new_user = User(
                username=users_name or users_email.split('@')[0],
                email=users_email,
                password_hash=dummy_password,
                profile_pic=picture,
                active=True,
                last_login=datetime.utcnow(),
                roles=['parent']
            )
            new_user.save()
            login_user(new_user)
            flash('Successfully registered and logged in with Google!', 'success')
        else:
            existing_user.last_login = datetime.utcnow()
            existing_user.profile_pic = picture
            existing_user.save()
            login_user(existing_user)
            flash('Successfully logged in with Google!', 'success')

        if current_user.has_role('admin'):
            return redirect(url_for('admin.dashboard')) # Assuming admin.dashboard exists
        elif current_user.has_role('school'):
            return redirect(url_for('listings.school_dashboard')) # Assuming listings.school_dashboard exists
        elif current_user.has_role('ngo'):
            return redirect(url_for('listings.ngo_dashboard')) # Assuming listings.ngo_dashboard exists
        else:
            return redirect(url_for('listings.dashboard')) # Default to parent dashboard or generic dashboard


    # SocketIO event handlers - These should ideally be in a messaging blueprint
    # but are kept here as per your provided structure.
    @socketio.on('connect')
    def handle_connect():
        if current_user.is_authenticated:
            socketio.join_room(str(current_user.id))
            current_app.logger.info(f"Client connected: {current_user.username} (ID: {current_user.id})")
        else:
            current_app.logger.info("Anonymous client connected.")

    @socketio.on('disconnect')
    def handle_disconnect():
        if current_user.is_authenticated:
            socketio.leave_room(str(current_user.id))
            current_app.logger.info(f"Client disconnected: {current_user.username} (ID: {current_user.id})")
        else:
            current_app.logger.info("Anonymous client disconnected.")

    @socketio.on('send_message')
    def handle_send_message(data):
        sender_id = data.get('sender_id')
        recipient_id = data.get('recipient_id')
        message_content = data.get('message')
        timestamp = datetime.utcnow().isoformat()

        if sender_id and recipient_id and message_content:
            socketio.emit('new_message', {
                'sender_id': sender_id,
                'recipient_id': recipient_id,
                'message': message_content,
                'timestamp': timestamp,
                'from_self': True
            }, room=str(sender_id))
            socketio.emit('new_message', {
                'sender_id': sender_id,
                'recipient_id': recipient_id,
                'message': message_content,
                'timestamp': timestamp,
                'from_self': False
            }, room=str(recipient_id))
            current_app.logger.info(f"Message from {sender_id} to {recipient_id}: {message_content}")
        else:
            current_app.logger.warning("Invalid message data received.")

    @socketio.on('mark_notification_read')
    def handle_mark_notification_read(data):
        notification_id = data.get('notification_id')
        if notification_id and current_user.is_authenticated:
            # Assuming Notification model uses 'id' and 'user' fields for MongoEngine
            notification = Notification.objects(id=notification_id, user=current_user.id).first()
            if notification and not notification.is_read: # Assuming 'is_read' field
                notification.is_read = True
                # notification.read_at = datetime.utcnow() # Add this field to your Notification model if needed
                notification.save()
                unread_count = Notification.objects(user=current_user.id, is_read=False).count()
                socketio.emit('update_notification_count', {'count': unread_count}, room=str(current_user.id))
                current_app.logger.info(f"Notification {notification_id} marked as read for user {current_user.id}")
            else:
                current_app.logger.warning(f"Notification {notification_id} not found or already read for user {current_user.id}.")
        else:
            current_app.logger.warning("Invalid data or user not authenticated for marking notification as read.")

    return app
