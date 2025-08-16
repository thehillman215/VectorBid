#!/usr/bin/env python3
"""
VectorBid Quick Test Harness - United Airlines Focus
Run this locally or in Replit console for instant feedback without web server.
"""

import json
import sys
from datetime import datetime

# Sample United Airlines trip data for testing
SAMPLE_UNITED_TRIPS = [
    {
        "trip_id": "UA123",
        "days": 3,
        "credit_hours": 18.5,
        "routing": "DEN-LAX-DEN",
        "dates": "15JAN-17JAN",
        "includes_weekend": False,
        "raw": "UA123 3DAY 15JAN-17JAN DEN-LAX-DEN 18:30"
    },
    {
        "trip_id": "UA456",
        "days": 4,
        "credit_hours": 25.2,
        "routing": "DEN-LHR-FRA-DEN",
        "dates": "20JAN-23JAN",
        "includes_weekend": True,
        "raw": "UA456 4DAY 20JAN-23JAN DEN-LHR-FRA-DEN 25:12 SAT"
    },
    {
        "trip_id": "UA789",
        "days": 2,
        "credit_hours": 12.0,
        "routing": "DEN-PHX-DEN",
        "dates": "25JAN-26JAN",
        "includes_weekend": False,
        "raw": "UA789 2DAY 25JAN-26JAN DEN-PHX-DEN 12:00"
    }
]

# Sample United Airlines bid packet text
SAMPLE_UNITED_TEXT = """UNITED AIRLINES PILOT BID PACKAGE - FEBRUARY 2025
Base: DEN  Equipment: 737  Position: FO

Trip   Days  Routing           Credit  Dates
UA123  3DAY  DEN-LAX-DEN     18:30   15FEB-17FEB
UA456  4DAY  DEN-LHR-FRA-DEN 25:12   20FEB-23FEB SAT
UA789  2DAY  DEN-PHX-DEN     12:00   25FEB-26FEB
UA101  5DAY  DEN-NRT-ICN-DEN 32:15   01MAR-05MAR
UA202  1DAY  DEN-ORD-DEN     06:45   10MAR-10MAR
"""

SAMPLE_PREFERENCES = {
    "work_life_balance": "I want weekends off and shorter trips for family time",
    "credit_hunter": "Maximize credit hours and pay, longer international trips preferred",
    "commuter_friendly": "Prefer trips that start/end at DEN with efficient scheduling"
}

def test_united_parser():
    """Test United Airlines parsing logic."""
    print("🔍 Testing United Airlines Parser...")

    # Test parsing United format lines
    test_lines = [
        "UA123 3DAY 15JAN-17JAN DEN-LAX-DEN 18:30",
        "UA456 4DAY 20JAN-23JAN DEN-LHR-FRA-DEN 25:12 SAT",
        "456 2DAY 25JAN-26JAN DEN-PHX-DEN 12:00",  # No UA prefix
        "UA101 737 5DAY DEN-NRT-ICN-DEN Credit: 32:15"  # With aircraft
    ]

    parsed_trips = []
    for line in test_lines:
        trip = parse_united_line(line)
        if trip:
            parsed_trips.append(trip)
            efficiency = trip['credit_hours'] / trip['days']
            print(f"  ✅ {trip['trip_id']}: {trip['days']}d, {trip['credit_hours']}h ({efficiency:.1f}h/day)")
        else:
            print(f"  ❌ Failed to parse: {line}")

    return parsed_trips

def parse_united_line(line: str) -> dict:
    """Quick United Airlines parser for testing."""
    import re

    # United Airlines patterns (simplified for testing)
    patterns = [
        # Standard: UA123 3DAY 15JAN-17JAN DEN-LAX-DEN 18:30
        re.compile(r'(?P<trip_id>UA\d+)\s+(?P<days>\d+)DAY\s+(?P<dates>\S+)\s+(?P<routing>[A-Z]{3}(?:-[A-Z]{3})+)\s+(?P<credit>\d+[:\.]?\d+)'),

        # Numeric: 123 3DAY 15JAN-17JAN DEN-LAX-DEN 18:30
        re.compile(r'(?P<trip_id>\d+)\s+(?P<days>\d+)DAY\s+(?P<dates>\S+)\s+(?P<routing>[A-Z]{3}(?:-[A-Z]{3})+)\s+(?P<credit>\d+[:\.]?\d+)'),

        # With aircraft: UA123 737 3DAY DEN-LAX-DEN Credit: 18:30
        re.compile(r'(?P<trip_id>UA\d+)\s+(?P<aircraft>\w+)\s+(?P<days>\d+)DAY\s+(?P<routing>[A-Z]{3}(?:-[A-Z]{3})+)\s+Credit:\s*(?P<credit>\d+[:\.]?\d+)'),
    ]

    for pattern in patterns:
        match = pattern.search(line)
        if match:
            groups = match.groupdict()

            trip_id = groups['trip_id']
            if not trip_id.startswith('UA') and trip_id.isdigit():
                trip_id = f"UA{trip_id}"

            days = int(groups['days'])
            credit_str = groups['credit'].replace(':', '.')
            credit_hours = float(credit_str)
            routing = groups['routing']
            dates = groups.get('dates', '')
            aircraft = groups.get('aircraft', '')

            includes_weekend = any(indicator in line.upper() for indicator in ['SAT', 'SUN', 'WEEKEND'])

            return {
                'trip_id': trip_id,
                'days': days,
                'credit_hours': credit_hours,
                'routing': routing,
                'dates': dates,
                'includes_weekend': includes_weekend,
                'aircraft': aircraft,
                'raw': line,
                'efficiency': credit_hours / days
            }

    return None

def test_full_united_parsing():
    """Test parsing full United bid packet."""
    print("\n📄 Testing Full United Bid Packet...")

    trips = []
    lines = SAMPLE_UNITED_TEXT.split('\n')

    for line in lines:
        line = line.strip()
        if not line or len(line) < 10:
            continue
        if any(header in line.upper() for header in ['TRIP', 'BASE', 'EQUIPMENT', 'UNITED AIRLINES']):
            continue

        trip = parse_united_line(line)
        if trip:
            trips.append(trip)

    print(f"  Parsed {len(trips)} trips from sample bid packet:")
    for trip in trips:
        print(f"  • {trip['trip_id']}: {trip['days']}d, {trip['credit_hours']}h, {trip['routing']}")

    return trips

def test_ai_fallback_ranking():
    """Test ranking logic without OpenAI API calls."""
    print("\n🤖 Testing AI Fallback Ranking...")

    preferences = SAMPLE_PREFERENCES["work_life_balance"]
    trips = SAMPLE_UNITED_TRIPS.copy()

    # Score trips based on preferences
    scored_trips = []
    for trip in trips:
        score = calculate_united_score(trip, preferences)
        trip_with_score = trip.copy()
        trip_with_score['score'] = score
        trip_with_score['reasoning'] = get_united_reasoning(trip, preferences)
        scored_trips.append(trip_with_score)

    # Sort by score
    ranked_trips = sorted(scored_trips, key=lambda x: x['score'], reverse=True)

    print(f"  Preferences: {preferences}")
    for i, trip in enumerate(ranked_trips):
        print(f"  {i+1}. {trip['trip_id']}: {trip['score']}/10 - {trip['reasoning']}")

    return ranked_trips

def calculate_united_score(trip: dict, preferences: str) -> int:
    """Score United trips based on preferences."""
    score = 5  # baseline

    # Work-life balance scoring
    if "weekend" in preferences.lower():
        if not trip['includes_weekend']:
            score += 3
        else:
            score -= 2

    if "shorter" in preferences.lower() or "family" in preferences.lower():
        if trip['days'] <= 2:
            score += 3
        elif trip['days'] <= 3:
            score += 1
        elif trip['days'] >= 5:
            score -= 1

    # Credit hunter scoring
    if "credit" in preferences.lower() or "pay" in preferences.lower():
        efficiency = trip['credit_hours'] / trip['days']
        if efficiency > 8:
            score += 3
        elif efficiency > 6:
            score += 1

    # Commuter preferences (DEN base)
    if "commuter" in preferences.lower() or "DEN" in preferences.lower():
        if trip['routing'].startswith('DEN-') and trip['routing'].endswith('-DEN'):
            score += 2

    # International preference
    if "international" in preferences.lower():
        international_codes = ['LHR', 'FRA', 'NRT', 'ICN', 'CDG', 'AMS']
        if any(code in trip['routing'] for code in international_codes):
            score += 3

    return min(10, max(1, score))

def get_united_reasoning(trip: dict, preferences: str) -> str:
    """Generate reasoning for United trip score."""
    reasons = []

    if not trip['includes_weekend']:
        reasons.append("weekends off")
    if trip['days'] <= 3:
        reasons.append("short trip")

    efficiency = trip['credit_hours'] / trip['days']
    if efficiency > 8:
        reasons.append(f"high efficiency ({efficiency:.1f}h/day)")

    if trip['routing'].startswith('DEN-') and trip['routing'].endswith('-DEN'):
        reasons.append("DEN-based")

    international_codes = ['LHR', 'FRA', 'NRT', 'ICN']
    if any(code in trip['routing'] for code in international_codes):
        reasons.append("international")

    return ", ".join(reasons) if reasons else "standard trip"

def test_profile_matching():
    """Test profile-based preferences."""
    print("\n👤 Testing Profile-Based Preferences...")

    profile = {
        "airline": "United",
        "base": "DEN",
        "fleet": "737",
        "seat": "FO",
        "seniority": 1500,
        "persona": "work_life_balance"
    }

    preferences = build_united_preferences(profile)
    print(f"  Profile: {profile}")
    print(f"  ✅ Generated preferences: {preferences}")

    return preferences

def build_united_preferences(profile: dict) -> str:
    """Build United-specific preferences from profile."""
    base_prefs = SAMPLE_PREFERENCES.get(profile.get('persona', 'work_life_balance'))

    additions = []
    if profile.get('base'):
        additions.append(f"prefer trips departing/arriving at {profile['base']}")
    if profile.get('fleet'):
        additions.append(f"comfortable with {profile['fleet']} aircraft")
    if profile.get('seniority', 0) > 1000:
        additions.append("higher seniority allows for more selective bidding")

    if additions:
        return f"{base_prefs}. Additionally: {', '.join(additions)}."
    return base_prefs

def benchmark_united_performance():
    """Performance test with United data."""
    print("\n⚡ United Airlines Performance Test...")

    start = datetime.now()

    # Simulate processing 100 United trips
    large_trip_set = SAMPLE_UNITED_TRIPS * 34  # 102 trips
    total_scores = 0

    for trip in large_trip_set:
        score = calculate_united_score(trip, SAMPLE_PREFERENCES["work_life_balance"])
        total_scores += score

    end = datetime.now()
    duration = (end - start).total_seconds()

    print(f"  ✅ Processed {len(large_trip_set)} United trips in {duration:.3f}s")
    print(f"  Rate: {len(large_trip_set)/duration:.0f} trips/second")
    print(f"  Average score: {total_scores/len(large_trip_set):.1f}/10")

def run_united_tests():
    """Run all United-focused tests."""
    print("🧪 VectorBid United Airlines Test Harness")
    print("=" * 50)

    # Test each component
    parsed_trips = test_united_parser()
    full_trips = test_full_united_parsing()
    ranked = test_ai_fallback_ranking()
    prefs = test_profile_matching()

    print("\n✅ All United Airlines tests completed!")
    print(f"   Parsed {len(parsed_trips)} individual lines")
    print(f"   Parsed {len(full_trips)} trips from full packet")
    print(f"   Ranked {len(ranked)} trips")
    print(f"   Generated preferences: {len(prefs)} chars")

    return {
        "parsed_trips": parsed_trips,
        "full_trips": full_trips,
        "ranked": ranked,
        "preferences": prefs
    }

if __name__ == "__main__":
    # Quick argument handling
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        if test_name == "parser":
            test_united_parser()
            test_full_united_parsing()
        elif test_name == "ranking":
            test_ai_fallback_ranking()
        elif test_name == "profile":
            test_profile_matching()
        elif test_name == "perf":
            benchmark_united_performance()
        else:
            print(f"Unknown test: {test_name}")
            print("Available tests: parser, ranking, profile, perf")
    else:
        # Run all tests
        results = run_united_tests()
        benchmark_united_performance()

        # Save results for inspection
        try:
            with open('/tmp/united_test_results.json', 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print("\n💾 Results saved to /tmp/united_test_results.json")
        except:
            print("\n💾 Could not save results file")
