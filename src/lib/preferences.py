# preferences.py
# Create this file in your main project directory (same level as app.py)
"""
VectorBid Flying Style Personas and Preference Management
"""

# Pre-defined Flying Style Personas
FLYING_PERSONAS = {
    "family_first": {
        "name": "Family First",
        "icon": "fas fa-home",
        "description": "Maximize time at home with family and consistent schedule",
        "preferences": """I prioritize family time above all else. I want:
- Maximum consecutive days off (prefer 4+ days together)
- Consistent schedule patterns each month
- Minimal weekend flying (Friday-Sunday)
- Shorter trips when possible (1-3 days max)
- Avoid red-eye flights that disrupt sleep schedule
- Prefer domestic routes for faster commutes home
- Avoid reserve flying - need predictable schedule""",
    },
    "money_maker": {
        "name": "Money Maker",
        "icon": "fas fa-dollar-sign",
        "description": "Maximize pay through high-credit trips and optimal scheduling",
        "preferences": """I want to maximize my monthly earnings. I prefer:
- Highest credit hour trips available
- International flights with higher pay rates
- Longer trips (4-5 days) for efficiency
- Premium destinations with good per diem
- Overtime opportunities when available
- High-value routes and aircraft types
- Willing to work weekends for premium pay""",
    },
    "commuter_friendly": {
        "name": "Commuter Friendly",
        "description": "Optimize for easy commuting with flexible departure times",
        "icon": "fas fa-plane-departure",
        "preferences": """As a commuting pilot, I need schedule flexibility:
- Late report times (after 10 AM) to catch commuter flights
- Trips starting/ending at major hub airports
- Avoid early morning or late night departures
- Prefer longer trips to minimize commute frequency
- Flexible scheduling around airline commute options
- Avoid same-day connections when commuting""",
    },
    "quality_of_life": {
        "name": "Quality of Life",
        "icon": "fas fa-heart",
        "description": "Balance work and personal time with reasonable schedules",
        "preferences": """I seek work-life balance and reasonable schedules:
- Prefer trips with good layovers (12+ hours)
- Avoid back-to-back duty days
- Reasonable report times (not too early/late)
- Interesting destinations when possible
- Avoid excessive duty time or long days
- Prefer variety in routes and experiences
- Moderate credit hours (not maximum, not minimum)""",
    },
    "reserve_avoider": {
        "name": "Reserve Avoider",
        "icon": "fas fa-calendar-check",
        "description": "Prioritize holding a line to avoid reserve duty",
        "preferences": """My top priority is avoiding reserve and holding a line:
- Will take any line over reserve duty
- Flexible on trip types and destinations
- Willing to work weekends to hold a line
- Prefer predictable schedule over ideal trips
- Focus on trips I can reliably hold with my seniority
- Conservative bidding strategy to ensure line holding""",
    },
}


def convert_preferences_to_string(profile):
    """Convert user profile preferences to natural language string for AI processing."""
    if not profile:
        return "Standard pilot preferences - maximize schedule efficiency and quality of life."

    # Check for persona-based preferences
    persona = profile.get("persona")
    if persona and persona in FLYING_PERSONAS:
        base_prefs = FLYING_PERSONAS[persona]["preferences"]

        # Add any custom preferences
        custom = profile.get("custom_preferences", "").strip()
        if custom:
            return f"{base_prefs}\n\nAdditional custom preferences:\n{custom}"
        return base_prefs

    # For custom-only preferences
    custom = profile.get("custom_preferences", "").strip()
    if custom:
        return custom

    # Fallback
    return (
        "Standard pilot preferences - maximize schedule efficiency and quality of life."
    )


def get_preference_summary(profile):
    """Get a human-readable summary of user preferences for display."""
    if not profile:
        return "No preferences set."

    summary_parts = []

    # Persona summary
    persona = profile.get("persona")
    if persona and persona in FLYING_PERSONAS:
        persona_data = FLYING_PERSONAS[persona]
        summary_parts.append(f"Flying Style: {persona_data['name']}")
        summary_parts.append(persona_data["description"])

    # Custom preferences
    custom = profile.get("custom_preferences", "").strip()
    if custom:
        summary_parts.append(f"Custom Requirements: {custom}")

    return "\n".join(summary_parts) if summary_parts else "Standard preferences."


# Test function to verify the module works
def test_preferences():
    """Test function to verify preferences module is working."""
    print("Testing VectorBid Preferences Module")
    print("=" * 50)

    # Test persona access
    for persona_id, persona_data in FLYING_PERSONAS.items():
        print(f"✓ {persona_data['name']}: {persona_data['description']}")

    # Test conversion function
    test_profile = {
        "persona": "family_first",
        "custom_preferences": "I also need Fridays off for family commitments.",
    }

    result = convert_preferences_to_string(test_profile)
    print(f"\nTest conversion result length: {len(result)} characters")
    print("✓ Preferences module working correctly!")

    return True


if __name__ == "__main__":
    test_preferences()
