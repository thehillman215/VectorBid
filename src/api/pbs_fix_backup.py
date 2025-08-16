"""
Fixed PBS Generation Functions for routes.py
"""

def natural_language_to_pbs_filters(preferences_text, trip_data=None):
    """Generate PBS filters from natural language preferences"""

    # Handle empty input
    if not preferences_text or preferences_text.strip() == "":
        return ["PREFER TRIPS WITH GOOD_QUALITY_OF_LIFE"]

    filters = []
    text_lower = preferences_text.lower().strip()

    # Debug logging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Processing preferences: {text_lower}")

    # Weekend preferences
    weekend_phrases = ['weekends off', 'weekend off', 'no weekends', 'no weekend', 
                      'avoid weekends', 'weekends free', 'saturday off', 'sunday off']
    if any(phrase in text_lower for phrase in weekend_phrases):
        filters.append("AVOID TRIPS IF DUTY_PERIOD OVERLAPS SAT OR SUN")
        logger.info("Added weekend filter")

    # Early morning preferences
    early_phrases = ['no early', 'avoid early', 'late start', 'no morning', 
                    'avoid morning', 'no early departure', 'no early departures']
    if any(phrase in text_lower for phrase in early_phrases):
        filters.append("AVOID TRIPS STARTING BEFORE 0800")
        logger.info("Added early morning filter")

    # Trip length preferences
    if any(phrase in text_lower for phrase in ['short trip', 'day trip', '1 day', 'one day', 'short']):
        filters.append("PREFER TRIPS WITH DUTY_DAYS <= 2")
        logger.info("Added short trip filter")
    elif any(phrase in text_lower for phrase in ['long trip', '4 day', 'four day', 'week long']):
        filters.append("PREFER TRIPS WITH DUTY_DAYS >= 4")
        logger.info("Added long trip filter")

    # Red-eye preferences
    redeye_phrases = ['no redeye', 'avoid redeye', 'no red-eye', 'no red eye', 
                     'avoid red-eye', 'no overnight', 'no late night']
    if any(phrase in text_lower for phrase in redeye_phrases):
        filters.append("AVOID TRIPS WITH DEPARTURE_TIME BETWEEN 2200 AND 0559")
        logger.info("Added red-eye filter")

    # Commute preferences
    commute_phrases = ['commut', 'late start', 'commutable', 'easy commute']
    if any(phrase in text_lower for phrase in commute_phrases):
        filters.append("PREFER TRIPS STARTING AFTER 1000")
        logger.info("Added commute filter")

    # International preferences
    if 'international' in text_lower or 'overseas' in text_lower:
        if any(word in text_lower for word in ['avoid', 'no', 'without']):
            filters.append("AVOID TRIPS WITH DESTINATION INTL")
            logger.info("Added avoid international filter")
        else:
            filters.append("PREFER TRIPS WITH DESTINATION INTL")
            logger.info("Added prefer international filter")

    # Layover preferences
    if 'layover' in text_lower:
        if any(word in text_lower for word in ['short', 'quick', 'minimal']):
            filters.append("PREFER TRIPS WITH LAYOVER_TIME < 2:00")
            logger.info("Added short layover filter")
        elif any(word in text_lower for word in ['long', 'extended']):
            filters.append("PREFER TRIPS WITH LAYOVER_TIME > 3:00")
            logger.info("Added long layover filter")

    # Days off preferences
    if 'days off' in text_lower or 'time off' in text_lower:
        filters.append("PREFER MAX_DAYS_OFF")
        logger.info("Added days off filter")

    # Specific date avoidance (birthday, anniversary, etc.)
    import re
    date_pattern = r'(\d{1,2})(st|nd|rd|th)?'
    date_matches = re.findall(date_pattern, text_lower)
    for match in date_matches:
        day = match[0]
        if any(word in text_lower for word in ['avoid', 'off', 'not flying', 'home']):
            filters.append(f"AVOID TRIPS ON DAY {day}")
            logger.info(f"Added date avoidance filter for day {day}")

    # Add default if no specific matches
    if not filters:
        filters.append("PREFER TRIPS WITH GOOD_QUALITY_OF_LIFE")
        logger.info("No specific matches, added default filter")

    logger.info(f"Generated {len(filters)} PBS filters")
    return filters

# Add this function to the existing routes.py file
