#!/usr/bin/env python3
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
