"""
Database models for VectorBid
"""

from datetime import datetime

from src.core.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    name = db.Column(db.String(100))
    airline = db.Column(db.String(50))
    base = db.Column(db.String(50))
    role = db.Column(db.String(20), default="user")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime)


class BidPacket(db.Model):
    __tablename__ = "bid_packets"

    id = db.Column(db.Integer, primary_key=True)
    month_tag = db.Column(db.String(6))
    airline = db.Column(db.String(50), nullable=False)
    filename = db.Column(db.String(255))
    airline = db.Column(db.String(50))
    pdf_data = db.Column(db.LargeBinary)
    file_size = db.Column(db.Integer)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint(
            "month_tag", "airline", name="uix_bid_packets_month_tag_airline"
        ),
    )


class BidAnalysis(db.Model):
    __tablename__ = "bid_analyses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey("users.id"))
    preferences = db.Column(db.Text)
    commands = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AdminActionLog(db.Model):
    """Audit log of admin actions"""

    __tablename__ = "admin_action_logs"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    admin_id = db.Column(db.String(120))
    action = db.Column(db.String(50), nullable=False)
    target = db.Column(db.String(255))
