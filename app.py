
"""VectorBid Flask Application Factory"""
import os
import logging
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

db = SQLAlchemy()

def create_app():
    """Create and configure the Flask app."""
    # Load environment variables from .env in dev
    load_dotenv()

    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    # Secret key
    app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'dev-secret')

    # Database config
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///vectorbid.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Logging
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=getattr(logging, log_level))
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

    # Initialise extensions
    db.init_app(app)

    with app.app_context():
        db.create_all()

    # Register blueprints
    from routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
