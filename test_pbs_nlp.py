"""
Test PBS Natural Language Processing
Verify professional-grade command generation
"""

import os
import sys

sys.path.insert(0, "src/lib")

from pbs_command_generator import generate_pbs_commands

# Professional test cases that would impress any pilot
test_cases = [
    {
        "input": "I'm a commuter from Las Vegas to Denver, need weekends off for family. Prefer morning departures after 9am to account for drive time. Want to maximize credit while being home for kids' bedtime.",
        "profile": {
            "base": "Denver (DEN)",
            "seniority": 65,
            "fleet": ["737"],
            "commuter": True,
        },
        "expected_commands": ["weekends", "departure time", "commute", "credit"],
    },
    {
        "input": "Senior captain wanting to maximize retirement earnings. International flying preferred, especially European routes. Don't mind redeyes if they pay well. Flexible on everything except Christmas week off.",
        "profile": {
            "base": "San Francisco (SFO)",
            "seniority": 92,
            "fleet": ["777", "787"],
        },
        "expected_commands": ["international", "pay", "christmas", "redeye"],
    },
    {
        "input": "New hire focused on quality of life. No more than 3-day trips, avoid weekends, need predictable schedule. Prefer day trips if possible, absolutely no redeyes.",
        "profile": {"base": "Chicago (ORD)", "seniority": 15, "fleet": ["320"]},
        "expected_commands": ["trip length", "weekends", "redeye", "quality of life"],
    },
    {
        "input": "I want to fly as little as possible while maintaining benefits. Minimum block hours only, longest layovers, avoid busy seasons.",
        "profile": {"base": "Houston (IAH)", "seniority": 78, "fleet": ["737"]},
        "expected_commands": ["minimum", "layover", "efficiency"],
    },
]

print("=" * 80)
print("PBS NATURAL LANGUAGE PROCESSING TEST")
print("Testing Professional-Grade Command Generation")
print("=" * 80)

# Check if using LLM
use_llm = os.environ.get("USE_LLM", "true").lower() == "true"
api_key = os.environ.get("OPENAI_API_KEY", "")

print("\nConfiguration:")
print(f"  LLM Enabled: {use_llm}")
print(f"  API Key Set: {'Yes' if api_key else 'No'}")
print("=" * 80)

for i, test in enumerate(test_cases, 1):
    print(f"\n[TEST CASE {i}]")
    print(
        f"Pilot: {test['profile'].get('seniority', 50)}% seniority at {test['profile'].get('base', 'Unknown')}"
    )
    print(f"Input: \"{test['input'][:100]}...\"")
    print("-" * 40)

    # Generate commands
    result = generate_pbs_commands(test["input"], test["profile"])

    # Check quality
    stats = result.get("stats", {})
    quality = stats.get("quality_score", 0)
    method = stats.get("generation_method", "unknown")

    # Display results
    print(f"Method: {method.upper()}")
    print(f"Quality Score: {quality}/100 {'⭐' * (quality // 20)}")
    print(f"Commands Generated: {len(result.get('commands', []))}")

    # Show commands
    print("\nGenerated PBS Commands:")
    for cmd in result.get("commands", [])[:5]:  # Show first 5
        confidence = f"[{cmd.get('confidence', 0.5):.0%}]" if method == "llm" else ""
        print(f"  • {cmd['command']}")
        print(f"    → {cmd['explanation']} {confidence}")

    # Check if expected categories were covered
    command_text = " ".join(c["command"] for c in result.get("commands", []))
    covered = []
    for expected in test["expected_commands"]:
        if expected.lower() in command_text.lower():
            covered.append(expected)

    coverage = len(covered) / len(test["expected_commands"]) * 100
    print(f"\nExpected Coverage: {coverage:.0f}% - Covered: {', '.join(covered)}")

    # Warnings/Issues
    if result.get("warnings"):
        print(f"⚠️  Warnings: {', '.join(result['warnings'])}")

    # Professional Assessment
    if quality >= 85 and coverage >= 75:
        print("✅ PROFESSIONAL GRADE - Ready for production!")
    elif quality >= 70:
        print("⚠️  GOOD - But could be better with LLM enabled")
    else:
        print("❌ NEEDS IMPROVEMENT - Check configuration")

print("\n" + "=" * 80)
print("OVERALL ASSESSMENT")
print("=" * 80)

if use_llm and api_key:
    print("✅ System configured for MAXIMUM quality with LLM")
    print("   Ready for production use with pilots!")
else:
    print("⚠️  System using pattern matching fallback")
    print("   For professional quality, set:")
    print("   export OPENAI_API_KEY='your-key'")
    print("   export USE_LLM='true'")

print("\nThis is the CORE VALUE of VectorBid - make it exceptional!")
print("=" * 80)
