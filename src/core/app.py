"""
Flask application factory for VectorBid - FIXED VERSION
"""

import os

from flask import Flask

from src.core.extensions import db


def create_app(config_name='development'):
    """Create and configure Flask app with correct paths"""

    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Set correct template and static folders
    template_folder = os.path.join(project_root, "src", "ui", "templates")
    static_folder = os.path.join(project_root, "src", "ui", "static")

    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)

    # Configuration based on environment
    if config_name == 'testing':
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test-secret-key"
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        app.config["WTF_CSRF_ENABLED"] = False
    else:
        app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///vectorbid.db")
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size

    # Initialize extensions
    db.init_app(app)
    
    # Only create tables in non-testing mode
    if config_name != 'testing':
        with app.app_context():
            # Import models to register tables
            import src.core.models  # noqa: F401
            db.create_all()

    # Debug: Print paths to verify they're correct (only in non-testing mode)
    if config_name != 'testing':
        print(f"Template folder: {template_folder}")
        print(f"Static folder: {static_folder}")
        print(f"Template folder exists: {os.path.exists(template_folder)}")
        print(f"Static folder exists: {os.path.exists(static_folder)}")

    # Register main routes blueprint
    try:
        from src.api.routes import bp as main_bp

        app.register_blueprint(main_bp)
        if config_name != 'testing':
            print("✅ Main routes registered!")
    except ImportError as e:
        if config_name != 'testing':
            print(f"❌ Failed to register main routes: {e}")

    # Register admin portal - try only the fixed version
    try:
        from src.api.admin_unified import unified_admin

        app.register_blueprint(unified_admin)
        if config_name != 'testing':
            print("✅ Unified admin system registered!")
    except ImportError:
        if config_name != 'testing':
            print("⚠️ Admin portal not available")

    # Add a simple health check route for debugging
    @app.route("/health")
    def health_check():
        return {
            "status": "ok",
            "template_folder": app.template_folder,
            "static_folder": app.static_folder,
            "template_exists": (
                os.path.exists(app.template_folder) if app.template_folder else False
            ),
            "static_exists": (os.path.exists(app.static_folder) if app.static_folder else False),
        }

    # Register Flask API endpoints
    try:
        from src.api.flask_api_adapter import api_v1

        app.register_blueprint(api_v1)
        if config_name != 'testing':
            print("✅ Flask API v1 endpoints registered!")
    except ImportError as e:
        if config_name != 'testing':
            print(f"⚠️ Flask API adapter not available: {e}")

    # Add a test route to verify the app is working
    @app.route("/test")
    def test_route():
        return "<h1>VectorBid Test Route Working!</h1><p>If you see this, the Flask app is running correctly.</p>"

    return app
