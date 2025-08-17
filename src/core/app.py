
"""
Flask application factory for VectorBid - FIXED VERSION
"""

import os

from flask import Flask
from src.core.extensions import db


def create_app():
    """Create and configure Flask app with correct paths"""

    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Set correct template and static folders
    template_folder = os.path.join(project_root, 'src', 'ui', 'templates')
    static_folder = os.path.join(project_root, 'src', 'ui', 'static')

    app = Flask(__name__,
                template_folder=template_folder,
                static_folder=static_folder)

    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///vectorbid.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

    # Initialize extensions
    db.init_app(app)
    with app.app_context():
        # Import models to register tables
        import src.core.models  # noqa: F401
        db.create_all()

    # Debug: Print paths to verify they're correct
    print(f"Template folder: {template_folder}")
    print(f"Static folder: {static_folder}")
    print(f"Template folder exists: {os.path.exists(template_folder)}")
    print(f"Static folder exists: {os.path.exists(static_folder)}")

    # Register main routes blueprint
    try:
        from src.api.routes import bp as main_bp
        app.register_blueprint(main_bp)
        print("✅ Main routes registered!")
    except ImportError as e:
        print(f"❌ Failed to register main routes: {e}")

    # Register admin portal - try only the fixed version
    try:
        from src.api.admin_unified import unified_admin
        app.register_blueprint(unified_admin)
        print("✅ Unified admin system registered!")
    except ImportError:
        print("⚠️ Admin portal not available")

    # Add a simple health check route for debugging
    @app.route('/health')
    def health_check():
        return {
            'status': 'ok',
            'template_folder': app.template_folder,
            'static_folder': app.static_folder,
            'template_exists': os.path.exists(app.template_folder) if app.template_folder else False,
            'static_exists': os.path.exists(app.static_folder) if app.static_folder else False
        }

    # Add a test route to verify the app is working
    @app.route('/test')
    def test_route():
        return '<h1>VectorBid Test Route Working!</h1><p>If you see this, the Flask app is running correctly.</p>'

    return app
