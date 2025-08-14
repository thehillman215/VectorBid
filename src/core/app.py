"""
Flask application factory for VectorBid with Fixed Admin Portal
"""

from flask import Flask
import os

def create_app():
    """Create and configure Flask app"""
    app = Flask(__name__, 
                template_folder='../../src/ui/templates',
                static_folder='../../src/ui/static')

    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///vectorbid.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

    # Register blueprints
    from src.api.routes import bp as main_bp
    app.register_blueprint(main_bp)

    # Register admin portal - try fixed version first
    try:
        from admin_portal_fixed import admin_portal
        app.register_blueprint(admin_portal)
        print("✅ Fixed admin portal registered!")
    except ImportError:
        try:
            from admin_portal_enhanced import admin_portal
            app.register_blueprint(admin_portal)
            print("✅ Enhanced admin portal registered!")
        except ImportError:
            try:
                from admin_portal import admin_portal
                app.register_blueprint(admin_portal)
                print("✅ Basic admin portal registered")
            except ImportError:
                print("⚠️ No admin portal available")

    return app
