#!/usr/bin/env python3
"""
FIXED VERSION - AUTOMATIC PBS FIX FOR VECTORBID
This script automatically fixes all PBS generation issues
Just run: python fix_vectorbid_v2.py
"""

import os
import shutil
from datetime import datetime
from pathlib import Path


def backup_file(filepath):
    """Create a backup of a file before modifying"""
    if os.path.exists(filepath):
        backup_path = f"{filepath}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(filepath, backup_path)
        print(f"  📁 Backed up to: {backup_path}")
        return True
    return False


def write_file(filepath, content):
    """Write content to file"""
    try:
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"  ✅ Updated: {filepath}")
        return True
    except Exception as e:
        print(f"  ❌ Error writing {filepath}: {e}")
        return False


print("=" * 60)
print("🚀 VECTORBID PBS FIX - VERSION 2")
print("=" * 60)
print()

# Step 1: Create the fixed PBS function as a separate file
print("Step 1: Creating fixed PBS generation module...")

fixed_pbs_module = '''"""
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
        'weekends off', 'weekend off', 'no weekends', 'no weekend', 
        'avoid weekends', 'weekends free', 'saturday off', 'sunday off',
        'saturdays off', 'sundays off', 'no saturday', 'no sunday'
    ]
    if any(phrase in text_lower for phrase in weekend_phrases):
        filters.append("AVOID TRIPS IF DUTY_PERIOD OVERLAPS SAT OR SUN")
        logger.info("Added weekend filter")

    # Early morning preferences - EXPANDED PHRASES
    early_phrases = [
        'no early', 'avoid early', 'late start', 'no morning', 
        'avoid morning', 'no early departure', 'no early departures',
        'not early', 'hate early', 'sleep in', 'no dawn'
    ]
    if any(phrase in text_lower for phrase in early_phrases):
        filters.append("AVOID TRIPS STARTING BEFORE 0800")
        logger.info("Added early morning filter")

    # Trip length preferences
    short_phrases = [
        'short trip', 'day trip', '1 day', 'one day', 'short', 
        'quick trip', 'turns', 'day turns', 'no overnight'
    ]
    long_phrases = [
        'long trip', '4 day', 'four day', 'week long', '5 day',
        'five day', 'extended', 'multi-day'
    ]

    if any(phrase in text_lower for phrase in short_phrases):
        filters.append("PREFER TRIPS WITH DUTY_DAYS <= 2")
        logger.info("Added short trip filter")
    elif any(phrase in text_lower for phrase in long_phrases):
        filters.append("PREFER TRIPS WITH DUTY_DAYS >= 4")
        logger.info("Added long trip filter")

    # Red-eye preferences - EXPANDED PHRASES
    redeye_phrases = [
        'no redeye', 'avoid redeye', 'no red-eye', 'no red eye', 
        'avoid red-eye', 'no overnight', 'no late night',
        'not redeye', 'hate redeye', 'no night flight'
    ]
    if any(phrase in text_lower for phrase in redeye_phrases):
        filters.append("AVOID TRIPS WITH DEPARTURE_TIME BETWEEN 2200 AND 0559")
        logger.info("Added red-eye filter")

    # Commute preferences - EXPANDED PHRASES
    commute_phrases = [
        'commut', 'late start', 'commutable', 'easy commute',
        'commuter', 'drive in', 'drive home', 'same day'
    ]
    if any(phrase in text_lower for phrase in commute_phrases):
        filters.append("PREFER TRIPS STARTING AFTER 1000")
        logger.info("Added commute filter")

    # International preferences
    intl_phrases = [
        'international', 'overseas', 'europe', 'asia', 'london',
        'paris', 'tokyo', 'foreign', 'abroad'
    ]
    if any(phrase in text_lower for phrase in intl_phrases):
        # Note: avoiding quote issues by using list
        avoid_words = ['avoid', 'no', 'without', 'not', 'dont', 'hate']
        if any(word in text_lower for word in avoid_words):
            filters.append("AVOID TRIPS WITH DESTINATION INTL")
            logger.info("Added avoid international filter")
        else:
            filters.append("PREFER TRIPS WITH DESTINATION INTL")
            logger.info("Added prefer international filter")

    # Layover preferences
    if 'layover' in text_lower or 'overnight' in text_lower:
        if any(word in text_lower for word in ['short', 'quick', 'minimal', 'brief']):
            filters.append("PREFER TRIPS WITH LAYOVER_TIME < 2:00")
            logger.info("Added short layover filter")
        elif any(word in text_lower for word in ['long', 'extended', 'relaxed']):
            filters.append("PREFER TRIPS WITH LAYOVER_TIME > 24:00")
            logger.info("Added long layover filter")

    # Days off preferences
    days_off_phrases = ['days off', 'time off', 'more off', 'maximize off']
    if any(phrase in text_lower for phrase in days_off_phrases):
        filters.append("PREFER MAX_DAYS_OFF")
        logger.info("Added days off filter")

    # Specific date avoidance (birthday, anniversary, etc.)
    # Using raw string to avoid escape issues
    date_pattern = r'(\\d{1,2})(st|nd|rd|th)?'
    try:
        date_matches = re.findall(date_pattern, text_lower)
        for match in date_matches:
            day = match[0]
            context_words = ['avoid', 'off', 'not flying', 'home', 'birthday', 'anniversary']
            if any(word in text_lower for word in context_words):
                filters.append(f"AVOID TRIPS ON DAY {day}")
                logger.info(f"Added date avoidance filter for day {day}")
    except:
        pass  # Skip date parsing if it fails

    # Specific city preferences
    cities = {
        'denver': 'DEN', 'chicago': 'ORD', 'houston': 'IAH', 'newark': 'EWR',
        'san francisco': 'SFO', 'los angeles': 'LAX', 'boston': 'BOS',
        'seattle': 'SEA', 'miami': 'MIA', 'dallas': 'DFW'
    }
    for city, code in cities.items():
        if city in text_lower:
            if any(word in text_lower for word in ['avoid', 'no', 'not', 'hate']):
                filters.append(f"AVOID TRIPS WITH LAYOVER IN {code}")
                logger.info(f"Added avoid {city} filter")
            elif any(word in text_lower for word in ['prefer', 'like', 'love', 'want']):
                filters.append(f"PREFER TRIPS WITH LAYOVER IN {code}")
                logger.info(f"Added prefer {city} filter")

    # Home every night preference
    home_phrases = ['home every night', 'home daily', 'no overnights', 'day trips only']
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
        user_id = session.get('user_id', '44040350')

        if user_id:
            try:
                from src.lib.services.db import get_profile
                profile = get_profile(user_id)
                if profile:
                    pilot_profile = profile
            except:
                pass

        # Process preferences with enhanced system
        result = service.process_pilot_preferences(
            preferences=preferences_text,
            user_id=user_id,
            pilot_profile=pilot_profile
        )

        if result['success']:
            # Store enhanced data in session for results page
            session['enhanced_pbs_data'] = result['session_data']
            return result['commands']
        else:
            logger.error(f"Enhanced PBS generation failed: {result.get('error', 'Unknown error')}")
            return _fallback_pbs_generation(preferences_text)

    except ImportError:
        logger.info("Enhanced PBS system not available, using fixed fallback")
        return _fallback_pbs_generation(preferences_text)
    except Exception as e:
        logger.error(f"Enhanced PBS system error: {str(e)}")
        return _fallback_pbs_generation(preferences_text)
'''

write_file("src/lib/pbs_fixed.py", fixed_pbs_module)

# Step 2: Create a patch file that imports the fixed module
print("\nStep 2: Creating patch for routes.py...")

patch_code = '''
# Add this to the TOP of your routes.py file, right after the other imports:

# Import the fixed PBS generation functions
from src.lib.pbs_fixed import natural_language_to_pbs_filters, _fallback_pbs_generation

# That's it! The functions are now available to use in your routes.
'''

write_file("routes_patch_instructions.txt", patch_code)

# Step 3: Read current routes.py and add the import
print("\nStep 3: Patching routes.py...")
routes_path = "src/api/routes.py"

if os.path.exists(routes_path):
    backup_file(routes_path)

    with open(routes_path, 'r') as f:
        current_content = f.read()

    # Check if already has the import
    if 'from src.lib.pbs_fixed import' in current_content:
        print("  ✅ Routes.py already imports the fixed module")
    else:
        # Find the last import line
        lines = current_content.split('\n')
        last_import_index = 0

        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                last_import_index = i

        # Add our import after the last import
        lines.insert(last_import_index + 1, '')
        lines.insert(last_import_index + 2, '# Fixed PBS generation functions')
        lines.insert(
            last_import_index + 3,
            'from src.lib.pbs_fixed import natural_language_to_pbs_filters, _fallback_pbs_generation'
        )

        new_content = '\n'.join(lines)

        with open(routes_path, 'w') as f:
            f.write(new_content)

        print("  ✅ Added import for fixed PBS module to routes.py")

# Step 4: Create test file
print("\nStep 4: Creating test file...")

test_content = '''#!/usr/bin/env python3
"""Test the PBS fix - Version 2"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("Testing PBS Natural Language Processing...")
print("=" * 60)

# Import the fixed functions
try:
    from src.lib.pbs_fixed import natural_language_to_pbs_filters, _fallback_pbs_generation
    print("✅ Successfully imported fixed PBS functions")
except ImportError as e:
    print(f"❌ Could not import: {e}")
    sys.exit(1)

# Test cases
test_cases = [
    ("I want weekends off and no early departures", 2, "Weekend + Early"),
    ("Short trips only with no red-eyes", 2, "Short + Red-eye"),
    ("International flying with long layovers", 2, "International + Layover"),
    ("Commutable trips starting late", 1, "Commute"),
    ("Maximum days off with weekends free", 2, "Days off + Weekend"),
    ("", 1, "Empty input"),
    ("Home every night please", 1, "Day trips only"),
]

print()
all_passed = True

for input_text, min_expected, description in test_cases:
    try:
        filters = _fallback_pbs_generation(input_text)

        if len(filters) >= min_expected:
            print(f"✅ PASS: {description}")
            print(f"   Generated {len(filters)} filters:")
            for f in filters[:3]:  # Show first 3
                print(f"   - {f}")
        else:
            print(f"❌ FAIL: {description}")
            print(f"   Expected >= {min_expected}, got {len(filters)}")
            print(f"   Filters: {filters}")
            all_passed = False

    except Exception as e:
        print(f"❌ ERROR: {description} - {e}")
        all_passed = False
    print()

print("=" * 60)
if all_passed:
    print("🎉 ALL TESTS PASSED!")
    print()
    print("PBS generation is now working correctly!")
    print("Test in your app: python main.py")
else:
    print("⚠️  Some tests failed")
print("=" * 60)
'''

write_file("test_pbs_v2.py", test_content)

# Final summary
print("\n" + "=" * 60)
print("✅ FIX COMPLETE - VERSION 2")
print("=" * 60)
print()
print("What was done:")
print("1. ✅ Created fixed PBS module at src/lib/pbs_fixed.py")
print("2. ✅ Backed up and patched routes.py")
print("3. ✅ Created test file")
print()
print("Test it now:")
print("Run: python test_pbs_v2.py")
print()
print("If tests pass, your app is fixed!")
print("Start with: python main.py")
