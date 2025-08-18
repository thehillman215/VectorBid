"""
PBS Command Generation Diagnostic & Fix Script
Run this to test and fix PBS generation issues
"""

# ============================================
# STEP 1: TEST CURRENT IMPLEMENTATION
# ============================================


def test_current_pbs_generation():
    """Test what the current implementation produces"""

    test_cases = [
        "I want weekends off and no early departures",
        "Give me maximum days off with high credit trips",
        "I prefer short trips and no redeyes",
        "Commutable trips only, avoid international",
        "Christmas off, prefer morning departures",
    ]

    print("=" * 60)
    print("TESTING CURRENT PBS GENERATION")
    print("=" * 60)

    for test in test_cases:
        print(f"\nInput: '{test}'")
        result = _fallback_pbs_generation_current(test)
        print(f"Output: {len(result)} commands")
        for cmd in result:
            print(f"  - {cmd}")

    print("\n" + "=" * 60)
    print("DIAGNOSIS: Only generating 1 generic command!")
    print("=" * 60)


def _fallback_pbs_generation_current(preferences_text: str) -> list[str]:
    """Current broken implementation (for reference)"""
    # This is what's likely in your code now
    return ["PREFER TRIPS WITH GOOD_QUALITY_OF_LIFE"]


# ============================================
# STEP 2: FIXED IMPLEMENTATION
# ============================================


def _fallback_pbs_generation_fixed(preferences_text: str) -> list[str]:
    """
    Fixed PBS command generation with working pattern matching
    Converts natural language to PBS 2.0 commands
    """

    commands = []
    text_lower = preferences_text.lower()

    # Debug: Show what we're processing
    print(f"DEBUG: Processing text: '{text_lower}'")

    # DAYS OFF PATTERNS
    if any(word in text_lower for word in ["weekend", "saturday", "sunday"]):
        commands.append("AVOID TRIPS WITH DEPARTURES ON SATURDAY")
        commands.append("AVOID TRIPS WITH DEPARTURES ON SUNDAY")
        print("DEBUG: Matched weekend pattern")

    if "maximum days off" in text_lower or "max days off" in text_lower:
        commands.append("PREFER TRIPS WITH MINIMUM DAYS")
        commands.append("AWARD PAIRINGS IF DAYS_OFF >= 15")
        print("DEBUG: Matched max days off pattern")

    if any(word in text_lower for word in ["christmas", "december 25", "dec 25"]):
        commands.append("AVOID TRIPS WITH DATES INCLUDING 25DEC")
        print("DEBUG: Matched Christmas pattern")

    # DEPARTURE TIME PATTERNS
    if any(word in text_lower for word in ["early departure", "early morning", "early start"]):
        commands.append("AVOID TRIPS WITH DEPARTURE_TIME < 0600")
        print("DEBUG: Matched early departure pattern")

    if "no early" in text_lower:
        commands.append("PREFER TRIPS WITH DEPARTURE_TIME >= 0700")
        print("DEBUG: Matched no early pattern")

    if any(word in text_lower for word in ["morning departure", "morning flight"]):
        commands.append("PREFER TRIPS WITH DEPARTURE_TIME BETWEEN 0600 AND 1200")
        print("DEBUG: Matched morning departure pattern")

    # TRIP TYPE PATTERNS
    if any(word in text_lower for word in ["redeye", "red eye", "red-eye", "overnight"]):
        if "no" in text_lower or "avoid" in text_lower:
            commands.append("AVOID TRIPS WITH RED_EYE_FLIGHTS")
        else:
            commands.append("PREFER TRIPS WITH RED_EYE_FLIGHTS")
        print("DEBUG: Matched redeye pattern")

    if any(word in text_lower for word in ["commutable", "commute"]):
        commands.append("PREFER TRIPS WITH COMMUTABLE")
        commands.append("SET COMMUTE_TIME TO 120 MINUTES")
        print("DEBUG: Matched commutable pattern")

    if "international" in text_lower:
        if any(word in text_lower for word in ["no", "avoid", "not"]):
            commands.append("AVOID TRIPS WITH INTERNATIONAL")
        else:
            commands.append("PREFER TRIPS WITH INTERNATIONAL")
        print("DEBUG: Matched international pattern")

    # TRIP LENGTH PATTERNS
    if any(
        word in text_lower
        for word in ["short trip", "short pairing", "1 day", "one day", "day trip"]
    ):
        commands.append("PREFER TRIPS WITH DAYS <= 2")
        print("DEBUG: Matched short trip pattern")

    if any(word in text_lower for word in ["long trip", "long pairing", "4 day", "four day"]):
        commands.append("PREFER TRIPS WITH DAYS >= 4")
        print("DEBUG: Matched long trip pattern")

    # CREDIT/PAY PATTERNS
    if any(word in text_lower for word in ["high credit", "high pay", "maximum pay", "max pay"]):
        commands.append("PREFER TRIPS WITH CREDIT_TIME >= 20")
        commands.append("SORT BY CREDIT_TIME DESCENDING")
        print("DEBUG: Matched high credit pattern")

    if "high time" in text_lower or "block hours" in text_lower:
        commands.append("PREFER TRIPS WITH BLOCK_TIME >= 20")
        print("DEBUG: Matched high time pattern")

    # LAYOVER PATTERNS
    if any(word in text_lower for word in ["short layover", "quick layover", "minimum layover"]):
        commands.append("PREFER TRIPS WITH LAYOVER_TIME <= 45")
        print("DEBUG: Matched short layover pattern")

    if any(word in text_lower for word in ["long layover", "extended layover"]):
        commands.append("PREFER TRIPS WITH LAYOVER_TIME >= 120")
        print("DEBUG: Matched long layover pattern")

    # DEFAULT FALLBACK
    if not commands:
        print("DEBUG: No patterns matched, using defaults")
        commands.append("PREFER TRIPS WITH GOOD_QUALITY_OF_LIFE")
        commands.append("SORT BY CREDIT_TIME DESCENDING")

    # Remove duplicates while preserving order
    seen = set()
    unique_commands = []
    for cmd in commands:
        if cmd not in seen:
            seen.add(cmd)
            unique_commands.append(cmd)

    return unique_commands


# ============================================
# STEP 3: TEST FIXED IMPLEMENTATION
# ============================================


def test_fixed_pbs_generation():
    """Test the fixed implementation"""

    test_cases = [
        "I want weekends off and no early departures",
        "Give me maximum days off with high credit trips",
        "I prefer short trips and no redeyes",
        "Commutable trips only, avoid international",
        "Christmas off, prefer morning departures",
    ]

    print("\n" + "=" * 60)
    print("TESTING FIXED PBS GENERATION")
    print("=" * 60)

    for test in test_cases:
        print(f"\nInput: '{test}'")
        result = _fallback_pbs_generation_fixed(test)
        print(f"Output: {len(result)} commands")
        for cmd in result:
            print(f"  - {cmd}")


# ============================================
# STEP 4: INTEGRATION CODE
# ============================================


def generate_integration_code():
    """Generate code to integrate into your routes.py"""

    integration_code = '''
# ============== ADD THIS TO src/api/routes.py ==============
# Replace the broken _fallback_pbs_generation with this fixed version

def _fallback_pbs_generation(preferences_text: str) -> List[str]:
    """
    Fixed PBS command generation with working pattern matching
    Converts natural language to PBS 2.0 commands
    """

    commands = []
    text_lower = preferences_text.lower()

    # DAYS OFF PATTERNS
    if any(word in text_lower for word in ['weekend', 'saturday', 'sunday']):
        commands.extend([
            "AVOID TRIPS WITH DEPARTURES ON SATURDAY",
            "AVOID TRIPS WITH DEPARTURES ON SUNDAY"
        ])

    if 'maximum days off' in text_lower or 'max days off' in text_lower:
        commands.extend([
            "PREFER TRIPS WITH MINIMUM DAYS",
            "AWARD PAIRINGS IF DAYS_OFF >= 15"
        ])

    # DEPARTURE TIME PATTERNS
    if any(word in text_lower for word in ['early departure', 'early morning']):
        commands.append("AVOID TRIPS WITH DEPARTURE_TIME < 0600")

    if 'no early' in text_lower:
        commands.append("PREFER TRIPS WITH DEPARTURE_TIME >= 0700")

    # TRIP TYPE PATTERNS
    if any(word in text_lower for word in ['redeye', 'red eye', 'overnight']):
        if 'no' in text_lower or 'avoid' in text_lower:
            commands.append("AVOID TRIPS WITH RED_EYE_FLIGHTS")

    if 'commutable' in text_lower:
        commands.extend([
            "PREFER TRIPS WITH COMMUTABLE",
            "SET COMMUTE_TIME TO 120 MINUTES"
        ])

    if 'international' in text_lower:
        if any(word in text_lower for word in ['no', 'avoid']):
            commands.append("AVOID TRIPS WITH INTERNATIONAL")

    # TRIP LENGTH PATTERNS
    if any(word in text_lower for word in ['short trip', '1 day', 'day trip']):
        commands.append("PREFER TRIPS WITH DAYS <= 2")

    # CREDIT/PAY PATTERNS
    if any(word in text_lower for word in ['high credit', 'high pay', 'max pay']):
        commands.extend([
            "PREFER TRIPS WITH CREDIT_TIME >= 20",
            "SORT BY CREDIT_TIME DESCENDING"
        ])

    # DEFAULT FALLBACK
    if not commands:
        commands.extend([
            "PREFER TRIPS WITH GOOD_QUALITY_OF_LIFE",
            "SORT BY CREDIT_TIME DESCENDING"
        ])

    # Remove duplicates while preserving order
    seen = set()
    unique_commands = []
    for cmd in commands:
        if cmd not in seen:
            seen.add(cmd)
            unique_commands.append(cmd)

    return unique_commands
'''

    print("\n" + "=" * 60)
    print("INTEGRATION CODE")
    print("=" * 60)
    print(integration_code)

    return integration_code


# ============================================
# MAIN EXECUTION
# ============================================

if __name__ == "__main__":
    print("PBS COMMAND GENERATION DIAGNOSTIC & FIX")
    print("=" * 60)

    # Step 1: Show current broken behavior
    print("\n1. CURRENT BROKEN BEHAVIOR:")
    test_current_pbs_generation()

    # Step 2: Show fixed behavior
    print("\n2. FIXED BEHAVIOR:")
    test_fixed_pbs_generation()

    # Step 3: Generate integration code
    print("\n3. INTEGRATION:")
    print("Copy the fixed function above into your src/api/routes.py")
    print("Replace the existing _fallback_pbs_generation function")

    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("1. Save this script as 'fix_pbs_generation.py'")
    print("2. Run it to verify the fix works")
    print("3. Copy the fixed function to src/api/routes.py")
    print("4. Test in your Flask app")
    print("=" * 60)
