#!/usr/bin/env python3
"""
Test script for PBS generation fix
Run: python test_pbs_fix.py
"""

import sys
sys.path.insert(0, '.')

from src.api.pbs_fix import natural_language_to_pbs_filters

# Test cases
test_cases = [
    ("I want weekends off and no early departures", 2),
    ("Short trips only with no red-eyes", 2),
    ("International flying with long layovers", 2),
    ("Commutable trips starting late", 1),
    ("Maximum days off with weekends free", 2),
    ("Avoid the 15th and 20th for family events", 2),
    ("", 1),  # Empty input
    ("Just give me a good schedule", 1),  # Generic input
]

print("Testing PBS Natural Language Processing")
print("=" * 50)

all_passed = True
for input_text, expected_count in test_cases:
    filters = natural_language_to_pbs_filters(input_text)
    passed = len(filters) >= expected_count

    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: '{input_text[:30]}...' → {len(filters)} filters (expected >= {expected_count})")

    if not passed:
        all_passed = False
        print(f"  Generated: {filters}")

print("=" * 50)
if all_passed:
    print("✅ All tests passed! PBS generation is working correctly.")
else:
    print("❌ Some tests failed. Check the implementation.")
