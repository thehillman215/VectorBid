# extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager  # optional but convenient

db = SQLAlchemy()  # the ONE shared SQLAlchemy object
login_manager = LoginManager()
