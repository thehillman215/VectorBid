import os
import sys
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# ---------------------------------------------------------------------------
# Extensions
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    """Base class for SQL-Alchemy models (needed for v3.x)."""
    pass


# Create the shared SQLAlchemy instance *once* so every module can import it
# via ``from extensions import db``.
db = SQLAlchemy(model_class=Base)

try:
    from flask_login import LoginManager
    login_manager = LoginManager()
except ModuleNotFoundError:
    # If login support is optional, fall back gracefully
    login_manager = None

# Make *this* module importable as ``extensions`` to satisfy existing imports
sys.modules.setdefault("extensions", sys.modules[__name__])

# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def create_app() -> Flask:
    """Application-factory so other modules can import without side-effects."""

    app = Flask(__name__)

    # ---------- Config ------------------------------------------------------
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///site.db")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }

    # ---------- Middleware & Logging ----------------------------------------
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
    logging.basicConfig(level=logging.DEBUG)

    # ---------- Initialise extensions --------------------------------------
    db.init_app(app)
    if login_manager:
        login_manager.init_app(app)
        login_manager.login_view = 'replit_auth.login'  # type: ignore
        
        # User loader function
        @login_manager.user_loader
        def load_user(user_id):
            from models import User
            return User.query.get(user_id)

    # ---------- Database tables --------------------------------------------
    with app.app_context():
        import models  # noqa: F401 – side-effect: define tables
        db.create_all()

    # ---------- Blueprints --------------------------------------------------
    try:
        from routes import bp as main_bp
        app.register_blueprint(main_bp)
    except ModuleNotFoundError:
        logging.warning("routes blueprint not found; skipping")

    try:
        from replit_auth import make_replit_blueprint
        app.register_blueprint(make_replit_blueprint())
    except ModuleNotFoundError:
        logging.info("replit_auth not configured; skipping auth blueprint")

    return app


# ---------------------------------------------------------------------------
# CLI entry-point (``python app.py``) ---------------------------------------
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    application = create_app()
    application.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        debug=True,
    )
