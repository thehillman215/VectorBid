"""
Quick integration helper for persona-based scoring.
"""


def detect_pilot_persona_from_preferences(preferences):
    """Detect pilot persona from preference text."""
    prefs_lower = preferences.lower()

    # Check for explicit persona keywords
    if any(
        word in prefs_lower for word in ["credit", "hours", "pay", "maximize", "money"]
    ):
        return "credit_hunter"
    elif any(
        word in prefs_lower
        for word in ["family", "home", "balance", "weekend", "time off"]
    ):
        return "family_friendly"
    elif any(
        word in prefs_lower
        for word in ["adventure", "variety", "interesting", "exotic", "new"]
    ):
        return "adventure_seeker"
    elif any(
        word in prefs_lower
        for word in ["commute", "commuter", "short", "quick", "efficient"]
    ):
        return "commuter"
    else:
        return "work_life_balance"  # Default


# Test persona detection
if __name__ == "__main__":
    test_prefs = [
        "I want to maximize credit hours and pay",
        "I prioritize family time and work-life balance",
        "I love adventure and interesting destinations",
        "I'm a commuter pilot who wants efficient trips",
        "I want reasonable schedules and good routes",
    ]

    print("🧪 Persona Detection Test")
    print("=" * 40)
    for prefs in test_prefs:
        persona = detect_pilot_persona_from_preferences(prefs)
        print(f"'{prefs[:30]}...' → {persona}")
