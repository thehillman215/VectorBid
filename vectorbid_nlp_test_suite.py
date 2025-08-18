"""
VectorBid Natural Language Processing Test Suite
Testing the LLM's ability to understand pilot preferences and lingo
"""

import json
from datetime import datetime

# ================================================================================
# COMPREHENSIVE TEST CASES - PILOT LANGUAGE & PREFERENCES
# ================================================================================

PILOT_TEST_CASES = [
    # === BASIC PREFERENCES ===
    {
        "id": "basic_1",
        "input": "I want weekends off",
        "expected_commands": ["AVOID TRIPS IF DUTY_PERIOD OVERLAPS SAT OR SUN"],
        "category": "Basic",
    },
    {
        "id": "basic_2",
        "input": "No early morning departures",
        "expected_commands": ["AVOID TRIPS STARTING BEFORE 0800"],
        "category": "Basic",
    },
    # === PILOT LINGO - COMMON TERMS ===
    {
        "id": "lingo_1",
        "input": "I need commutable trips, no red-eyes, and max credit",
        "expected_commands": [
            "PREFER TRIPS STARTING AFTER 1000",
            "AVOID TRIPS WITH DEPARTURE_TIME BETWEEN 2200 AND 0559",
            "MAXIMIZE CREDIT_TIME",
        ],
        "category": "Pilot Lingo",
    },
    {
        "id": "lingo_2",
        "input": "Give me high-time turns with good per diem",
        "expected_commands": [
            "PREFER TRIPS WITH DUTY_DAYS = 1",
            "MAXIMIZE CREDIT_TIME",
            "MAXIMIZE PER_DIEM_VALUE",
        ],
        "category": "Pilot Lingo",
    },
    {
        "id": "lingo_3",
        "input": "I'm a slam-clicker who wants easy layovers and no hub turns",
        "expected_commands": [
            "PREFER LAYOVERS WITH DURATION >= 14 HOURS",
            "AVOID HUB_TURNS",
            "PREFER TRIPS WITH GOOD_HOTELS",
        ],
        "category": "Pilot Lingo",
    },
    # === SENIORITY-BASED PREFERENCES ===
    {
        "id": "senior_1",
        "input": "Senior pilot - want prime time off, holiday avoidance, best equipment",
        "expected_commands": [
            "AVOID TRIPS DURING HOLIDAYS",
            "PREFER WEEKDAYS OFF",
            "PREFER EQUIPMENT TYPE 777 OR 787",
        ],
        "category": "Seniority",
    },
    {
        "id": "junior_1",
        "input": "Junior guy here - just need to build time and avoid reserve",
        "expected_commands": [
            "MAXIMIZE BLOCK_TIME",
            "AVOID RESERVE_ASSIGNMENTS",
            "ACCEPT ANY_LEGAL_TRIP",
        ],
        "category": "Seniority",
    },
    # === LIFESTYLE PREFERENCES ===
    {
        "id": "lifestyle_1",
        "input": "Family first - home every night if possible, no overnights on school nights",
        "expected_commands": [
            "PREFER DAY_TRIPS",
            "AVOID OVERNIGHTS MON THROUGH THU",
            "MINIMIZE TIME_AWAY_FROM_BASE",
        ],
        "category": "Lifestyle",
    },
    {
        "id": "lifestyle_2",
        "input": "Commuter from LAX to DEN base - need late shows and early releases",
        "expected_commands": [
            "PREFER TRIPS STARTING AFTER 1200",
            "PREFER TRIPS ENDING BEFORE 1500",
            "AVOID EARLY_MORNING_DEPARTURES",
            "AVOID LATE_NIGHT_ARRIVALS",
        ],
        "category": "Lifestyle",
    },
    {
        "id": "lifestyle_3",
        "input": "Part-timer looking for minimum days with maximum pay",
        "expected_commands": [
            "MINIMIZE DUTY_DAYS",
            "MAXIMIZE CREDIT_PER_DAY",
            "PREFER TRIPS WITH DAYS <= 10 PER MONTH",
        ],
        "category": "Lifestyle",
    },
    # === COMPLEX MULTI-PREFERENCE ===
    {
        "id": "complex_1",
        "input": "I want weekends off, no red-eyes, prefer 3-day trips, and need Fridays at home for family commitments",
        "expected_commands": [
            "AVOID TRIPS IF DUTY_PERIOD OVERLAPS SAT OR SUN",
            "AVOID TRIPS WITH DEPARTURE_TIME BETWEEN 2200 AND 0559",
            "PREFER TRIPS WITH DUTY_DAYS = 3",
            "AVOID TRIPS IF DUTY_PERIOD INCLUDES FRI",
        ],
        "category": "Complex",
    },
    {
        "id": "complex_2",
        "input": "Senior captain wants Europe trips, avoid CDG, prefer LHR or FRA, no back-to-back atlantics",
        "expected_commands": [
            "PREFER INTERNATIONAL_DESTINATIONS",
            "PREFER DESTINATIONS INCLUDE LHR OR FRA",
            "AVOID DESTINATION CDG",
            "AVOID CONSECUTIVE_ATLANTIC_CROSSINGS",
        ],
        "category": "Complex",
    },
    # === EQUIPMENT & ROUTE PREFERENCES ===
    {
        "id": "equipment_1",
        "input": "737 only, no MAX variants please",
        "expected_commands": [
            "PREFER EQUIPMENT TYPE 737",
            "AVOID EQUIPMENT TYPE 737MAX",
        ],
        "category": "Equipment",
    },
    {
        "id": "routes_1",
        "input": "West coast flying only, avoid transcons",
        "expected_commands": [
            "PREFER DESTINATIONS WEST_COAST",
            "AVOID TRANSCONTINENTAL_FLIGHTS",
        ],
        "category": "Routes",
    },
    # === SPECIFIC AIRLINE TERMINOLOGY ===
    {
        "id": "airline_1",
        "input": "No continuous duty overnights (CDOs) or stand-ups",
        "expected_commands": [
            "AVOID CONTINUOUS_DUTY_OVERNIGHTS",
            "AVOID STANDUP_OVERNIGHTS",
        ],
        "category": "Airline Specific",
    },
    {
        "id": "airline_2",
        "input": "Prefer productivity runs and avoid min-rest layovers",
        "expected_commands": [
            "PREFER HIGH_PRODUCTIVITY_TRIPS",
            "AVOID LAYOVERS WITH REST < 10 HOURS",
        ],
        "category": "Airline Specific",
    },
    # === EDGE CASES & UNUSUAL REQUESTS ===
    {
        "id": "edge_1",
        "input": "I have a fear of flying over water - no ocean crossings",
        "expected_commands": ["AVOID OCEANIC_ROUTES", "AVOID INTERNATIONAL_OVER_WATER"],
        "category": "Edge Cases",
    },
    {
        "id": "edge_2",
        "input": "Birthday is March 15th - always want that day off",
        "expected_commands": ["AVOID TRIPS IF DUTY_PERIOD INCLUDES DATE 03/15"],
        "category": "Edge Cases",
    },
    # === ABBREVIATIONS & SHORTHAND ===
    {
        "id": "abbrev_1",
        "input": "Max block, min TAFB, no DH",
        "expected_commands": [
            "MAXIMIZE BLOCK_TIME",
            "MINIMIZE TIME_AWAY_FROM_BASE",
            "AVOID DEADHEAD_SEGMENTS",
        ],
        "category": "Abbreviations",
    },
    {
        "id": "abbrev_2",
        "input": "No JFK, EWR, or LGA - basically avoid NYC",
        "expected_commands": [
            "AVOID DESTINATION JFK",
            "AVOID DESTINATION EWR",
            "AVOID DESTINATION LGA",
        ],
        "category": "Abbreviations",
    },
    # === UNION & CONTRACT SPECIFIC ===
    {
        "id": "union_1",
        "input": "Want to maximize my 401k contributions - need high credit months",
        "expected_commands": [
            "MAXIMIZE MONTHLY_CREDIT",
            "PREFER CREDIT_TIME >= 85 HOURS",
        ],
        "category": "Union/Contract",
    },
    {
        "id": "union_2",
        "input": "Trying to hit guarantee plus 20",
        "expected_commands": ["TARGET CREDIT_TIME BETWEEN 95 AND 105 HOURS"],
        "category": "Union/Contract",
    },
]

# ================================================================================
# TEST EXECUTION FRAMEWORK
# ================================================================================


def run_nlp_test(test_case: dict, llm_function=None) -> dict:
    """
    Execute a single NLP test case
    Returns result with score and analysis
    """
    result = {
        "id": test_case["id"],
        "category": test_case["category"],
        "input": test_case["input"],
        "expected": test_case["expected_commands"],
        "actual": [],
        "score": 0,
        "passed": False,
        "missing_commands": [],
        "extra_commands": [],
        "analysis": "",
    }

    # If we have an LLM function, use it
    if llm_function:
        try:
            result["actual"] = llm_function(test_case["input"])
        except Exception as e:
            result["actual"] = []
            result["analysis"] = f"Error: {str(e)}"
            return result
    else:
        # Simulate for testing framework
        result["actual"] = simulate_llm_response(test_case["input"])

    # Score the result
    expected_set = set(test_case["expected_commands"])
    actual_set = set(result["actual"])

    # Calculate accuracy
    result["missing_commands"] = list(expected_set - actual_set)
    result["extra_commands"] = list(actual_set - expected_set)

    if expected_set == actual_set:
        result["score"] = 100
        result["passed"] = True
        result["analysis"] = "Perfect match!"
    else:
        # Partial credit calculation
        correct = len(expected_set & actual_set)
        total = len(expected_set | actual_set)
        result["score"] = int((correct / total * 100) if total > 0 else 0)
        result["passed"] = result["score"] >= 70  # 70% threshold

        if result["missing_commands"]:
            result["analysis"] = f"Missing: {', '.join(result['missing_commands'][:3])}"
        if result["extra_commands"]:
            result["analysis"] += f" Extra: {', '.join(result['extra_commands'][:3])}"

    return result


def simulate_llm_response(input_text: str) -> list[str]:
    """
    Simulate LLM response for testing framework
    In production, this would call your actual LLM
    """
    commands = []
    text_lower = input_text.lower()

    # Basic pattern matching for simulation
    if "weekend" in text_lower:
        commands.append("AVOID TRIPS IF DUTY_PERIOD OVERLAPS SAT OR SUN")
    if "early" in text_lower and ("no" in text_lower or "avoid" in text_lower):
        commands.append("AVOID TRIPS STARTING BEFORE 0800")
    if "red-eye" in text_lower or "redeye" in text_lower:
        commands.append("AVOID TRIPS WITH DEPARTURE_TIME BETWEEN 2200 AND 0559")
    if "commut" in text_lower:
        commands.append("PREFER TRIPS STARTING AFTER 1000")
    if "family" in text_lower:
        commands.append("PREFER DAY_TRIPS")
    if "credit" in text_lower and "max" in text_lower:
        commands.append("MAXIMIZE CREDIT_TIME")

    return commands if commands else ["PREFER TRIPS WITH GOOD_QUALITY_OF_LIFE"]


def run_full_test_suite(llm_function=None) -> dict:
    """
    Run the complete test suite and generate report
    """
    print("\n" + "=" * 80)
    print(" VECTORBID NATURAL LANGUAGE PROCESSING TEST SUITE")
    print(" Testing Pilot Preference Understanding")
    print("=" * 80)

    results = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": len(PILOT_TEST_CASES),
        "passed": 0,
        "failed": 0,
        "total_score": 0,
        "categories": {},
        "detailed_results": [],
    }

    # Run each test
    for test_case in PILOT_TEST_CASES:
        print(f"\n[{test_case['category']}] Testing: {test_case['id']}")
        print(
            f'  Input: "{test_case["input"][:60]}..."'
            if len(test_case["input"]) > 60
            else f'  Input: "{test_case["input"]}"'
        )

        result = run_nlp_test(test_case, llm_function)
        results["detailed_results"].append(result)

        # Update statistics
        if result["passed"]:
            results["passed"] += 1
            print(f"  ✅ PASSED (Score: {result['score']}/100)")
        else:
            results["failed"] += 1
            print(f"  ❌ FAILED (Score: {result['score']}/100)")
            print(f"     {result['analysis']}")

        results["total_score"] += result["score"]

        # Track by category
        category = test_case["category"]
        if category not in results["categories"]:
            results["categories"][category] = {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "avg_score": 0,
            }
        results["categories"][category]["total"] += 1
        if result["passed"]:
            results["categories"][category]["passed"] += 1
        else:
            results["categories"][category]["failed"] += 1

    # Calculate averages
    results["average_score"] = results["total_score"] / results["total_tests"]
    for category in results["categories"]:
        cat_scores = [
            r["score"] for r in results["detailed_results"] if r["category"] == category
        ]
        results["categories"][category]["avg_score"] = sum(cat_scores) / len(cat_scores)

    # Generate summary report
    print("\n" + "=" * 80)
    print(" TEST SUITE SUMMARY")
    print("=" * 80)
    print("\n📊 Overall Results:")
    print(f"  • Total Tests: {results['total_tests']}")
    print(
        f"  • Passed: {results['passed']} ({results['passed'] / results['total_tests'] * 100:.1f}%)"
    )
    print(f"  • Failed: {results['failed']}")
    print(f"  • Average Score: {results['average_score']:.1f}/100")

    print("\n📈 Results by Category:")
    for category, stats in results["categories"].items():
        print(f"\n  {category}:")
        print(f"    • Tests: {stats['total']}")
        print(
            f"    • Pass Rate: {stats['passed']}/{stats['total']} ({stats['passed'] / stats['total'] * 100:.1f}%)"
        )
        print(f"    • Avg Score: {stats['avg_score']:.1f}/100")

    # Identify problem areas
    print("\n⚠️  Problem Areas (Failed Tests):")
    failed_tests = [r for r in results["detailed_results"] if not r["passed"]]
    for test in failed_tests[:5]:  # Show top 5 failures
        print(f"  • {test['id']}: {test['input'][:40]}...")
        print(f"    Score: {test['score']}/100 - {test['analysis']}")

    # Final grade
    grade = (
        "A"
        if results["average_score"] >= 90
        else (
            "B"
            if results["average_score"] >= 80
            else (
                "C"
                if results["average_score"] >= 70
                else "D"
                if results["average_score"] >= 60
                else "F"
            )
        )
    )

    print(f"\n🎯 Final Grade: {grade} ({results['average_score']:.1f}%)")

    if results["average_score"] >= 90:
        print("   ⭐ EXCELLENT! The NLP system is production-ready!")
    elif results["average_score"] >= 70:
        print("   ✅ GOOD! The system handles most cases well.")
    else:
        print("   ⚠️  NEEDS IMPROVEMENT - Review failed test cases.")

    return results


# ================================================================================
# INTEGRATION HELPERS
# ================================================================================


def test_with_your_llm():
    """
    Example of how to integrate with your actual LLM function
    """

    # Import your actual function
    # from src.api.routes import natural_language_to_pbs_filters

    def llm_wrapper(input_text):
        """Wrapper to match expected interface"""
        # Call your actual function here
        # return natural_language_to_pbs_filters(input_text)

        # For now, return simulation
        return simulate_llm_response(input_text)

    # Run the full test suite
    results = run_full_test_suite(llm_function=llm_wrapper)

    # Save results to file
    with open("nlp_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n💾 Results saved to nlp_test_results.json")

    return results


# ================================================================================
# MAIN EXECUTION
# ================================================================================

if __name__ == "__main__":
    print("\n🚀 Starting VectorBid NLP Test Suite...")
    print("This will test the LLM's ability to understand pilot preferences.\n")

    # Run with simulation for demonstration
    results = run_full_test_suite()

    # Instructions for real testing
    print("\n" + "=" * 80)
    print(" HOW TO USE WITH YOUR ACTUAL LLM")
    print("=" * 80)
    print(
        """
1. Import your actual NLP function:
   from src.api.routes import natural_language_to_pbs_filters

2. Create a wrapper function that matches the expected interface:
   def llm_wrapper(input_text):
       return natural_language_to_pbs_filters(input_text)

3. Run the test suite:
   results = run_full_test_suite(llm_function=llm_wrapper)

4. Review the results and iterate on any failed tests.
    """
    )

    print("\n✨ Test suite complete!")
