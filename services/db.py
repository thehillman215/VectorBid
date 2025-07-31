"""Database service for user profile management."""

from typing import Dict, Any
from replit import db
from datetime import date

PROFILE_KEY = "user:{uid}:profile"

DEFAULT_PROFILE = {
    "name": None,
    "email": None,
    "airline": None,         # e.g. "United"
    "fleet": [],             # list[str]  → ["737", "320"]
    "base": None,            # e.g. "IAH"
    "seat": None,            # "CA" | "FO"
    "seniority": None,       # int
    "seniority_last_updated": None,  # iso date str
    # ✨ future / monetization
    "subscription_tier": "free",     # free | pro | enterprise
    "referral_code": None,
    "onboard_complete": False,
    # Legacy compatibility
    "persona": None,
    "custom_preferences": None,
    "profile_completed": False
}


def get_profile(uid: str) -> Dict[str, Any]:
    """Get user profile by user ID.
    
    Args:
        uid: User ID from Replit authentication
        
    Returns:
        Profile data dictionary with default values if not found
    """
    return db.get(PROFILE_KEY.format(uid=uid), DEFAULT_PROFILE.copy())


def save_profile(uid: str, data: Dict[str, Any]) -> None:
    """Save user profile data.
    
    Args:
        uid: User ID from Replit authentication
        data: Profile data to save
    """
    profile = get_profile(uid)
    profile.update(data)
    db[PROFILE_KEY.format(uid=uid)] = profile