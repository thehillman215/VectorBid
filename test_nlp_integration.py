#!/usr/bin/env python3

# Test cases for VectorBid NLP
TEST_CASES = [
    {"input": "I want weekends off", "expected": 2},
    {"input": "No early morning departures", "expected": 1},
    {"input": "I need commutable trips, no red-eyes, and max credit", "expected": 3},
    {"input": "Family first - home every night if possible", "expected": 2},
    {"input": "No red-eyes or early departures, prefer 3-day trips", "expected": 3},
]


def test_nlp():
    print("Testing VectorBid NLP")
    print("=" * 50)

    # Try to import the function
    try:
        from src.api.pbs_fix import natural_language_to_pbs_filters

        print("Imported from pbs_fix")
    except:
        try:
            from src.api.routes import natural_language_to_pbs_filters

            print("Imported from routes")
        except:
            print("ERROR: Could not import natural_language_to_pbs_filters")
            print("Check that it exists in src/api/pbs_fix.py or src/api/routes.py")
            return

    # Run tests
    total = len(TEST_CASES)
    passed = 0

    for test in TEST_CASES:
        result = natural_language_to_pbs_filters(test["input"])
        num_commands = len(result)

        if num_commands >= test["expected"]:
            print(f"PASS: '{test['input'][:30]}...' -> {num_commands} commands")
            passed += 1
        else:
            print(f"FAIL: '{test['input'][:30]}...'")
            print(f"  Expected: {test['expected']} commands")
            print(f"  Got: {num_commands} commands")
            print(f"  Commands: {result}")

    # Summary
    print("=" * 50)
    print(f"Results: {passed}/{total} passed")
    score = (passed / total) * 100
    print(f"Score: {score:.0f}%")

    if score >= 80:
        print("SUCCESS: NLP is working well!")
    elif score >= 60:
        print("WARNING: NLP needs improvement")
    else:
        print("CRITICAL: NLP has major issues")


if __name__ == "__main__":
    test_nlp()
