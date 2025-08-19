"""Tests for database models and their relationships."""

import pytest
from src.core.models import (
    User, SecuritySettings, CommunicationPreference, 
    CareerPreference, Subscription, BillingRecord
)


def test_user_creation(db_session):
    """Test creating a user with basic fields."""
    user = User(
        id="test_user_456",
        email="pilot@example.com",
        name="John Pilot",
        airline="UAL",
        base="ORD",
        role="pilot"
    )
    
    db_session.add(user)
    db_session.commit()
    
    assert user.id == "test_user_456"
    assert user.email == "pilot@example.com"
    assert user.airline == "UAL"
    assert user.base == "ORD"
    assert user.role == "pilot"


def test_user_security_settings_relationship(db_session, sample_user):
    """Test the relationship between User and SecuritySettings."""
    # Create security settings
    security = SecuritySettings(
        user_id=sample_user.id,
        two_factor_enabled=True
    )
    
    db_session.add(security)
    db_session.commit()
    
    # Test relationship
    assert sample_user.security_settings is not None
    assert sample_user.security_settings.two_factor_enabled is True
    assert sample_user.security_settings.user_id == sample_user.id


def test_user_communication_preferences_relationship(db_session, sample_user):
    """Test the relationship between User and CommunicationPreference."""
    comm_prefs = CommunicationPreference(
        user_id=sample_user.id,
        email_opt_in=True,
        sms_opt_in=False,
        preferred_language="en"
    )
    
    db_session.add(comm_prefs)
    db_session.commit()
    
    # Test relationship
    assert sample_user.communication_preferences is not None
    assert sample_user.communication_preferences.email_opt_in is True
    assert sample_user.communication_preferences.sms_opt_in is False
    assert sample_user.communication_preferences.preferred_language == "en"


def test_user_career_preferences_relationship(db_session, sample_user):
    """Test the relationship between User and CareerPreference."""
    career_prefs = CareerPreference(
        user_id=sample_user.id,
        desired_base="LAX",
        desired_aircraft="B737",
        long_term_goal="Captain"
    )
    
    db_session.add(career_prefs)
    db_session.commit()
    
    # Test relationship
    assert sample_user.career_preferences is not None
    assert sample_user.career_preferences.desired_base == "LAX"
    assert sample_user.career_preferences.desired_aircraft == "B737"
    assert sample_user.career_preferences.long_term_goal == "Captain"


def test_user_subscriptions_relationship(db_session, sample_user):
    """Test the relationship between User and Subscription."""
    subscription = Subscription(
        user_id=sample_user.id,
        plan="premium",
        status="active"
    )
    
    db_session.add(subscription)
    db_session.commit()
    
    # Test relationship
    assert len(sample_user.subscriptions) == 1
    assert sample_user.subscriptions[0].plan == "premium"
    assert sample_user.subscriptions[0].status == "active"


def test_user_billing_history_relationship(db_session, sample_user):
    """Test the relationship between User and BillingRecord."""
    billing_record = BillingRecord(
        user_id=sample_user.id,
        amount=99.99,
        description="Premium Plan Monthly"
    )
    
    db_session.add(billing_record)
    db_session.commit()
    
    # Test relationship
    assert len(sample_user.billing_history) == 1
    assert float(sample_user.billing_history[0].amount) == 99.99
    assert sample_user.billing_history[0].description == "Premium Plan Monthly"


def test_security_settings_page_mapping(db_session, sample_user):
    """Test that security settings model maps to security settings page."""
    # This test ensures the database model supports all fields needed by the security settings page
    security = SecuritySettings(
        user_id=sample_user.id,
        two_factor_enabled=True
    )
    
    db_session.add(security)
    db_session.commit()
    
    # Verify all fields that the security settings page needs are present
    assert hasattr(security, 'user_id')
    assert hasattr(security, 'two_factor_enabled')
    assert hasattr(security, 'last_password_change')
    
    # Test that we can update settings (simulating form submission)
    security.two_factor_enabled = False
    db_session.commit()
    
    # Verify the change persisted
    db_session.refresh(security)
    assert security.two_factor_enabled is False


def test_communication_preferences_page_mapping(db_session, sample_user):
    """Test that communication preferences model maps to communication settings page."""
    comm_prefs = CommunicationPreference(
        user_id=sample_user.id,
        email_opt_in=True,
        sms_opt_in=False,
        preferred_language="en"
    )
    
    db_session.add(comm_prefs)
    db_session.commit()
    
    # Verify all fields that the communication settings page needs are present
    assert hasattr(comm_prefs, 'user_id')
    assert hasattr(comm_prefs, 'email_opt_in')
    assert hasattr(comm_prefs, 'sms_opt_in')
    assert hasattr(comm_prefs, 'preferred_language')
    
    # Test updating preferences (simulating form submission)
    comm_prefs.sms_opt_in = True
    comm_prefs.preferred_language = "es"
    db_session.commit()
    
    # Verify changes persisted
    db_session.refresh(comm_prefs)
    assert comm_prefs.sms_opt_in is True
    assert comm_prefs.preferred_language == "es"


def test_career_preferences_page_mapping(db_session, sample_user):
    """Test that career preferences model maps to career settings page."""
    career_prefs = CareerPreference(
        user_id=sample_user.id,
        desired_base="LAX",
        desired_aircraft="B737",
        long_term_goal="Captain"
    )
    
    db_session.add(career_prefs)
    db_session.commit()
    
    # Verify all fields that the career settings page needs are present
    assert hasattr(career_prefs, 'user_id')
    assert hasattr(career_prefs, 'desired_base')
    assert hasattr(career_prefs, 'desired_aircraft')
    assert hasattr(career_prefs, 'long_term_goal')
    
    # Test updating preferences (simulating form submission)
    career_prefs.desired_base = "JFK"
    career_prefs.long_term_goal = "Training Captain"
    db_session.commit()
    
    # Verify changes persisted
    db_session.refresh(career_prefs)
    assert career_prefs.desired_base == "JFK"
    assert career_prefs.long_term_goal == "Training Captain"
