"""
Enhanced international route scoring for VectorBid United Airlines system.
Integrates with existing llm_service.py fallback scoring.
"""


def enhanced_international_scoring(trip, preferences_lower):
    """
    Enhanced scoring for international route preferences.

    Args:
        trip: Trip dictionary with routing information
        preferences_lower: User preferences in lowercase

    Returns:
        tuple: (score_boost, key_factors, reasoning_parts)
    """
    routing = trip.get("routing", "").upper()
    score_boost = 0
    key_factors = []
    reasoning_parts = []

    # Premium international destinations with scoring weights
    premium_international = {
        "LHR": ("London Heathrow", 25),  # Premium European hub
        "FRA": ("Frankfurt", 25),  # Premium European hub
        "CDG": ("Paris CDG", 20),  # Major European hub
        "AMS": ("Amsterdam", 20),  # European hub
        "MUC": ("Munich", 15),  # European destination
        "ZUR": ("Zurich", 15),  # European destination
        "NRT": ("Tokyo Narita", 30),  # Premium Asian hub
        "ICN": ("Seoul Incheon", 30),  # Premium Asian hub
        "HKG": ("Hong Kong", 25),  # Asian hub
        "SIN": ("Singapore", 25),  # Asian hub
        "BOM": ("Mumbai", 20),  # Indian hub
        "DEL": ("Delhi", 20),  # Indian hub
    }

    # European secondary markets
    european_secondary = {
        "MAD": ("Madrid", 12),
        "BCN": ("Barcelona", 10),
        "FCO": ("Rome", 15),
        "MXP": ("Milan", 12),
        "VIE": ("Vienna", 12),
        "BRU": ("Brussels", 12),
        "ARN": ("Stockholm", 10),
        "CPH": ("Copenhagen", 10),
        "OSL": ("Oslo", 10),
        "LIS": ("Lisbon", 10),
        "DUB": ("Dublin", 8),
    }

    # Find international destinations in routing
    found_destinations = []
    total_boost = 0

    # Check premium international
    for code, (city, boost) in premium_international.items():
        if code in routing:
            found_destinations.append(city)
            total_boost += boost
            key_factors.append(f"premium_{code.lower()}")

    # Check European secondary markets
    for code, (city, boost) in european_secondary.items():
        if code in routing:
            found_destinations.append(city)
            total_boost += boost
            key_factors.append(f"european_{code.lower()}")

    # Route pattern bonuses
    if len(found_destinations) > 1:
        total_boost += 10  # Multi-city international bonus
        key_factors.append("multi_city_international")
        reasoning_parts.append("multi-city international route")
    elif len(found_destinations) == 1:
        key_factors.append("international_route")
        reasoning_parts.append("international route")

    # Apply preference-based multipliers
    if found_destinations:  # Only boost if actually international
        # General international preference
        if "international" in preferences_lower:
            score_boost += total_boost
            reasoning_parts.append(f"international flying to {', '.join(found_destinations)}")

        # Specific regional preferences
        if "european" in preferences_lower or "europe" in preferences_lower:
            europe_codes = [
                "LHR",
                "FRA",
                "CDG",
                "AMS",
                "MUC",
                "ZUR",
                "MAD",
                "FCO",
                "VIE",
                "BRU",
                "LIS",
                "DUB",
            ]
            if any(code in routing for code in europe_codes):
                score_boost += 15  # Additional European preference bonus
                key_factors.append("europe_preferred")
                reasoning_parts.append("preferred European destination")

        if "asian" in preferences_lower or "asia" in preferences_lower:
            asia_codes = ["NRT", "ICN", "HKG", "SIN", "BOM", "DEL"]
            if any(code in routing for code in asia_codes):
                score_boost += 15  # Additional Asian preference bonus
                key_factors.append("asia_preferred")
                reasoning_parts.append("preferred Asian destination")

        # Layover quality bonus
        if "layover" in preferences_lower:
            score_boost += 8
            key_factors.append("good_layovers")
            reasoning_parts.append("good international layovers")

        # Destination variety bonus
        if "destination" in preferences_lower or "variety" in preferences_lower:
            score_boost += 5
            key_factors.append("destination_variety")

    return score_boost, key_factors, reasoning_parts


def test_enhanced_scoring():
    """Test function to verify the enhanced scoring works."""

    test_trips = [
        {"trip_id": "UA002", "routing": "DEN-LHR-FRA-DEN"},  # European multi-city
        {"trip_id": "UA004", "routing": "DEN-NRT-ICN-DEN"},  # Asian multi-city
        {"trip_id": "UA001", "routing": "DEN-LAX-SFO-DEN"},  # Domestic multi-city
        {"trip_id": "UA003", "routing": "DEN-PHX-DEN"},  # Domestic simple
        {"trip_id": "UA005", "routing": "DEN-LHR-DEN"},  # European single
    ]

    test_preferences = [
        "I love international flying and interesting destinations",
        "I prefer European routes with good layovers",
        "I want Asian destinations and variety in my flying",
    ]

    print("🧪 Enhanced International Scoring Test")
    print("=" * 60)

    for prefs in test_preferences:
        print(f"\nPreferences: {prefs}")
        print("-" * 40)

        results = []
        for trip in test_trips:
            boost, factors, reasoning = enhanced_international_scoring(trip, prefs.lower())
            results.append((trip["trip_id"], trip["routing"], boost, reasoning))

        # Sort by boost (descending)
        results.sort(key=lambda x: x[2], reverse=True)

        for trip_id, _routing, boost, reasoning in results:
            reasoning_str = "; ".join(reasoning) if reasoning else "domestic route"
            print(f"  {trip_id} (+{boost:2d}): {reasoning_str}")


if __name__ == "__main__":
    test_enhanced_scoring()
