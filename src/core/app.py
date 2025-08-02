"""
VectorBid Flask Application
Clean factory pattern with simplified configuration and extensions.
"""

import os
import sys
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy.orm import DeclarativeBase
from src.lib.bid_layers_routes import bid_layers_bp

# Configure logging early
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass


# Global extensions (initialized in create_app)
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()


def create_app(config=None):
    """
    Application factory function for VectorBid.

    Args:
        config: Optional configuration dict to override defaults

    Returns:
        Flask app instance
    """
    app = Flask(__name__, template_folder='../ui/templates')
    app.register_blueprint(bid_layers_bp)

    # ===== CONFIGURATION =====
    configure_app(app, config)

    # ===== MIDDLEWARE =====
    configure_middleware(app)

    # ===== EXTENSIONS =====
    configure_extensions(app)

    # ===== DATABASE =====
    configure_database(app)

    # ===== BLUEPRINTS =====
    register_blueprints(app)

    # ===== ERROR HANDLERS =====
    configure_error_handlers(app)

    logger.info("VectorBid application created successfully")
    return app


def configure_app(app, config=None):
    """Configure Flask app with environment variables and overrides."""

    # Core Flask configuration
    app.config.update({
        'SECRET_KEY':
        os.environ.get('SECRET_KEY', 'dev-secret-change-in-production'),
        'SQLALCHEMY_DATABASE_URI':
        os.environ.get('DATABASE_URL', 'sqlite:///vectorbid.db'),
        'SQLALCHEMY_TRACK_MODIFICATIONS':
        False,
        'SQLALCHEMY_ENGINE_OPTIONS': {
            'pool_recycle': 300,
            'pool_pre_ping': True,
            'echo':
            os.environ.get('DEBUG') == '1',  # SQL logging in debug mode
        },

        # Session configuration
        'PERMANENT_SESSION_LIFETIME':
        86400 * 30,  # 30 days
        'SESSION_COOKIE_SECURE':
        os.environ.get('HTTPS') == '1',
        'SESSION_COOKIE_HTTPONLY':
        True,
        'SESSION_COOKIE_SAMESITE':
        'Lax',

        # Application-specific settings
        'MAX_CONTENT_LENGTH':
        16 * 1024 * 1024,  # 16MB max file upload
        'UPLOAD_EXTENSIONS': ['.pdf', '.csv', '.txt'],
        'ADMIN_BEARER_TOKEN':
        os.environ.get('ADMIN_BEARER_TOKEN'),
        'ADMIN_TOKEN':
        os.environ.get(
            'ADMIN_TOKEN',
            'admin-default-token'),  # Added for complete admin portal
        'OPENAI_API_KEY':
        os.environ.get('OPENAI_API_KEY'),

        # Feature flags
        'ENABLE_AI_RANKING':
        os.environ.get('OPENAI_API_KEY') is not None,
        'ENABLE_ADMIN_ENDPOINTS':
        os.environ.get('ADMIN_BEARER_TOKEN') is not None,
        'DEBUG':
        os.environ.get('DEBUG', '0') == '1',
    })

    # Apply any provided config overrides
    if config:
        app.config.update(config)

    # Environment-specific adjustments
    if app.config['DEBUG']:
        app.config['SQLALCHEMY_ENGINE_OPTIONS']['echo'] = True
        logging.getLogger().setLevel(logging.DEBUG)


def configure_middleware(app):
    """Configure middleware for the application."""
    # Handle proxy headers for proper URL generation
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)


def configure_extensions(app):
    """Initialize Flask extensions."""

    # Database
    db.init_app(app)

    # Authentication
    login_manager.init_app(app)
    # Don't set login_view since we're using a different auth system
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        """Load user for Flask-Login."""
        try:
            from src.core.models import User
            return User.query.get(user_id)
        except Exception as e:
            logger.error(f"Error loading user {user_id}: {e}")
            return None


def configure_database(app):
    """Set up database tables and any initial data."""

    # Create tables immediately when app is configured
    with app.app_context():
        try:
            # Import models to register them
            from src.core import models  # noqa: F401

            # Create all tables
            db.create_all()
            logger.info("Database tables created successfully")

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            # Don't fail completely - allow app to start for debugging


def register_blueprints(app):
    """Register application blueprints."""

    # Main application routes - use existing routes.py
    from src.api.routes import bp as main_bp
    app.register_blueprint(main_bp)
    logger.info("Main routes registered successfully")

    # Authentication routes - try to import, but don't fail if missing
    try:
        from src.auth.replit_auth import make_replit_blueprint
        auth_bp = make_replit_blueprint()
        app.register_blueprint(auth_bp, url_prefix='/auth')
        logger.info("Auth routes registered successfully")
    except Exception as e:
        logger.warning(f"Replit auth not available: {e}")

    # COMPLETE ADMIN PORTAL (REPLACES ALL OTHER ADMIN SYSTEMS)
    try:
        from admin_complete import admin_bp
        app.register_blueprint(admin_bp)
        logger.info("✅ Complete admin portal registered successfully")
    except ImportError as e:
        logger.error(f"❌ Complete admin portal not found: {e}")
        logger.warning(
            "Skipping admin portal - will fix admin_complete.py file")
    except Exception as e:
        logger.error(f"❌ Admin portal error: {e}")
        logger.warning("Skipping admin portal due to error")

    logger.info("All blueprints registered successfully")


def register_fallback_routes(app):
    """Register minimal fallback routes if blueprint imports fail."""

    @app.route('/')
    def index():
        return """
        <h1>VectorBid</h1>
        <p>Application is starting up...</p>
        <p>Some components may not be fully loaded yet.</p>
        """

    @app.route('/health')
    def health():
        return {'status': 'ok', 'message': 'VectorBid is running'}


def configure_error_handlers(app):
    """Configure custom error handlers."""

    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Page not found'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal error: {error}")
        db.session.rollback()
        return {'error': 'Internal server error'}, 500

    @app.errorhandler(413)
    def too_large(error):
        return {'error': 'File too large. Maximum size is 16MB.'}, 413


# Helper functions for getting user context
def get_current_user_id():
    """Get current user ID from Replit headers or session."""
    from flask import request, session

    # Try Replit Auth header first
    user_id = request.headers.get('X-Replit-User-Id')
    if user_id:
        return user_id

    # Fallback to session
    return session.get('user_id')


def get_current_user():
    """Get current user object."""
    user_id = get_current_user_id()
    if not user_id:
        return None

    try:
        from models import User
        return User.query.get(user_id)
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        return None


# CLI commands for development
def register_cli_commands(app):
    """Register CLI commands for database management."""

    @app.cli.command()
    def init_db():
        """Initialize the database."""
        db.create_all()
        print("Database initialized!")

    @app.cli.command()
    def reset_db():
        """Reset the database (WARNING: Deletes all data)."""
        if input("Are you sure? This will delete all data. (y/N): ").lower(
        ) == 'y':
            db.drop_all()
            db.create_all()
            print("Database reset!")
        else:
            print("Cancelled.")


# For direct execution
if __name__ == '__main__':
    app = create_app()

    # Register CLI commands
    register_cli_commands(app)

    # Run in development mode
    app.run(host='0.0.0.0',
            port=int(os.environ.get('PORT', 5000)),
            debug=app.config.get('DEBUG', False))
