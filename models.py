"""
Simplified database models for VectorBid.
Consolidates User profile data and streamlines the overall schema.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json
from typing import List, Dict, Optional

# Import the shared db instance
from app import db


class User(UserMixin, db.Model):
    """
    Consolidated user model that includes both authentication and pilot profile data.
    Replaces the separate User + UserProfile pattern for simplicity.
    """
    __tablename__ = 'users'

    # Authentication fields (required for Replit Auth)
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    profile_image_url = db.Column(db.String(255), nullable=True)

    # Pilot-specific profile data (consolidated from UserProfile)
    airline = db.Column(db.String(50), nullable=True)
    base = db.Column(db.String(10), nullable=True)  # Home base airport code
    equipment = db.Column(
        db.String(50),
        nullable=True)  # Aircraft type(s) - JSON string for multiple
    seat = db.Column(db.String(10),
                     nullable=True)  # "CA" (Captain) or "FO" (First Officer)
    seniority = db.Column(db.Integer, nullable=True)  # Seniority number

    # User preferences and onboarding
    persona = db.Column(
        db.String(50),
        nullable=True)  # "Senior Maximizer", "Family First", etc.
    custom_preferences = db.Column(db.Text,
                                   nullable=True)  # Free-form preference text
    onboard_complete = db.Column(db.Boolean, nullable=False, default=False)

    # Timestamps
    created_at = db.Column(db.DateTime,
                           default=datetime.utcnow,
                           nullable=False)
    updated_at = db.Column(db.DateTime,
                           default=datetime.utcnow,
                           onupdate=datetime.utcnow,
                           nullable=False)

    # Relationships
    bid_analyses = db.relationship('BidAnalysis',
                                   backref='user',
                                   lazy=True,
                                   cascade='all, delete-orphan')

    def __repr__(self):
        return f"<User {self.id} ({self.email or 'No email'}, {self.airline or 'No airline'})>"

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.email or self.id

    @property
    def display_name(self) -> str:
        """Get display name for UI."""
        return self.first_name or self.email or self.id

    def get_equipment_list(self) -> List[str]:
        """Get list of aircraft equipment types."""
        if not self.equipment:
            return []
        try:
            if self.equipment.startswith('['):
                return json.loads(self.equipment)
            else:
                return [self.equipment]  # Single equipment string
        except (json.JSONDecodeError, TypeError):
            return [self.equipment] if self.equipment else []

    def set_equipment_list(self, equipment_list: List[str]) -> None:
        """Set aircraft equipment types from list."""
        if not equipment_list:
            self.equipment = None
        elif len(equipment_list) == 1:
            self.equipment = equipment_list[0]
        else:
            self.equipment = json.dumps(equipment_list)

    def is_profile_complete(self) -> bool:
        """Check if user has completed minimum profile requirements."""
        required_fields = [self.airline, self.base, self.seat]
        return all(field is not None for field in required_fields)


class BidAnalysis(db.Model):
    """
    Stores the results of a bid analysis session.
    Replaces the old ScheduleData model with clearer naming.
    """
    __tablename__ = 'bid_analyses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)

    # Analysis input data
    filename = db.Column(db.String(255), nullable=False)
    preferences = db.Column(db.Text, nullable=False)

    # Analysis results (stored as JSON)
    trips_data = db.Column(db.Text, nullable=False)  # Raw parsed trip data
    ranking_results = db.Column(db.Text, nullable=False)  # AI ranking results

    # Metadata
    created_at = db.Column(db.DateTime,
                           default=datetime.utcnow,
                           nullable=False)

    def __repr__(self):
        return f"<BidAnalysis {self.id} for {self.user_id} ({self.filename})>"

    def get_trips_data(self) -> List[Dict]:
        """Get parsed trip data as Python objects."""
        if not self.trips_data:
            return []
        try:
            return json.loads(self.trips_data)
        except (json.JSONDecodeError, TypeError):
            return []

    def set_trips_data(self, data: List[Dict]) -> None:
        """Set trip data from Python objects."""
        self.trips_data = json.dumps(data) if data else "[]"

    def get_ranking_results(self) -> List[Dict]:
        """Get AI ranking results as Python objects."""
        if not self.ranking_results:
            return []
        try:
            return json.loads(self.ranking_results)
        except (json.JSONDecodeError, TypeError):
            return []

    def set_ranking_results(self, results: List[Dict]) -> None:
        """Set ranking results from Python objects."""
        self.ranking_results = json.dumps(results) if results else "[]"

    @property
    def trip_count(self) -> int:
        """Get number of trips in this analysis."""
        return len(self.get_trips_data())

    @property
    def top_trips(self) -> List[Dict]:
        """Get top 5 ranked trips."""
        rankings = self.get_ranking_results()
        return rankings[:5] if rankings else []


class BidPacket(db.Model):
    """
    Stores monthly bid packet PDFs uploaded by administrators.
    Used to provide current month's trips to pilots.
    """
    __tablename__ = 'bid_packets'

    id = db.Column(db.Integer, primary_key=True)
    month_tag = db.Column(db.String(6), unique=True,
                          nullable=False)  # YYYYMM format
    filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # Size in bytes
    content_type = db.Column(db.String(100),
                             nullable=False,
                             default='application/pdf')
    pdf_data = db.Column(db.LargeBinary, nullable=False)  # PDF content
    uploaded_at = db.Column(db.DateTime,
                            default=datetime.utcnow,
                            nullable=False)

    def __repr__(self):
        return f"<BidPacket {self.month_tag} ({self.file_size} bytes)>"

    @property
    def month_display(self) -> str:
        """Get human-readable month display."""
        if len(self.month_tag) == 6:
            year = self.month_tag[:4]
            month = self.month_tag[4:]
            months = {
                '01': 'January',
                '02': 'February',
                '03': 'March',
                '04': 'April',
                '05': 'May',
                '06': 'June',
                '07': 'July',
                '08': 'August',
                '09': 'September',
                '10': 'October',
                '11': 'November',
                '12': 'December'
            }
            return f"{months.get(month, month)} {year}"
        return self.month_tag

    @property
    def file_size_mb(self) -> float:
        """Get file size in MB."""
        return round(self.file_size / (1024 * 1024), 2)


# Keep OAuth model for Replit Auth compatibility (required)
class OAuth(db.Model):
    """
    OAuth token storage for Replit Auth - DO NOT MODIFY.
    This table is required for Replit Auth integration.
    """
    __tablename__ = 'oauth'

    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    browser_session_key = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime,
                           default=datetime.utcnow,
                           nullable=False)

    # Relationships
    user = db.relationship('User', backref='oauth_tokens')

    __table_args__ = (db.UniqueConstraint(
        'user_id',
        'browser_session_key',
        'provider',
        name='uq_user_browser_session_provider'), )


# Database initialization function
def init_db(app):
    """Initialize database tables."""
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")


# Migration helper functions
def migrate_user_profiles():
    """
    Migration function to move data from UserProfile to User model.
    Run this once after deploying the new schema.
    """
    # This would be used if you have existing UserProfile data to migrate
    pass


if __name__ == '__main__':
    # Quick test of the models
    print("VectorBid Models Module")
    print("======================")
    print(f"User: {User.__doc__}")
    print(f"BidAnalysis: {BidAnalysis.__doc__}")
    print(f"BidPacket: {BidPacket.__doc__}")
