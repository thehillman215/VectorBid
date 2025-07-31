"""Database service for user profile management."""

import json
from typing import Dict, Any, Optional, List
from extensions import db
from models import UserProfile


def get_profile(uid: str) -> Dict[str, Any]:
    """Get user profile by user ID.
    
    Args:
        uid: User ID from Replit authentication
        
    Returns:
        Profile data dictionary with default values if not found
    """
    profile = UserProfile.query.filter_by(user_id=uid).first()
    
    if not profile:
        # Return default profile structure
        return {
            "airline": None,
            "fleet": [],
            "seat": None,
            "base": None,
            "seniority": None,
            "profile_completed": False
        }
    
    # Parse fleet data from JSON
    fleet_data = []
    if profile.fleet:
        try:
            fleet_data = json.loads(profile.fleet)
        except json.JSONDecodeError:
            fleet_data = []
    
    return {
        "airline": profile.airline,
        "fleet": fleet_data,
        "seat": profile.seat,
        "base": profile.base,
        "seniority": profile.seniority,
        "persona": profile.persona,
        "custom_preferences": profile.custom_preferences,
        "profile_completed": profile.profile_completed
    }


def save_profile(uid: str, data: Dict[str, Any]) -> bool:
    """Save user profile data.
    
    Args:
        uid: User ID from Replit authentication
        data: Profile data dictionary
        
    Returns:
        True if save was successful, False otherwise
    """
    try:
        profile = UserProfile.query.filter_by(user_id=uid).first()
        
        if not profile:
            profile = UserProfile()
            profile.user_id = uid
            db.session.add(profile)
        
        # Update profile fields
        profile.airline = data.get("airline")
        profile.seat = data.get("seat")
        profile.base = data.get("base")
        profile.seniority = data.get("seniority")
        profile.persona = data.get("persona")
        profile.custom_preferences = data.get("custom_preferences")
        profile.profile_completed = data.get("profile_completed", False)
        
        # Handle fleet data as JSON
        fleet_data = data.get("fleet", [])
        if isinstance(fleet_data, list):
            profile.fleet = json.dumps(fleet_data)
        else:
            profile.fleet = json.dumps([])
        
        db.session.commit()
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"Error saving profile: {e}")
        return False