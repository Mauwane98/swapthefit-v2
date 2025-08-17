from flask import Flask
from flask_login import current_user
from app.config import Config
from app.extensions import mongo, login_manager, mail, moment

def create_app(config_class=Config):
    """
    Application factory function to create and configure the Flask app.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions with the app instance
    mongo.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    moment.init_app(app)

    # CRITICAL: Import models and blueprints *inside* the factory function.
    # This avoids circular import errors by ensuring extensions like 'db' are
    # initialized before the models or blueprints try to import them.
    from app.models.users import User
    from app.models.listings import Listing
    from app.models.messages import Message
    from app.models.wishlist import Wishlist
    from app.models.reviews import Review
    from app.models.notifications import Notification
    from app.models.swaps import SwapRequest

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

    # Configure the login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.find_by_id(user_id)

    @app.context_processor
    def inject_notifications():
        if current_user.is_authenticated:
            # Use a more specific query to avoid conflicts
            unread_count = Notification.count_unread(current_user.id)
            return dict(unread_notifications=unread_count)
        return dict(unread_notifications=0)
    
    return app
