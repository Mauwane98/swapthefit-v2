# app/__init__.py
import os
import logging
from logging import StreamHandler
import sys
import traceback
from flask import Flask, render_template, current_app, redirect, url_for, flash, request
from flask_login import current_user, login_user
from app.config import Config
from app.extensions import login_manager, bcrypt, socketio, init_app as init_extensions
from oauthlib.oauth2 import WebApplicationClient
import requests
import json
from datetime import datetime
from bson.objectid import ObjectId
from app.models.notifications import Notification
from app.models.users import User
from flask_apscheduler import APScheduler # Import APScheduler

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# Initialize scheduler
scheduler = APScheduler()

def create_app(config_class=None):
    """
    Application factory function to create and configure the Flask app.
    Initializes extensions, registers blueprints, and sets up error handlers.
    """
    app = Flask(__name__)
    if config_class is None:
        app.config.from_object(Config)
    else:
        app.config.from_object(config_class)

    # Configure logging for console output
    if app.debug:
        # Create console_handler unconditionally within app.debug block
        console_handler = StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s'))

        # Set app.logger level to DEBUG to capture all messages
        app.logger.setLevel(logging.DEBUG)
        app.logger.addHandler(console_handler) # Always add to app.logger in debug mode

        # Ensure Werkzeug's logger also outputs to console
        werkzeug_logger = logging.getLogger('werkzeug')
        werkzeug_logger.setLevel(logging.INFO) # Set to INFO to capture request logs
        werkzeug_logger.propagate = True # Ensure messages are passed to parent loggers
        werkzeug_logger.addHandler(console_handler) # Always add to werkzeug_logger in debug mode

    app.logger.info('SwapTheFit startup')

    # Initialize Flask extensions with the app instance
    init_extensions(app)

    # Configure and start scheduler
    if not scheduler.running:
        scheduler.init_app(app)
        scheduler.start()

    # Add payout job
    @scheduler.task('interval', id='do_process_payouts', hours=24, misfire_grace_time=900)
    def scheduled_process_payouts():
        with app.app_context():
            current_app.logger.info("Running scheduled payout processing...")
            # Import and run the script's main function
            from scripts.process_payouts import process_payouts
            process_payouts.callback() # Call the underlying function of the click command
            current_app.logger.info("Scheduled payout processing completed.")

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.objects(id=ObjectId(user_id)).first()
        except Exception as e:
            current_app.logger.error(f"Error loading user {user_id}: {e}")
            return None

    with app.app_context():
        # Context processors and error handlers
        @app.context_processor
        def inject_datetime():
            return dict(datetime=datetime)

        @app.context_processor
        def inject_notifications():
            if current_user.is_authenticated:
                unread_count = Notification.objects(user=current_user.id, is_read=False).count()
                return dict(unread_notifications=unread_count)
            return dict(unread_notifications=0)

        @app.errorhandler(403)
        def forbidden_error(error):
            return render_template('errors/403.html'), 403

        @app.errorhandler(404)
        def not_found_error(error):
            return render_template('errors/404.html'), 404

        @app.errorhandler(500)
        def internal_error(error):
            current_app.logger.error(f"Internal Server Error: {error}")
            # Explicitly print traceback to stderr
            traceback.print_exc(file=sys.stderr)
            return render_template('errors/500.html'), 500

    # Register Blueprints
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
    from app.blueprints.logistics.routes import logistics_bp
    from app.blueprints.disputes.routes import disputes_bp
    from app.blueprints.reports.routes import reports_bp
    from app.blueprints.follows.routes import follows_bp
    from app.blueprints.forums.routes import forums_bp # Import forums_bp
    from app.blueprints.sponsored_content.routes import sponsored_content_bp # Import sponsored_content_bp
    from app.blueprints.referrals.routes import referrals_bp # Import referrals_bp
    from app.blueprints.feeds.routes import feeds_bp # Import feeds_bp

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
    app.register_blueprint(disputes_bp, url_prefix='/disputes')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(follows_bp, url_prefix='/follows')
    app.register_blueprint(forums_bp, url_prefix='/forums') # Register forums_bp
    app.register_blueprint(sponsored_content_bp, url_prefix='/sponsored_content') # Register sponsored_content_bp
    app.register_blueprint(referrals_bp, url_prefix='/referrals') # Register referrals_bp
    app.register_blueprint(feeds_bp, url_prefix='/feeds') # Register feeds_bp

    # Google OAuth Setup
    client = WebApplicationClient(GOOGLE_CLIENT_ID)
    def get_google_provider_cfg():
        return requests.get(GOOGLE_DISCOVERY_URL).json()

    @app.route("/auth/google/login")
    def google_login():
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
            return redirect(url_for('admin.dashboard'))
        elif current_user.has_role('school'):
            return redirect(url_for('listings.school_dashboard'))
        elif current_user.has_role('ngo'):
            return redirect(url_for('listings.ngo_dashboard'))
        else:
            return redirect(url_for('listings.dashboard'))

    # SocketIO event handlers
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
        from app.models.messages import Message
        from app.models.users import User

        sender_id = data.get('sender_id')
        recipient_id = data.get('recipient_id')
        message_content = data.get('message')

        if not (sender_id and recipient_id and message_content):
            current_app.logger.warning("Invalid message data received.")
            return

        try:
            sender = User.objects(id=sender_id).first()
            recipient = User.objects(id=recipient_id).first()

            if not (sender and recipient):
                current_app.logger.warning(f"Sender or recipient not found. Sender ID: {sender_id}, Recipient ID: {recipient_id}")
                return

            new_message = Message(
                sender=sender,
                receiver=recipient,
                content=message_content
            )
            new_message.save()

            message_data = new_message.to_dict()

            # Emit to sender
            socketio.emit('new_message', {**message_data, 'from_self': True}, room=str(sender_id))
            # Emit to recipient
            socketio.emit('new_message', {**message_data, 'from_self': False}, room=str(recipient_id))

            current_app.logger.info(f"Message from {sender.username} to {recipient.username} saved and emitted: {message_content}")

        except Exception as e:
            current_app.logger.error(f"Error saving or emitting message: {e}")

    @socketio.on('mark_notification_read')
    def handle_mark_notification_read(data):
        notification_id = data.get('notification_id')
        if notification_id and current_user.is_authenticated:
            notification = Notification.objects(id=notification_id, user=current_user.id).first()
            if notification and not notification.is_read:
                notification.is_read = True
                notification.save()
                unread_count = Notification.objects(user=current_user.id, is_read=False).count()
                socketio.emit('update_notification_count', {'count': unread_count}, room=str(current_user.id))
                current_app.logger.info(f"Notification {notification_id} marked as read for user {current_user.id}")
            else:
                current_app.logger.warning(f"Notification {notification_id} not found or already read for user {current_user.id}.")
        else:
            current_app.logger.warning("Invalid data or user not authenticated for marking notification as read.")

    return app