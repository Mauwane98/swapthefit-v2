from flask import Flask
from app.config import Config
from app.extensions import mongo, jwt, mail

def create_app(config_class=Config):
    """
    Application factory function.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]

    # Initialize Flask extensions
    mongo.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)

    # Import and register blueprints inside the factory
    from app.blueprints.landing.routes import landing_bp
    from app.blueprints.auth.routes import auth_bp
    from app.blueprints.listings.routes import listings_bp
    from app.blueprints.messaging.routes import messaging_bp
    from app.blueprints.admin.routes import admin_bp
    
    app.register_blueprint(landing_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(listings_bp)
    app.register_blueprint(messaging_bp, url_prefix="/messages")
    # This line is now active
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # A simple health check endpoint to verify the a pp is running
    @app.get("/health")
    def health():
        return {"status": "ok"}, 200

    return app
