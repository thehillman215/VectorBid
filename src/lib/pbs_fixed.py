"""
Fixed PBS Generation Module for VectorBid
This module contains the corrected PBS filter generation functions
"""

import logging
import re

logger = logging.getLogger(__name__)


def _fallback_pbs_generation(preferences_text):
    """Fixed PBS generation with working pattern matching"""

    # Handle empty input
    if not preferences_text or preferences_text.strip() == "":
        return ["PREFER TRIPS WITH GOOD_QUALITY_OF_LIFE"]

    filters = []
    text_lower = preferences_text.lower().strip()

    logger.info(f"PBS Processing preferences: {text_lower}")

    # Weekend preferences - EXPANDED PHRASES
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
        "no saturday",
        "no sunday",
    ]
    if any(phrase in text_lower for phrase in weekend_phrases):
        filters.append("AVOID TRIPS IF DUTY_PERIOD OVERLAPS SAT OR SUN")
        logger.info("Added weekend filter")

    # Early morning preferences - EXPANDED PHRASES
    early_phrases = [
        "no early",
        "avoid early",
        "late start",
        "no morning",
        "avoid morning",
        "no early departure",
        "no early departures",
        "not early",
        "hate early",
        "sleep in",
        "no dawn",
    ]
    if any(phrase in text_lower for phrase in early_phrases):
        filters.append("AVOID TRIPS STARTING BEFORE 0800")
        logger.info("Added early morning filter")

    # Trip length preferences
    short_phrases = [
        "short trip",
        "day trip",
        "1 day",
        "one day",
        "short",
        "quick trip",
        "turns",
        "day turns",
        "no overnight",
    ]
    long_phrases = [
        "long trip",
        "4 day",
        "four day",
        "week long",
        "5 day",
        "five day",
        "extended",
        "multi-day",
    ]

    if any(phrase in text_lower for phrase in short_phrases):
        filters.append("PREFER TRIPS WITH DUTY_DAYS <= 2")
        logger.info("Added short trip filter")
    elif any(phrase in text_lower for phrase in long_phrases):
        filters.append("PREFER TRIPS WITH DUTY_DAYS >= 4")
        logger.info("Added long trip filter")

    # Red-eye preferences - EXPANDED PHRASES
    redeye_phrases = [
        "no redeye",
        "avoid redeye",
        "no red-eye",
        "no red eye",
        "avoid red-eye",
        "no overnight",
        "no late night",
        "not redeye",
        "hate redeye",
        "no night flight",
    ]
    if any(phrase in text_lower for phrase in redeye_phrases):
        filters.append("AVOID TRIPS WITH DEPARTURE_TIME BETWEEN 2200 AND 0559")
        logger.info("Added red-eye filter")

    # Commute preferences - EXPANDED PHRASES
    commute_phrases = [
        "commut",
        "late start",
        "commutable",
        "easy commute",
        "commuter",
        "drive in",
        "drive home",
        "same day",
    ]
    if any(phrase in text_lower for phrase in commute_phrases):
        filters.append("PREFER TRIPS STARTING AFTER 1000")
        logger.info("Added commute filter")

    # International preferences
    intl_phrases = [
        "international",
        "overseas",
        "europe",
        "asia",
        "london",
        "paris",
        "tokyo",
        "foreign",
        "abroad",
    ]
    if any(phrase in text_lower for phrase in intl_phrases):
        # Note: avoiding quote issues by using list
        avoid_words = ["avoid", "no", "without", "not", "dont", "hate"]
        if any(word in text_lower for word in avoid_words):
            filters.append("AVOID TRIPS WITH DESTINATION INTL")
            logger.info("Added avoid international filter")
        else:
            filters.append("PREFER TRIPS WITH DESTINATION INTL")
            logger.info("Added prefer international filter")

    # Layover preferences
    if "layover" in text_lower or "overnight" in text_lower:
        if any(word in text_lower for word in ["short", "quick", "minimal", "brief"]):
            filters.append("PREFER TRIPS WITH LAYOVER_TIME < 2:00")
            logger.info("Added short layover filter")
        elif any(word in text_lower for word in ["long", "extended", "relaxed"]):
            filters.append("PREFER TRIPS WITH LAYOVER_TIME > 24:00")
            logger.info("Added long layover filter")

    # Days off preferences
    days_off_phrases = ["days off", "time off", "more off", "maximize off"]
    if any(phrase in text_lower for phrase in days_off_phrases):
        filters.append("PREFER MAX_DAYS_OFF")
        logger.info("Added days off filter")

    # Specific date avoidance (birthday, anniversary, etc.)
    # Using raw string to avoid escape issues
    date_pattern = r"(\d{1,2})(st|nd|rd|th)?"
    try:
        date_matches = re.findall(date_pattern, text_lower)
        for match in date_matches:
            day = match[0]
            context_words = [
                "avoid",
                "off",
                "not flying",
                "home",
                "birthday",
                "anniversary",
            ]
            if any(word in text_lower for word in context_words):
                filters.append(f"AVOID TRIPS ON DAY {day}")
                logger.info(f"Added date avoidance filter for day {day}")
    except Exception:
        pass  # Skip date parsing if it fails

    # Specific city preferences
    cities = {
        "denver": "DEN",
        "chicago": "ORD",
        "houston": "IAH",
        "newark": "EWR",
        "san francisco": "SFO",
        "los angeles": "LAX",
        "boston": "BOS",
        "seattle": "SEA",
        "miami": "MIA",
        "dallas": "DFW",
    }
    for city, code in cities.items():
        if city in text_lower:
            if any(word in text_lower for word in ["avoid", "no", "not", "hate"]):
                filters.append(f"AVOID TRIPS WITH LAYOVER IN {code}")
                logger.info(f"Added avoid {city} filter")
            elif any(word in text_lower for word in ["prefer", "like", "love", "want"]):
                filters.append(f"PREFER TRIPS WITH LAYOVER IN {code}")
                logger.info(f"Added prefer {city} filter")

    # Home every night preference
    home_phrases = ["home every night", "home daily", "no overnights", "day trips only"]
    if any(phrase in text_lower for phrase in home_phrases):
        filters.append("PREFER TRIPS WITH DUTY_DAYS = 1")
        logger.info("Added home every night filter")

    # Add default if no specific matches
    if not filters:
        filters.append("PREFER TRIPS WITH GOOD_QUALITY_OF_LIFE")
        logger.info("No specific matches, added default filter")

    logger.info(f"Generated {len(filters)} PBS filters")
    return filters


def natural_language_to_pbs_filters(preferences_text, trip_data=None):
    """Main PBS filter generation function - tries enhanced then falls back"""

    # First try the enhanced system if available
    try:
        from src.lib.vectorbid_pbs_integration import VectorBidPBSService

        service = VectorBidPBSService()

        # Get pilot profile from session if available
        from flask import session

        pilot_profile = {}
        user_id = session.get("user_id", "44040350")

        if user_id:
            try:
                from src.lib.services.db import get_profile

                profile = get_profile(user_id)
                if profile:
                    pilot_profile = profile
            except Exception:
                pass

        # Process preferences with enhanced system
        result = service.process_pilot_preferences(
            preferences=preferences_text, user_id=user_id, pilot_profile=pilot_profile
        )

        if result["success"]:
            # Store enhanced data in session for results page
            session["enhanced_pbs_data"] = result["session_data"]
            return result["commands"]
        else:
            logger.error(f"Enhanced PBS generation failed: {result.get('error', 'Unknown error')}")
            return _fallback_pbs_generation(preferences_text)

    except ImportError:
        logger.info("Enhanced PBS system not available, using fixed fallback")
        return _fallback_pbs_generation(preferences_text)
    except Exception as e:
        logger.error(f"Enhanced PBS system error: {str(e)}")
        return _fallback_pbs_generation(preferences_text)
