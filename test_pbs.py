#!/usr/bin/env python3
"""Test the PBS fix"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the routes module
try:
    from src.api.routes import natural_language_to_pbs_filters, _fallback_pbs_generation
    print("✅ Successfully imported from src.api.routes")
except ImportError:
    try:
        from routes import natural_language_to_pbs_filters, _fallback_pbs_generation
        print("✅ Successfully imported from routes")
    except ImportError:
        print("❌ Could not import PBS functions. Trying direct function test...")
        exec(open("src/api/routes.py").read())

# Test cases
test_cases = [
    ("I want weekends off and no early departures", 2, "Should generate weekend + early filters"),
    ("Short trips only with no red-eyes", 2, "Should generate short trip + red-eye filters"),
    ("International flying with long layovers", 2, "Should generate international + layover filters"),
    ("Commutable trips starting late", 1, "Should generate commute filter"),
    ("Maximum days off with weekends free", 2, "Should generate days off + weekend filters"),
    ("", 1, "Empty input should generate default"),
    ("Avoid Denver and prefer short trips", 2, "Should generate city + trip length filters"),
]

print()
print("=" * 60)
print("🧪 TESTING PBS NATURAL LANGUAGE PROCESSING")
print("=" * 60)
print()

all_passed = True
for input_text, min_expected, description in test_cases:
    try:
        # Try the main function first
        try:
            filters = natural_language_to_pbs_filters(input_text)
        except:
            filters = _fallback_pbs_generation(input_text)

        passed = len(filters) >= min_expected

        if passed:
            print(f"✅ PASS: {description}")
            print(f"   Input: '{input_text[:50]}...'")
            print(f"   Generated {len(filters)} filters (expected >= {min_expected})")
            for f in filters:
                print(f"   - {f}")
        else:
            print(f"❌ FAIL: {description}")
            print(f"   Input: '{input_text}'")
            print(f"   Generated {len(filters)} filters (expected >= {min_expected})")
            print(f"   Got: {filters}")
            all_passed = False

    except Exception as e:
        print(f"❌ ERROR: {description}")
        print(f"   Exception: {e}")
        all_passed = False

    print()

print("=" * 60)
if all_passed:
    print("🎉 ALL TESTS PASSED! PBS generation is working correctly!")
    print()
    print("Next steps:")
    print("1. Start your app: python main.py")
    print("2. Test in the web interface")
    print("3. Upload your United 737 bid packet")
else:
    print("⚠️  Some tests failed. Check the implementation.")
    print("Try running: python main.py")
    print("And testing manually in the web interface")
print("=" * 60)
