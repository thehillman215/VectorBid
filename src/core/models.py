"""
Database models for VectorBid
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    name = db.Column(db.String(100))
    airline = db.Column(db.String(50))
    base = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime)

class BidPacket(db.Model):
    __tablename__ = 'bid_packets'

    id = db.Column(db.Integer, primary_key=True)
    month_tag = db.Column(db.String(6), unique=True)
    filename = db.Column(db.String(255))
    file_data = db.Column(db.LargeBinary)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

class BidAnalysis(db.Model):
    __tablename__ = 'bid_analyses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'))
    preferences = db.Column(db.Text)
    commands = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
