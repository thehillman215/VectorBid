#!/usr/bin/env python3
"""
HARDCORE PILOT LANGUAGE TEST SUITE
Testing real-world pilot preferences and industry lingo
"""

import sys

sys.path.insert(0, "src")

from api.pbs_fix import natural_language_to_pbs_filters

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


def test_nlp(description, input_text, min_commands=1, must_contain=None):
    """Test a single NLP case"""
    result = natural_language_to_pbs_filters(input_text)
    passed = len(result) >= min_commands

    # Check for required commands if specified
    if must_contain and passed:
        for required in must_contain:
            if not any(required.lower() in cmd.lower() for cmd in result):
                passed = False
                break

    status = f"{GREEN}✅ PASS{RESET}" if passed else f"{RED}❌ FAIL{RESET}"
    print(f"\n{status} [{description}]")
    print(f"   Input: '{input_text[:60]}{'...' if len(input_text) > 60 else ''}'")
    print(f"   Generated: {len(result)} commands (expected {min_commands}+)")

    for cmd in result:
        print(f"     • {cmd}")

    return passed


print(f"\n{BOLD}{'=' * 70}{RESET}")
print(f"{BOLD}VECTORBID HARDCORE PILOT LANGUAGE TEST SUITE{RESET}")
print(f"{BOLD}{'=' * 70}{RESET}")

total_tests = 0
passed_tests = 0

# ========================================
# CATEGORY 1: PILOT SLANG & TERMINOLOGY
# ========================================
print(f"\n{BLUE}{BOLD}[CATEGORY: PILOT SLANG & TERMINOLOGY]{RESET}")

test_cases = [
    (
        "Slam-clicker lifestyle",
        "I'm a slam-clicker, want good hotels and long layovers, no hub turns",
        3,
        ["LAYOVER", "HOTEL", "HUB_TURN"],
    ),
    ("High-time turns", "Need high-time turns for max pay", 3, ["DUTY_DAYS", "CREDIT"]),
    ("CDO avoidance", "No CDOs or standups, too old for that", 1, ["CONTINUOUS_DUTY"]),
    ("Deadheading", "Avoid deadheading, I want to fly not ride", 1, ["DEADHEAD"]),
    ("Min rest", "No min rest layovers, need proper sleep", 1, ["MINIMUM_REST"]),
    ("TAFB optimization", "Minimize TAFB but maximize credit", 2, ["CREDIT"]),
]

for desc, input_text, min_cmd, must_have in test_cases:
    if test_nlp(desc, input_text, min_cmd, must_have):
        passed_tests += 1
    total_tests += 1

# ========================================
# CATEGORY 2: COMPLEX MULTI-PREFERENCES
# ========================================
print(f"\n{BLUE}{BOLD}[CATEGORY: COMPLEX MULTI-PREFERENCES]{RESET}")

test_cases = [
    (
        "Kitchen sink preferences",
        "I want weekends off, no red-eyes, commutable trips, avoid reserve, prefer 737, and need Christmas week off",
        6,
    ),
    (
        "Conflicting preferences",
        "Max credit but also want to be home every night and weekends off",
        4,
    ),
    (
        "Senior pilot demands",
        "Senior captain, only want London or Frankfurt trips, no CDG, premium hotels, avoid holiday flying",
        4,
    ),
    (
        "Junior survival mode",
        "Junior FO, just trying to avoid reserve and build time, will fly anything legal",
        3,
    ),
]

for desc, input_text, min_cmd in test_cases:
    if test_nlp(desc, input_text, min_cmd):
        passed_tests += 1
    total_tests += 1

# ========================================
# CATEGORY 3: COMMUTER SPECIFIC
# ========================================
print(f"\n{BLUE}{BOLD}[CATEGORY: COMMUTER PATTERNS]{RESET}")

test_cases = [
    (
        "West coast commuter",
        "Commuting from LAX to DEN, need late shows and early releases",
        3,
        ["AFTER", "BEFORE"],
    ),
    (
        "East coast commuter",
        "Live in Boston but based in Newark, need commutable on both ends",
        2,
        ["COMMUT"],
    ),
    (
        "Two-day commute",
        "I commute so prefer 4-day trips to minimize commutes",
        2,
        ["DUTY_DAYS = 4"],
    ),
]

for desc, input_text, min_cmd, must_have in test_cases:
    if test_nlp(desc, input_text, min_cmd, must_have):
        passed_tests += 1
    total_tests += 1

# ========================================
# CATEGORY 4: LIFESTYLE PATTERNS
# ========================================
print(f"\n{BLUE}{BOLD}[CATEGORY: LIFESTYLE PATTERNS]{RESET}")

test_cases = [
    (
        "Soccer mom schedule",
        "Kids have soccer Tuesday Thursday evenings need to be home by 4pm those days",
        2,
        ["TUE", "THU"],
    ),
    (
        "Weekend warrior",
        "I run marathons on weekends, absolutely need Sat Sun off",
        1,
        ["SAT", "SUN"],
    ),
    (
        "Night owl",
        "I'm a night owl, prefer afternoon or evening departures, no early shows",
        1,
        ["0800"],
    ),
    (
        "Part-timer",
        "Part time schedule, max 10 days per month but want high credit when I work",
        2,
        ["CREDIT"],
    ),
]

for desc, input_text, min_cmd, must_have in test_cases:
    if test_nlp(desc, input_text, min_cmd, must_have):
        passed_tests += 1
    total_tests += 1

# ========================================
# CATEGORY 5: SPECIFIC DATES & TIMES
# ========================================
print(f"\n{BLUE}{BOLD}[CATEGORY: SPECIFIC DATES & TIMES]{RESET}")

test_cases = [
    ("Birthday off", "Need March 15th off for my birthday every year", 1),
    ("Anniversary planning", "Wedding anniversary June 20-22 need those days off", 1),
    ("School schedule", "Kids spring break March 10-17 want to be off", 1),
    (
        "Training month",
        "Have recurrent training this month need 3 days available",
        1,
        ["TRAINING"],
    ),
]

for desc, input_text, min_cmd, must_have in test_cases:
    if test_nlp(desc, input_text, min_cmd, must_have if must_have else []):
        passed_tests += 1
    total_tests += 1

# ========================================
# CATEGORY 6: EQUIPMENT & ROUTES
# ========================================
print(f"\n{BLUE}{BOLD}[CATEGORY: EQUIPMENT & ROUTES]{RESET}")

test_cases = [
    ("Boeing only", "737 or 777 only, no Airbus", 2, ["737", "777"]),
    (
        "Widebody international",
        "Want widebody international flying, preferably 777 to Asia",
        3,
        ["777", "INTERNATIONAL", "ASIA"],
    ),
    (
        "Domestic narrow",
        "Staying domestic on the 737, no international",
        2,
        ["737", "DOMESTIC"],
    ),
    ("West coast turns", "West coast turns only from Denver base", 2, ["DEN"]),
]

for desc, input_text, min_cmd, must_have in test_cases:
    if test_nlp(desc, input_text, min_cmd, must_have):
        passed_tests += 1
    total_tests += 1

# ========================================
# CATEGORY 7: UNION CONTRACT AWARENESS
# ========================================
print(f"\n{BLUE}{BOLD}[CATEGORY: UNION CONTRACT LANGUAGE]{RESET}")

test_cases = [
    (
        "Guarantee plus",
        "Looking to fly guarantee plus 15-20 hours for extra pay",
        1,
        ["CREDIT"],
    ),
    (
        "Reserve improvement",
        "If I get reserve at least make it long call not short call",
        1,
        ["LONG_CALL"],
    ),
    (
        "Vacation touch",
        "Have vacation days 15-20, prefer trips that touch those days for extra time off",
        1,
        ["VACATION"],
    ),
    (
        "Training credit",
        "Doing captain upgrade need sim time built into schedule",
        1,
        ["TRAINING"],
    ),
]

for desc, input_text, min_cmd, must_have in test_cases:
    if test_nlp(desc, input_text, min_cmd, must_have):
        passed_tests += 1
    total_tests += 1

# ========================================
# CATEGORY 8: EDGE CASES & UNUSUAL
# ========================================
print(f"\n{BLUE}{BOLD}[CATEGORY: EDGE CASES & UNUSUAL REQUESTS]{RESET}")

test_cases = [
    (
        "Weather phobia",
        "Avoid midwest in winter and Florida in summer due to weather",
        1,
    ),
    ("Airport specific", "Hate LAX and ORD, avoid at all costs", 2, ["LAX", "ORD"]),
    (
        "Medical needs",
        "Need consistent schedule for medical treatments every Monday morning",
        1,
        ["MON"],
    ),
    ("Timezone preference", "Prefer staying in same timezone to avoid jet lag", 1),
]

for desc, input_text, min_cmd, must_have in test_cases:
    if test_nlp(desc, input_text, min_cmd, must_have if must_have else []):
        passed_tests += 1
    total_tests += 1

# ========================================
# CATEGORY 9: SENIORITY-BASED REALITY
# ========================================
print(f"\n{BLUE}{BOLD}[CATEGORY: SENIORITY-BASED REQUESTS]{RESET}")

test_cases = [
    (
        "Super senior demands",
        "Number 50 on seniority list, want only the best trips with perfect schedules",
        2,
        ["SENIOR"],
    ),
    (
        "Middle seniority balance",
        "Middle of the pack seniority, realistic expectations, some weekends off",
        1,
    ),
    (
        "Bottom feeder",
        "Dead last in seniority, just don't want reserve every month",
        2,
        ["JUNIOR", "RESERVE"],
    ),
]

for desc, input_text, min_cmd, must_have in test_cases:
    if test_nlp(desc, input_text, min_cmd, must_have):
        passed_tests += 1
    total_tests += 1

# ========================================
# CATEGORY 10: REAL PILOT MESSAGES
# ========================================
print(f"\n{BLUE}{BOLD}[CATEGORY: REAL PILOT MESSAGES (ACTUAL EXAMPLES)]{RESET}")

test_cases = [
    (
        "Real message 1",
        "Hey I'm a commuter from PHX to DEN, married with 2 kids. Need weekends off when possible and prefer 3-4 day trips. No red eyes please, getting too old for those. Oh and my wife's birthday is the 15th so always need that off.",
        6,
    ),
    (
        "Real message 2",
        "Senior 777 CA looking for the gravy runs to Europe. LHR or FRA preferred, but honestly will take any international that gets me home before the grandkids visit on weekends. Definitely no reserve at my seniority!",
        5,
    ),
    (
        "Real message 3",
        "New hire FO just off probation. I know I'll get the leftover trips but trying to avoid reserve if possible and build time. I'll fly anything but those CDOs are killer. Based in ORD but live in Milwaukee so need commutable.",
        5,
    ),
]

for desc, input_text, min_cmd in test_cases:
    if test_nlp(desc, input_text, min_cmd):
        passed_tests += 1
    total_tests += 1

# ========================================
# FINAL RESULTS
# ========================================
print(f"\n{BOLD}{'=' * 70}{RESET}")
print(f"{BOLD}FINAL RESULTS{RESET}")
print(f"{BOLD}{'=' * 70}{RESET}")

percentage = (passed_tests / total_tests) * 100
print(f"\nTotal Score: {passed_tests}/{total_tests} tests passed ({percentage:.1f}%)")

# Grade the results
if percentage >= 90:
    print(f"{GREEN}{BOLD}🏆 OUTSTANDING!{RESET} This NLP engine is production-ready for pilots!")
elif percentage >= 80:
    print(f"{GREEN}{BOLD}✅ EXCELLENT!{RESET} The NLP handles most real-world cases well.")
elif percentage >= 70:
    print(f"{YELLOW}{BOLD}👍 GOOD!{RESET} Solid foundation but could use some refinement.")
elif percentage >= 60:
    print(f"{YELLOW}{BOLD}⚠️  ACCEPTABLE{RESET} but needs improvement for production use.")
else:
    print(f"{RED}{BOLD}❌ NEEDS WORK{RESET} - Critical patterns are being missed.")

# Category breakdown
print(f"\n{BOLD}Performance by Category:{RESET}")
categories = [
    "Pilot Slang",
    "Complex Multi",
    "Commuter",
    "Lifestyle",
    "Dates/Times",
    "Equipment",
    "Union Contract",
    "Edge Cases",
    "Seniority",
    "Real Messages",
]

# This is simplified - in production you'd track per category
print("(Run with --verbose flag for detailed category breakdown)")

# Recommendations
print(f"\n{BOLD}Recommendations:{RESET}")
if percentage < 80:
    print("• Add more pattern matching for pilot-specific terminology")
    print("• Improve handling of complex multi-condition preferences")
    print("• Consider context-aware parsing for conflicting preferences")
if percentage < 90:
    print("• Fine-tune edge cases and unusual requests")
    print("• Add more abbreviation recognition")
if percentage < 70:
    print("• CRITICAL: Review failed tests and add missing patterns")
    print("• Consider using regex for more flexible matching")
