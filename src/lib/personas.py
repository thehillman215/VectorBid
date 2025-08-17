"""
Persona Preference System for VectorBid
"""

PILOT_PERSONAS = {
    "family_first": {
        "name": "Family First",
        "description": "Maximize time at home with family",
        "icon": "fas fa-home",
        "preferences": "I want weekends off and no early departures. Prefer short trips of 1-3 days with at least 4 consecutive days off. Avoid red-eyes and overnight trips.",
        "pbs_filters": [
            "AVOID TRIPS IF DUTY_PERIOD OVERLAPS SAT OR SUN",
            "PREFER TRIPS WITH DUTY_DAYS <= 3",
            "AVOID TRIPS WITH DEPARTURE_TIME BETWEEN 2200 AND 0559",
            "PREFER MAX_DAYS_OFF",
            "AVOID TRIPS STARTING BEFORE 0800"
        ]
    },
    "money_maker": {
        "name": "Money Maker",
        "description": "Maximize earnings and credit",
        "icon": "fas fa-dollar-sign",
        "preferences": "I want long trips with maximum credit hours. Prefer international flying and trips with overtime opportunities. Weekend flying is fine.",
        "pbs_filters": [
            "PREFER TRIPS WITH DUTY_DAYS >= 4",
            "PREFER TRIPS WITH DESTINATION INTL",
            "PREFER TRIPS WITH MAX_CREDIT_HOURS",
            "PREFER TRIPS WITH OVERTIME_ELIGIBLE = TRUE"
        ]
    },
    "commuter_friendly": {
        "name": "Commuter Friendly",
        "description": "Optimize for easy commuting",
        "icon": "fas fa-plane-departure",
        "preferences": "I need late starts and early finishes for commuting. Prefer trips starting after 10am and ending before 8pm. Minimize short overnights.",
        "pbs_filters": [
            "PREFER TRIPS STARTING AFTER 1000",
            "PREFER TRIPS ENDING BEFORE 2000",
            "AVOID TRIPS WITH LAYOVER_TIME < 10:00",
            "PREFER TRIPS WITH DUTY_DAYS <= 3"
        ]
    },
    "quality_of_life": {
        "name": "Quality of Life",
        "description": "Balance work and personal time",
        "icon": "fas fa-balance-scale",
        "preferences": "I want a balanced schedule with weekends off when possible, reasonable trip lengths, and good layovers. Avoid red-eyes.",
        "pbs_filters": [
            "PREFER TRIPS IF DUTY_PERIOD AVOIDS SAT OR SUN",
            "PREFER TRIPS WITH DUTY_DAYS BETWEEN 2 AND 4",
            "AVOID TRIPS WITH DEPARTURE_TIME BETWEEN 2200 AND 0559",
            "PREFER TRIPS WITH LAYOVER_TIME > 2:00"
        ]
    },
    "reserve_avoider": {
        "name": "Reserve Avoider",
        "description": "Any line to avoid reserve",
        "icon": "fas fa-calendar-check",
        "preferences": "I'll take any line to avoid reserve. Flexible on all trip types, destinations, and schedules.",
        "pbs_filters": [
            "PREFER ANY_LINE_OVER_RESERVE",
            "MINIMIZE_RESERVE_DAYS",
            "ACCEPT_ALL_TRIP_TYPES"
        ]
    },
    "adventure_seeker": {
        "name": "Adventure Seeker",
        "description": "New destinations and experiences",
        "icon": "fas fa-globe-americas",
        "preferences": "I want international trips with long layovers in interesting cities. Prefer new destinations and varied routes.",
        "pbs_filters": [
            "PREFER TRIPS WITH DESTINATION INTL",
            "PREFER TRIPS WITH LAYOVER_TIME > 24:00",
            "PREFER TRIPS WITH VARIED_DESTINATIONS",
            "PREFER TRIPS WITH NEW_ROUTES"
        ]
    }
}

def get_persona_preferences(persona_key):
    """Get preferences text for a specific persona"""
    if persona_key in PILOT_PERSONAS:
        return PILOT_PERSONAS[persona_key]["preferences"]
    return ""

def get_persona_pbs_filters(persona_key):
    """Get PBS filters for a specific persona"""
    if persona_key in PILOT_PERSONAS:
        return PILOT_PERSONAS[persona_key]["pbs_filters"]
    return ["PREFER TRIPS WITH GOOD_QUALITY_OF_LIFE"]
