"""
Enhanced PBS Generation Functions for routes.py
This version handles comprehensive pilot language patterns
"""

import logging

logger = logging.getLogger(__name__)


def natural_language_to_pbs_filters(preferences_text, trip_data=None):
    """Generate PBS filters from natural language preferences"""

    # Handle empty input
    if not preferences_text or preferences_text.strip() == "":
        return ["PREFER TRIPS WITH GOOD_QUALITY_OF_LIFE"]

    filters = []
    text_lower = preferences_text.lower().strip()

    # Debug logging
    logger.info(f"Processing preferences: {text_lower}")

    # ==========================================
    # WEEKEND PREFERENCES
    # ==========================================
    weekend_phrases = [
        "weekends off",
        "weekend off",
        "no weekends",
        "no weekend",
        "avoid weekends",
        "weekends free",
        "saturday off",
        "sunday off",
        "saturdays off",
        "sundays off",
        "sat off",
        "sun off",
        "family time",
        "weekend home",
    ]
    if any(phrase in text_lower for phrase in weekend_phrases):
        filters.append("AVOID TRIPS IF DUTY_PERIOD OVERLAPS SAT OR SUN")
        # If specifically mentioned for family, add quality of life
        if "family" in text_lower or "kids" in text_lower:
            filters.append("PREFER TRIPS WITH GOOD_QUALITY_OF_LIFE")

    # ==========================================
    # EARLY MORNING PREFERENCES
    # ==========================================
    early_phrases = [
        "no early",
        "avoid early",
        "late start",
        "no morning",
        "avoid morning",
        "no early departure",
        "no early departures",
        "sleep in",
        "not a morning person",
        "no early shows",
        "no early report",
        "late show",
    ]
    if any(phrase in text_lower for phrase in early_phrases):
        filters.append("AVOID TRIPS STARTING BEFORE 0800")

    # ==========================================
    # TRIP LENGTH PREFERENCES
    # ==========================================
    # Short trips
    short_phrases = [
        "short trip",
        "day trip",
        "1 day",
        "one day",
        "short",
        "quick turn",
        "turn",
        "day trips",
        "single day",
        "home every night",
        "home each night",
        "no overnight",
        "home daily",
        "local",
    ]
    if any(phrase in text_lower for phrase in short_phrases):
        filters.append("PREFER TRIPS WITH DUTY_DAYS <= 2")
        if "home" in text_lower and ("night" in text_lower or "daily" in text_lower):
            filters.append("PREFER DAY_TRIPS_NO_OVERNIGHT")

    # 3-day specific
    if "3 day" in text_lower or "three day" in text_lower or "3-day" in text_lower:
        filters.append("PREFER TRIPS WITH DUTY_DAYS = 3")

    # 4-day specific
    if "4 day" in text_lower or "four day" in text_lower or "4-day" in text_lower:
        filters.append("PREFER TRIPS WITH DUTY_DAYS = 4")

    # Long trips
    long_phrases = ["long trip", "week long", "extended", "long haul"]
    if any(phrase in text_lower for phrase in long_phrases):
        filters.append("PREFER TRIPS WITH DUTY_DAYS >= 4")

    # ==========================================
    # RED-EYE PREFERENCES
    # ==========================================
    redeye_phrases = [
        "no redeye",
        "avoid redeye",
        "no red-eye",
        "no red eye",
        "avoid red-eye",
        "no overnight",
        "no late night",
        "no all-nighter",
        "avoid night flying",
    ]
    if any(phrase in text_lower for phrase in redeye_phrases):
        filters.append("AVOID TRIPS WITH DEPARTURE_TIME BETWEEN 2200 AND 0559")

    # ==========================================
    # COMMUTER PREFERENCES
    # ==========================================
    commute_phrases = [
        "commut",
        "late start",
        "commutable",
        "easy commute",
        "drive in",
        "live far",
        "non-local",
        "late show",
    ]
    if any(phrase in text_lower for phrase in commute_phrases):
        filters.append("PREFER TRIPS STARTING AFTER 1000")
        if "commut" in text_lower:
            filters.append("PREFER TRIPS ENDING BEFORE 2000")

    # ==========================================
    # PAY/CREDIT PREFERENCES

    # ==========================================
    # FINAL 100% PATTERNS
    # ==========================================

    # Enhanced credit maximization (specific phrases)
    if "maximize credit hour" in text_lower or "max credit hour" in text_lower:
        filters.append("MAXIMIZE CREDIT_TIME")
        filters.append("PREFER HIGH_CREDIT_TRIPS")
        filters.append("MAXIMIZE MONTHLY_CREDIT")

    # Slam-clicker lifestyle (pilot who goes straight to hotel)
    if "slam-click" in text_lower or "slamclick" in text_lower or "slam click" in text_lower:
        if "PREFER LAYOVERS >= 14 HOURS" not in filters:
            filters.append("PREFER LAYOVERS >= 14 HOURS")
        if "PREFER TRIPS WITH QUALITY_HOTELS" not in filters:
            filters.append("PREFER TRIPS WITH QUALITY_HOTELS")

    # High-time turns (single day trips with max pay)
    if "high-time turn" in text_lower or "high time turn" in text_lower:
        filters.append("PREFER TRIPS WITH DUTY_DAYS = 1")
        filters.append("MAXIMIZE CREDIT_PER_DAY")
    elif "high-time" in text_lower or "high time" in text_lower:
        if "turn" in text_lower:
            filters.append("PREFER TRIPS WITH DUTY_DAYS = 1")
            filters.append("MAXIMIZE CREDIT_PER_DAY")

    # ==========================================
    credit_phrases = [
        "max credit",
        "maximum credit",
        "high credit",
        "max pay",
        "maximum pay",
        "high pay",
        "credit time",
        "build time",
        "high time",
        "max hours",
        "overtime",
        "premium pay",
        "productive",
        "efficiency",
    ]
    if any(phrase in text_lower for phrase in credit_phrases):
        filters.append("MAXIMIZE CREDIT_TIME")
        filters.append("PREFER HIGH_CREDIT_TRIPS")

    # ==========================================
    # LAYOVER PREFERENCES
    # ==========================================
    if "long layover" in text_lower or "good layover" in text_lower:
        filters.append("PREFER LAYOVERS >= 14 HOURS")
    elif "short layover" in text_lower or "quick layover" in text_lower:
        filters.append("PREFER LAYOVERS <= 12 HOURS")

    if "good hotel" in text_lower or "nice hotel" in text_lower:
        filters.append("PREFER TRIPS WITH QUALITY_HOTELS")

    # ==========================================
    # BASE/EQUIPMENT PREFERENCES
    # ==========================================
    # Check for specific bases
    bases = ["DEN", "ORD", "IAH", "EWR", "SFO", "LAX", "DCA", "BOS"]
    for base in bases:
        if base in text_lower or base.lower() in text_lower:
            filters.append(f"PREFER TRIPS FROM BASE {base}")

    # Equipment preferences
    if "737" in text_lower:
        filters.append("PREFER EQUIPMENT TYPE 737")
    if "777" in text_lower or "triple" in text_lower:
        filters.append("PREFER EQUIPMENT TYPE 777")
    if "787" in text_lower or "dreamliner" in text_lower:
        filters.append("PREFER EQUIPMENT TYPE 787")

    # ==========================================
    # INTERNATIONAL PREFERENCES
    # ==========================================
    intl_phrases = [
        "international",
        "europe",
        "asia",
        "london",
        "paris",
        "frankfurt",
        "tokyo",
        "overseas",
        "long haul",
        "widebody",
        "atlantic",
        "pacific",
        "LHR",
        "CDG",
        "FRA",
        "NRT",
    ]
    if any(phrase in text_lower for phrase in intl_phrases):
        filters.append("PREFER INTERNATIONAL_FLIGHTS")
        if "europe" in text_lower:
            filters.append("PREFER EUROPEAN_DESTINATIONS")
        if "asia" in text_lower:
            filters.append("PREFER ASIAN_DESTINATIONS")

    # ==========================================
    # DOMESTIC PREFERENCES
    # ==========================================
    if "domestic" in text_lower or "conus" in text_lower:
        filters.append("PREFER DOMESTIC_ONLY")

    # ==========================================
    # SPECIFIC DAY PREFERENCES
    # ==========================================
    days = {
        "monday": "MON",
        "tuesday": "TUE",
        "wednesday": "WED",
        "thursday": "THU",
        "friday": "FRI",
        "saturday": "SAT",
        "sunday": "SUN",
    }
    for day_name, day_code in days.items():
        if day_name in text_lower:
            if "no " + day_name in text_lower or "avoid " + day_name in text_lower:
                filters.append(f"AVOID TRIPS IF DUTY_PERIOD INCLUDES {day_code}")
            elif day_name + " off" in text_lower or day_name + "s off" in text_lower:
                filters.append(f"AVOID TRIPS IF DUTY_PERIOD INCLUDES {day_code}")

    # ==========================================
    # RESERVE PREFERENCES
    # ==========================================
    reserve_phrases = ["no reserve", "avoid reserve", "no standby", "line holder"]
    if any(phrase in text_lower for phrase in reserve_phrases):
        filters.append("AVOID RESERVE_ASSIGNMENTS")
    elif "long call" in text_lower:
        filters.append("PREFER LONG_CALL_RESERVE")
    elif "short call" in text_lower:
        filters.append("PREFER SHORT_CALL_RESERVE")

    # ==========================================
    # SENIORITY-BASED PREFERENCES
    # ==========================================
    if "senior" in text_lower and "junior" not in text_lower:
        filters.append("APPLY SENIOR_PILOT_PREFERENCES")
    elif "junior" in text_lower:
        filters.append("APPLY JUNIOR_PILOT_FLEXIBILITY")

    # ==========================================
    # TRAINING PREFERENCES
    # ==========================================
    if "training" in text_lower or "sim" in text_lower or "recurrent" in text_lower:
        filters.append("ENSURE TRAINING_DAYS_AVAILABLE")

    # ==========================================
    # VACATION PREFERENCES
    # ==========================================
    if "vacation" in text_lower or "time off" in text_lower:
        filters.append("PROTECT VACATION_DAYS")

    # ==========================================
    # HOLIDAY PREFERENCES
    # ==========================================
    holiday_phrases = [
        "christmas",
        "thanksgiving",
        "new year",
        "july 4",
        "memorial day",
        "labor day",
        "holiday",
    ]
    if any(phrase in text_lower for phrase in holiday_phrases):
        filters.append("AVOID TRIPS DURING HOLIDAYS")

    # ==========================================
    # QUALITY OF LIFE (CATCH-ALL)
    # ==========================================
    qol_phrases = [
        "quality of life",
        "work life balance",
        "family first",
        "lifestyle",
        "easy month",
        "relaxed",
    ]
    if any(phrase in text_lower for phrase in qol_phrases):
        if "PREFER TRIPS WITH GOOD_QUALITY_OF_LIFE" not in filters:
            filters.append("PREFER TRIPS WITH GOOD_QUALITY_OF_LIFE")

    # ==========================================
    # SPECIAL PATTERNS
    # ==========================================
    # Min rest issues
    if "min rest" in text_lower or "minimum rest" in text_lower:
        filters.append("AVOID MINIMUM_REST_LAYOVERS")

    # Deadheading
    if "no deadhead" in text_lower or "no dh" in text_lower:
        filters.append("AVOID DEADHEAD_SEGMENTS")

    # CDO/Standup
    if "cdo" in text_lower or "continuous duty" in text_lower or "standup" in text_lower:
        filters.append("AVOID CONTINUOUS_DUTY_OVERNIGHTS")

    # Hub turns
    if "no hub turn" in text_lower or "avoid hub turn" in text_lower:
        filters.append("AVOID HUB_TURNS")

    # Remove duplicates while preserving order
    seen = set()
    unique_filters = []
    for f in filters:
        if f not in seen:
            seen.add(f)
            unique_filters.append(f)

    # Log what we generated
    logger.info(f"Generated {len(unique_filters)} PBS commands")

    # Return filters or default if none found
    return unique_filters if unique_filters else ["PREFER TRIPS WITH GOOD_QUALITY_OF_LIFE"]


# Test function to verify it's working
def test_enhanced_nlp():
    """Quick test of the enhanced NLP"""
    test_cases = [
        "I want weekends off",
        "No early morning departures",
        "I need commutable trips, no red-eyes, and max credit",
        "Family first - home every night if possible",
        "No red-eyes or early departures, prefer 3-day trips",
    ]

    print("Testing Enhanced NLP")
    print("=" * 50)

    for test in test_cases:
        result = natural_language_to_pbs_filters(test)
        print(f"\nInput: '{test}'")
        print(f"Commands ({len(result)}):")
        for cmd in result:
            print(f"  • {cmd}")

    return True


if __name__ == "__main__":
    test_enhanced_nlp()
