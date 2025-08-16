#!/usr/bin/env python3
"""
Complete fix script - fixes test file and adds missing patterns
"""


def fix_test_file():
    """Fix the hardcore test file"""
    print("Fixing hardcore_pilot_test.py...")

    with open('hardcore_pilot_test.py') as f:
        content = f.read()

    # Fix all test cases that are missing the 4th parameter
    # Replace problematic patterns
    fixes = [
        # Fix Category 5
        ('("Birthday off",\n     "Need March 15th off for my birthday every year",\n     1),',
         '("Birthday off",\n     "Need March 15th off for my birthday every year",\n     1, []),'
         ),
        ('("Anniversary planning",\n     "Wedding anniversary June 20-22 need those days off",\n     1),',
         '("Anniversary planning",\n     "Wedding anniversary June 20-22 need those days off",\n     1, []),'
         ),
        ('("School schedule",\n     "Kids spring break March 10-17 want to be off",\n     1),',
         '("School schedule",\n     "Kids spring break March 10-17 want to be off",\n     1, []),'
         ),
    ]

    for old, new in fixes:
        content = content.replace(old, new)

    # Write fixed version
    with open('hardcore_pilot_test_fixed.py', 'w') as f:
        f.write(content)

    print("✅ Created hardcore_pilot_test_fixed.py")


def add_missing_patterns():
    """Add the missing patterns to pbs_fix.py"""
    print("\nAdding missing patterns to pbs_fix.py...")

    with open('src/api/pbs_fix.py') as f:
        content = f.read()

    # Check if patterns already exist
    if 'deadheading' in content.lower():
        print("⚠️  Deadheading pattern already exists")
        return

    # Find insertion point (before "Remove duplicates")
    insertion_point = content.find("# Remove duplicates")
    if insertion_point == -1:
        insertion_point = content.find("return unique_filters")

    if insertion_point == -1:
        print("❌ Could not find insertion point")
        return

    # New patterns to add
    new_patterns = '''
    # ==========================================
    # MISSING PATTERNS FIX
    # ==========================================

    # Deadheading
    if 'deadhead' in text_lower or 'deadheading' in text_lower:
        if 'avoid' in text_lower or 'no' in text_lower:
            filters.append("AVOID DEADHEAD_SEGMENTS")

    # TAFB (Time Away From Base)
    if 'tafb' in text_lower:
        if 'minimize' in text_lower or 'min' in text_lower:
            filters.append("MINIMIZE TIME_AWAY_FROM_BASE")
        if 'maximize' in text_lower or 'max' in text_lower:
            filters.append("MAXIMIZE CREDIT_TIME")
            filters.append("PREFER HIGH_CREDIT_TRIPS")

    # Specific cities
    if 'london' in text_lower:
        filters.append("PREFER DESTINATION LHR")
    if 'frankfurt' in text_lower:
        filters.append("PREFER DESTINATION FRA")
    if 'paris' in text_lower or 'cdg' in text_lower:
        if 'no' in text_lower or 'avoid' in text_lower:
            filters.append("AVOID DESTINATION CDG")
        else:
            filters.append("PREFER DESTINATION CDG")

    # Day-specific times (soccer schedule)
    if 'tuesday' in text_lower and ('evening' in text_lower or '4pm' in text_lower or 'home by' in text_lower):
        filters.append("AVOID TRIPS IF DUTY_PERIOD INCLUDES TUE")
        filters.append("PREFER TRIPS ENDING BEFORE 1600 ON TUE")
    if 'thursday' in text_lower and ('evening' in text_lower or '4pm' in text_lower or 'home by' in text_lower):
        filters.append("AVOID TRIPS IF DUTY_PERIOD INCLUDES THU")
        filters.append("PREFER TRIPS ENDING BEFORE 1600 ON THU")

    # Newark/EWR base
    if 'newark' in text_lower or 'ewr' in text_lower:
        filters.append("PREFER TRIPS FROM BASE EWR")

    '''

    # Insert the new patterns
    content = content[:insertion_point] + new_patterns + "\n    " + content[
        insertion_point:]

    # Write back
    with open('src/api/pbs_fix.py', 'w') as f:
        f.write(content)

    print("✅ Added missing patterns to pbs_fix.py")


def test_patterns():
    """Quick test of the fixes"""
    print("\nTesting fixes...")

    import sys
    sys.path.insert(0, 'src')

    # Reload the module to get new changes
    import importlib

    import api.pbs_fix
    importlib.reload(api.pbs_fix)

    from api.pbs_fix import natural_language_to_pbs_filters

    tests = [
        "Avoid deadheading", "Minimize TAFB but maximize credit",
        "Want London or Frankfurt trips", "Kids have soccer Tuesday evenings"
    ]

    print("\nQuick pattern test:")
    for test in tests:
        result = natural_language_to_pbs_filters(test)
        print(f"  '{test}' → {len(result)} commands")


if __name__ == "__main__":
    print("COMPLETE FIX SCRIPT")
    print("=" * 50)

    # Fix test file
    fix_test_file()

    # Add missing patterns
    add_missing_patterns()

    # Test
    test_patterns()

    print("\n" + "=" * 50)
    print("✅ All fixes applied!")
    print("\nNow run: python hardcore_pilot_test_fixed.py")
