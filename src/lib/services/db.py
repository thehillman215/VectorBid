"""Enhanced database service for user profile management."""

from typing import Dict, Any, Optional
from replit import db
from datetime import datetime, date
import json

PROFILE_KEY = "user:{uid}:profile"

DEFAULT_PROFILE = {
    "name": None,
    "email": None,
    "airline": None,
    "fleet": [],
    "base": None,
    "seat": None,
    "seniority": None,
    # ✨ NEW: Enhanced seniority fields
    "hire_date": None,  # ISO date string
    "years_at_position": None,
    "seniority_percentile": None,
    "last_seniority_update": None,  # ISO datetime string
    # ✨ NEW: Enhanced persona fields
    "persona": None,
    "custom_preferences": None,
    # Profile completion tracking
    "onboard_complete": False,
    "profile_completed": False,  # Legacy compatibility
    "profile_completion_date": None,  # ISO datetime string
    # Future/monetization
    "subscription_tier": "free",
    "referral_code": None,
}


def get_profile(uid: str) -> Dict[str, Any]:
    """Get user profile by user ID.

    Args:
        uid: User ID from Replit authentication

    Returns:
        Profile data dictionary with all fields populated
    """
    profile = db.get(PROFILE_KEY.format(uid=uid), DEFAULT_PROFILE.copy())

    # Ensure backward compatibility and defaults
    for key, default_value in DEFAULT_PROFILE.items():
        if key not in profile:
            profile[key] = default_value

    return profile


def save_profile(uid: str, data: Dict[str, Any]) -> None:
    """Save user profile data.

    Args:
        uid: User ID from Replit authentication
        data: Profile data to save
    """
    profile = get_profile(uid)

    # Handle special data types for JSON storage
    for key, value in data.items():
        if isinstance(value, (date, datetime)):
            # Convert date/datetime to ISO string for JSON storage
            profile[key] = value.isoformat()
        elif key == "fleet" and isinstance(value, list):
            # Ensure fleet is stored as list
            profile[key] = value
        elif key == "fleet" and isinstance(value, str):
            # Handle comma-separated fleet input
            profile[key] = [f.strip() for f in value.split(",") if f.strip()]
        else:
            profile[key] = value

    # Update timestamp
    profile["last_updated"] = datetime.utcnow().isoformat()

    db[PROFILE_KEY.format(uid=uid)] = profile


def get_seniority_analysis(uid: str) -> Optional[Dict[str, Any]]:
    """Get seniority analysis for user.

    Args:
        uid: User ID

    Returns:
        Seniority analysis dictionary or None if insufficient data
    """
    profile = get_profile(uid)

    if not profile.get("seniority") or not profile.get("airline"):
        return None

    return {
        "seniority": profile["seniority"],
        "airline": profile["airline"],
        "percentile": profile.get("seniority_percentile"),
        "last_update": profile.get("last_seniority_update"),
        "category": calculate_seniority_category(
            profile.get("seniority_percentile", 50)
        ),
    }


def calculate_seniority_category(percentile: Optional[float]) -> str:
    """Calculate seniority category from percentile.

    Args:
        percentile: Seniority percentile (0-100)

    Returns:
        Human-readable seniority category
    """
    if not percentile:
        return "Unknown"

    if percentile >= 90:
        return "Very Senior"
    elif percentile >= 75:
        return "Senior"
    elif percentile >= 50:
        return "Mid-Seniority"
    elif percentile >= 25:
        return "Junior"
    else:
        return "Very Junior"


def needs_seniority_update(uid: str) -> bool:
    """Check if seniority analysis needs refresh.

    Args:
        uid: User ID

    Returns:
        True if seniority analysis should be recalculated
    """
    profile = get_profile(uid)

    if not profile.get("last_seniority_update"):
        return True

    try:
        last_update = datetime.fromisoformat(profile["last_seniority_update"])
        # Update if older than 30 days
        return (datetime.utcnow() - last_update).days > 30
    except (ValueError, TypeError):
        return True


def update_seniority_analysis(
    uid: str, percentile: float, category: str = None
) -> None:
    """Update seniority analysis for user.

    Args:
        uid: User ID
        percentile: Calculated seniority percentile
        category: Optional seniority category (will be calculated if not provided)
    """
    if category is None:
        category = calculate_seniority_category(percentile)

    save_profile(
        uid,
        {
            "seniority_percentile": percentile,
            "seniority_category": category,
            "last_seniority_update": datetime.utcnow(),
        },
    )


def get_all_profiles() -> Dict[str, Dict[str, Any]]:
    """Get all user profiles (for admin/debugging).

    Returns:
        Dictionary mapping user IDs to their profiles
    """
    profiles = {}
    for key in db.keys():
        if key.startswith("user:") and key.endswith(":profile"):
            uid = key.split(":")[1]  # Extract UID from key
            profiles[uid] = db[key]

    return profiles


def validate_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Validate profile data and return validation results.

    Args:
        profile: Profile dictionary to validate

    Returns:
        Dictionary with validation results
    """
    errors = []
    warnings = []

    # Required fields for complete profile
    required_fields = ["airline", "base", "seat", "seniority"]
    for field in required_fields:
        if not profile.get(field):
            errors.append(f"Missing required field: {field}")

    # Validate seniority range
    seniority = profile.get("seniority")
    if seniority and (seniority < 1 or seniority > 20000):
        warnings.append("Seniority number seems unusual (should be 1-20000)")

    # Validate seat position
    seat = profile.get("seat")
    if seat and seat not in ["CA", "FO"]:
        errors.append("Seat must be 'CA' (Captain) or 'FO' (First Officer)")

    # Validate fleet
    fleet = profile.get("fleet", [])
    if fleet and not isinstance(fleet, list):
        warnings.append("Fleet should be a list of aircraft types")

    return {
        "valid": len(errors) == 0,
        "complete": len(errors) == 0 and profile.get("onboard_complete", False),
        "errors": errors,
        "warnings": warnings,
    }


def migrate_existing_profiles():
    """Migrate existing profiles to new enhanced schema.

    Returns:
        Number of profiles migrated
    """
    print("🔄 Migrating existing Replit DB profiles...")

    # Get all profile keys
    profile_keys = [
        key for key in db.keys() if key.startswith("user:") and key.endswith(":profile")
    ]

    migrated = 0
    for key in profile_keys:
        try:
            profile = db[key]

            # Add new fields with defaults if missing
            updated = False
            for field, default in DEFAULT_PROFILE.items():
                if field not in profile:
                    profile[field] = default
                    updated = True

            # Handle legacy data transformations
            if updated:
                # Ensure fleet is a list
                if isinstance(profile.get("fleet"), str):
                    profile["fleet"] = [
                        f.strip() for f in profile["fleet"].split(",") if f.strip()
                    ]

                # Add migration timestamp
                profile["migrated_at"] = datetime.utcnow().isoformat()

                db[key] = profile
                migrated += 1

                uid = key.split(":")[1]
                print(f"✅ Migrated profile for user: {uid}")
            else:
                uid = key.split(":")[1]
                print(f"⏭️  Profile already up-to-date for user: {uid}")

        except Exception as e:
            print(f"❌ Error migrating {key}: {e}")

    print(f"🎉 Migration complete! Updated {migrated} profiles.")
    return migrated


def export_profiles(filename: str = "profile_backup.json") -> int:
    """Export all profiles to JSON file for backup.

    Args:
        filename: Name of backup file

    Returns:
        Number of profiles exported
    """
    profiles = get_all_profiles()

    with open(filename, "w") as f:
        json.dump(profiles, f, indent=2, default=str)

    print(f"📁 Exported {len(profiles)} profiles to {filename}")
    return len(profiles)


def import_profiles(filename: str = "profile_backup.json") -> int:
    """Import profiles from JSON backup file.

    Args:
        filename: Name of backup file to import

    Returns:
        Number of profiles imported
    """
    try:
        with open(filename, "r") as f:
            profiles = json.load(f)

        imported = 0
        for uid, profile_data in profiles.items():
            save_profile(uid, profile_data)
            imported += 1

        print(f"📥 Imported {imported} profiles from {filename}")
        return imported

    except FileNotFoundError:
        print(f"❌ Backup file {filename} not found")
        return 0
    except Exception as e:
        print(f"❌ Error importing profiles: {e}")
        return 0


# Backwards compatibility functions
def get_user_profile(uid: str) -> Dict[str, Any]:
    """Legacy function name - use get_profile instead."""
    return get_profile(uid)


def save_user_profile(uid: str, data: Dict[str, Any]) -> None:
    """Legacy function name - use save_profile instead."""
    return save_profile(uid, data)


if __name__ == "__main__":
    # Run migration if this file is executed directly
    print("🚀 Running Replit DB Profile Migration")
    migrate_existing_profiles()
