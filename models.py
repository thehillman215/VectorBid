from extensions import db  # ✅ import the already-created SQLAlchemy object
from datetime import datetime
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint


# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=True)
    first_name = db.Column(db.String, nullable=True)
    last_name = db.Column(db.String, nullable=True)
    profile_image_url = db.Column(db.String, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.String, db.ForeignKey(User.id))
    browser_session_key = db.Column(db.String, nullable=False)
    user = db.relationship(User)

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "browser_session_key",
            "provider",
            name="uq_user_browser_session_key_provider",
        ),
    )


class ScheduleData(db.Model):
    __tablename__ = "schedule_data"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey(User.id), nullable=False)
    filename = db.Column(db.String, nullable=False)
    preferences = db.Column(db.Text, nullable=False)
    trips_data = db.Column(db.Text, nullable=False)  # JSON string
    ranking_results = db.Column(db.Text, nullable=False)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.now)

    user = db.relationship(User, backref="schedules")


class BidPacket(db.Model):
    __tablename__ = "bid_packets"
    id = db.Column(db.Integer, primary_key=True)
    month_tag = db.Column(db.String(6), unique=True, nullable=False)  # YYYYMM format
    filename = db.Column(db.String, nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # size in bytes
    content_type = db.Column(db.String, nullable=False, default="application/pdf")
    pdf_data = db.Column(db.LargeBinary, nullable=False)  # bytea column for PDF content
    uploaded_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    def __repr__(self):
        return f"<BidPacket {self.month_tag} ({self.file_size} bytes)>"


class UserProfile(db.Model):
    __tablename__ = "user_profiles"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey(User.id), nullable=False, unique=True)
    airline = db.Column(db.String, nullable=True)
    fleet = db.Column(db.Text, nullable=True)  # JSON string for list of aircraft types
    seat = db.Column(db.String(2), nullable=True)  # "CA" or "FO"
    base = db.Column(db.String, nullable=True)  # Home base airport code
    seniority = db.Column(db.Integer, nullable=True)  # Seniority number
    profile_completed = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    user = db.relationship(User, backref="profile")

    def __repr__(self):
        return f"<UserProfile {self.user_id} ({self.airline or 'No airline'}, {self.seat or 'No seat'})>"
