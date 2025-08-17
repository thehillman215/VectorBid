#!/usr/bin/env python3
"""Quick test for VectorBid NLP - no dependencies needed"""

# Add src to path
import sys

sys.path.insert(0, "src")

# Import the function
try:
    from api.pbs_fix import natural_language_to_pbs_filters

    print("✅ Imported from pbs_fix")
except:
    print("❌ Could not import from pbs_fix")
    sys.exit(1)

# Test cases
tests = [
    ("I want weekends off", 1),
    ("No early morning departures", 1),
    ("I need commutable trips, no red-eyes, and max credit", 3),
    ("Family first - home every night if possible", 2),
    ("No red-eyes or early departures, prefer 3-day trips", 3),
]

print("\n" + "=" * 50)
print("VECTORBID NLP TEST")
print("=" * 50)

passed = 0
total = len(tests)

for input_text, expected_min in tests:
    result = natural_language_to_pbs_filters(input_text)
    count = len(result)

    if count >= expected_min:
        print(f"✅ PASS: '{input_text[:30]}...'")
        print(f"   Generated {count} commands")
        passed += 1
    else:
        print(f"❌ FAIL: '{input_text[:30]}...'")
        print(f"   Expected: {expected_min}+ commands")
        print(f"   Got: {count} commands")

    # Show the commands
    for cmd in result:
        print(f"     • {cmd}")
    print()

# Summary
print("=" * 50)
print(f"SCORE: {passed}/{total} passed ({passed/total*100:.0f}%)")

if passed == total:
    print("🎉 PERFECT! NLP is working great!")
elif passed >= 3:
    print("✅ GOOD! NLP is mostly working")
else:
    print("⚠️  NEEDS WORK - Update pbs_fix.py with enhanced version")
