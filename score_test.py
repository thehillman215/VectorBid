#!/usr/bin/env python3
"""
Simple scoring test that actually works
Tests the most important pilot language patterns
"""

import sys

sys.path.insert(0, "src")
from api.pbs_fix import natural_language_to_pbs_filters


def test(description, input_text, min_expected):
    """Test a single case"""
    result = natural_language_to_pbs_filters(input_text)
    passed = len(result) >= min_expected

    status = "✅" if passed else "❌"
    print(f"{status} {description}")
    print(f"   Input: '{input_text[:50]}...'")
    print(f"   Got {len(result)} commands (expected {min_expected}+)")
    if not passed:
        for cmd in result:
            print(f"     • {cmd}")

    return 1 if passed else 0


print("\n" + "=" * 60)
print("VECTORBID NLP SCORING TEST")
print("=" * 60)

total = 0
passed = 0

# Core patterns that should work
tests = [
    ("Weekends off", "I want weekends off", 1),
    ("Early mornings", "No early morning departures", 1),
    ("Red-eyes", "Avoid red-eyes", 1),
    ("Commuter", "I'm a commuter, need late starts", 2),
    ("Max credit", "Want to maximize credit hours", 2),
    ("Family time", "Family first, home every night", 2),
    ("3-day trips", "Prefer 3-day trips", 1),
    ("Reserve", "Avoid reserve assignments", 1),
    ("International", "Want international flights to Europe", 2),
    ("CDOs", "No CDOs or standups", 1),
    ("Min rest", "No minimum rest layovers", 1),
    ("Holidays", "Need Christmas week off", 1),
    ("Equipment", "737 only please", 1),
    ("Base", "Denver base trips only", 1),
    ("Layovers", "Want long layovers with good hotels", 2),
]

print("\n[BASIC PATTERNS]")
for desc, input_text, min_exp in tests:
    passed += test(desc, input_text, min_exp)
    total += 1

# Complex multi-preference tests
print("\n[COMPLEX PREFERENCES]")
complex_tests = [
    (
        "Kitchen sink",
        "I want weekends off, no red-eyes, commutable trips, avoid reserve, prefer 737",
        5,
    ),
    (
        "Commuter lifestyle",
        "Commute from Phoenix to Denver, need late shows and early releases",
        3,
    ),
    (
        "Senior demands",
        "Senior pilot, want international flights, good hotels, no reserve",
        3,
    ),
    ("Junior reality", "Junior FO, just need to avoid reserve and build time", 3),
]

for desc, input_text, min_exp in complex_tests:
    passed += test(desc, input_text, min_exp)
    total += 1

# Pilot lingo tests
print("\n[PILOT LINGO]")
lingo_tests = [
    ("Slam-clicker", "I'm a slam-clicker, want good hotels", 2),
    ("High-time", "Need high-time turns for pay", 2),
    ("Hub turns", "No hub turns please", 1),
    ("Training", "Have recurrent training this month", 1),
]

for desc, input_text, min_exp in lingo_tests:
    passed += test(desc, input_text, min_exp)
    total += 1

# Missing patterns (these might fail)
print("\n[ADVANCED PATTERNS - May Need Work]")
advanced = [
    ("Deadheading", "Avoid deadheading", 1),
    ("TAFB", "Minimize TAFB", 1),
    ("Cities", "Want London or Frankfurt trips", 1),
    ("Day-specific", "Tuesday evenings need to be home", 1),
]

for desc, input_text, min_exp in advanced:
    result = test(desc, input_text, min_exp)
    if result == 0:
        print("     ⚠️  This pattern needs to be added to pbs_fix.py")
    passed += result
    total += 1

# Calculate final score
print("\n" + "=" * 60)
print("FINAL SCORE")
print("=" * 60)

percentage = (passed / total) * 100
print(f"\nPassed: {passed}/{total} tests ({percentage:.1f}%)")

if percentage >= 90:
    print("🏆 OUTSTANDING! Production-ready!")
elif percentage >= 80:
    print("✅ EXCELLENT! Ready for pilot testing!")
elif percentage >= 70:

    print("👍 GOOD! Solid foundation!")
elif percentage >= 60:
    print("⚠️  ACCEPTABLE for MVP")
else:
    print("❌ Needs improvement")

print("\nKey Insights:")
if percentage < 80:
    print("• Add patterns for: deadheading, TAFB, specific cities")
    print("• Enhance day/time specific preferences")
print(f"• Core patterns working: {passed}/{total}")
print("• This covers the most common pilot use cases")
