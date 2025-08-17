"""
Preset-based airport scoring for different pilot personas.
Quick implementation before full customizable system.
"""


def get_pilot_persona_airport_weights(persona):
    """Get airport weights based on pilot persona."""

    presets = {
        "credit_hunter": {
            # Higher weights for premium-paying routes
            "LHR": 35,
            "FRA": 35,
            "CDG": 30,
            "AMS": 30,
            "NRT": 40,
            "ICN": 40,
            "HKG": 35,
            "SIN": 35,
            "MUC": 25,
            "ZUR": 25,
            "BOM": 30,
            "DEL": 30,
        },
        "family_friendly": {
            # Shorter time zones, easier adjustments
            "LHR": 30,
            "FRA": 25,
            "CDG": 25,
            "AMS": 20,
            "NRT": 15,
            "ICN": 15,
            "HKG": 10,
            "SIN": 10,
            "MUC": 20,
            "ZUR": 20,
            "BOM": 5,
            "DEL": 5,
        },
        "adventure_seeker": {
            # Exotic destinations, interesting layovers
            "LHR": 20,
            "FRA": 20,
            "CDG": 25,
            "AMS": 25,
            "NRT": 40,
            "ICN": 35,
            "HKG": 40,
            "SIN": 40,
            "MUC": 30,
            "ZUR": 30,
            "BOM": 45,
            "DEL": 40,
        },
        "commuter": {
            # Shorter flights, easier connections
            "LHR": 40,
            "FRA": 35,
            "CDG": 30,
            "AMS": 35,
            "NRT": 10,
            "ICN": 10,
            "HKG": 15,
            "SIN": 15,
            "MUC": 25,
            "ZUR": 20,
            "BOM": 5,
            "DEL": 5,
        },
        "work_life_balance": {
            # Balanced approach, reasonable destinations
            "LHR": 25,
            "FRA": 25,
            "CDG": 20,
            "AMS": 20,
            "NRT": 20,
            "ICN": 20,
            "HKG": 18,
            "SIN": 18,
            "MUC": 15,
            "ZUR": 15,
            "BOM": 12,
            "DEL": 12,
        },
    }

    return presets.get(persona, presets["work_life_balance"])


def enhanced_international_scoring_with_persona(
    trip, preferences_lower, pilot_persona="work_life_balance"
):
    """Enhanced scoring using pilot persona presets."""

    routing = trip.get("routing", "").upper()
    score_boost = 0
    key_factors = []
    reasoning_parts = []

    # Get persona-based weights
    persona_weights = get_pilot_persona_airport_weights(pilot_persona)

    found_destinations = []
    total_boost = 0

    # Check each airport in routing against persona weights
    for airport_code, weight in persona_weights.items():
        if airport_code in routing:
            found_destinations.append(airport_code)
            total_boost += weight
            key_factors.append(f"{pilot_persona}_{airport_code.lower()}")

    # Apply boost if international preference detected
    if "international" in preferences_lower and found_destinations:
        score_boost = total_boost

        # Add reasoning based on persona
        if pilot_persona == "credit_hunter":
            reasoning_parts.append(
                f"Premium high-credit routes to {', '.join(found_destinations)}"
            )
        elif pilot_persona == "family_friendly":
            reasoning_parts.append(
                f"Family-friendly time zones to {', '.join(found_destinations)}"
            )
        elif pilot_persona == "adventure_seeker":
            reasoning_parts.append(
                f"Exciting destinations to {', '.join(found_destinations)}"
            )
        elif pilot_persona == "commuter":
            reasoning_parts.append(
                f"Commuter-friendly routes to {', '.join(found_destinations)}"
            )
        else:
            reasoning_parts.append(
                f"International routes to {', '.join(found_destinations)}"
            )

    return score_boost, key_factors, reasoning_parts


def test_persona_scoring():
    """Test different personas with same trips."""

    test_trips = [
        {"trip_id": "UA002", "routing": "DEN-LHR-FRA-DEN"},  # European
        {"trip_id": "UA004", "routing": "DEN-NRT-ICN-DEN"},  # Asian
        {"trip_id": "UA006", "routing": "DEN-BOM-DEL-DEN"},  # Indian (exotic)
    ]

    personas = ["credit_hunter", "family_friendly", "adventure_seeker", "commuter"]
    preferences = "I love international flying and interesting destinations"

    print("🧪 Persona-Based Airport Scoring Test")
    print("=" * 60)

    for persona in personas:
        print(f"\n👤 {persona.upper().replace('_', ' ')} PERSONA:")
        print("-" * 30)

        results = []
        for trip in test_trips:
            boost, factors, reasoning = enhanced_international_scoring_with_persona(
                trip, preferences.lower(), persona
            )
            results.append((trip["trip_id"], trip["routing"], boost, reasoning))

        # Sort by boost
        results.sort(key=lambda x: x[2], reverse=True)

        for trip_id, routing, boost, reasoning in results:
            reasoning_str = (
                "; ".join(reasoning) if reasoning else "no international preference"
            )
            print(f"  {trip_id} (+{boost:2d}): {reasoning_str}")


if __name__ == "__main__":
    test_persona_scoring()
