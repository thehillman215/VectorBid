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

    # Relationships to settings models
    security_settings = db.relationship(
        "SecuritySettings", back_populates="user", uselist=False
    )
    communication_preferences = db.relationship(
        "CommunicationPreference", back_populates="user", uselist=False
    )
    career_preferences = db.relationship(
        "CareerPreference", back_populates="user", uselist=False
    )
    subscriptions = db.relationship("Subscription", back_populates="user")
    billing_history = db.relationship("BillingRecord", back_populates="user")


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
        db.UniqueConstraint("month_tag", "airline", name="uix_bid_packets_month_tag_airline"),
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


class SecuritySettings(db.Model):
    __tablename__ = "security_settings"

    user_id = db.Column(db.String, db.ForeignKey("users.id"), primary_key=True)
    two_factor_enabled = db.Column(db.Boolean, default=False, nullable=False)
    last_password_change = db.Column(db.DateTime)

    user = db.relationship("User", back_populates="security_settings")


class CommunicationPreference(db.Model):
    __tablename__ = "communication_preferences"

    user_id = db.Column(db.String, db.ForeignKey("users.id"), primary_key=True)
    email_opt_in = db.Column(db.Boolean, default=True, nullable=False)
    sms_opt_in = db.Column(db.Boolean, default=False, nullable=False)
    preferred_language = db.Column(db.String(10))

    user = db.relationship("User", back_populates="communication_preferences")


class CareerPreference(db.Model):
    __tablename__ = "career_preferences"

    user_id = db.Column(db.String, db.ForeignKey("users.id"), primary_key=True)
    desired_base = db.Column(db.String(50))
    desired_aircraft = db.Column(db.String(50))
    long_term_goal = db.Column(db.String(255))

    user = db.relationship("User", back_populates="career_preferences")


class Subscription(db.Model):
    __tablename__ = "subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)
    plan = db.Column(db.String(50))
    status = db.Column(db.String(20))
    renew_at = db.Column(db.DateTime)

    user = db.relationship("User", back_populates="subscriptions")


class BillingRecord(db.Model):
    __tablename__ = "billing_records"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Numeric(10, 2))
    description = db.Column(db.String(255))
    billed_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="billing_history")
