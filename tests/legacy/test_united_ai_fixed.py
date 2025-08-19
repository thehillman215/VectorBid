"""
Test Enhanced United Airlines LLM with Real OpenAI API - FIXED VERSION
"""

import json
import os

# United Airlines specific system prompt
UNITED_SYSTEM_PROMPT = """You are VectorBid, an expert AI assistant specializing in United Airlines pilot trip bidding.

You understand United Airlines operations, including:
- Hub operations at DEN, IAH, SFO, ORD, EWR, IAD
- International routes and layover cities
- Aircraft types (737, 757, 767, 777, 787, A320)
- Pilot quality of life factors

CRITICAL: Return EXACTLY this JSON format:
{
  "rankings": [
    {
      "rank": 1,
      "trip_id": "UA123",
      "score": 95,
      "reasoning": "Perfect match: 3-day trip with high efficiency, weekends off, DEN base",
      "efficiency": 6.1,
      "key_factors": ["high_efficiency", "weekends_off", "den_base"]
    }
  ]
}

Be specific about United Airlines operations."""


def create_united_prompt(trips, preferences, top_n=5):
    """Create United-specific prompt."""

    # Analyze preferences for context
    prefs_lower = preferences.lower()
    context = []

    if "den" in prefs_lower or "denver" in prefs_lower:
        context.append("appears to be Denver-based")
    if "family" in prefs_lower or "weekend" in prefs_lower:
        context.append("prioritizes work-life balance")
    if "credit" in prefs_lower or "hours" in prefs_lower:
        context.append("focuses on maximizing pay")
    if "international" in prefs_lower:
        context.append("prefers international routes")

    context_str = " and ".join(context) if context else "has standard preferences"

    # Create trip summaries
    trip_summaries = []
    for trip in trips:
        efficiency = trip.get("credit_hours", 0) / max(trip.get("days", 1), 1)
        routing = trip.get("routing", "")
        weekend_status = "includes weekend" if trip.get("includes_weekend") else "weekdays only"

        # Add United-specific insights
        route_notes = []
        if "DEN" in routing:
            route_notes.append("Denver hub")
        if "LHR" in routing or "FRA" in routing:
            route_notes.append("premium European route")
        if "NRT" in routing or "ICN" in routing:
            route_notes.append("premium Asian route")
        if efficiency >= 6:
            route_notes.append("good efficiency")

        notes = " • ".join(route_notes) if route_notes else "standard route"

        summary = f"Trip {trip['trip_id']}: {trip['days']}-day • {trip['credit_hours']} hrs • ({efficiency:.1f} hrs/day) • {routing} • {weekend_status} • {notes}"
        trip_summaries.append(summary)

    prompt = f"""PILOT PREFERENCES: {preferences}

CONTEXT: This pilot {context_str}

AVAILABLE UNITED TRIPS:
{chr(10).join(trip_summaries)}

Rank the top {top_n} trips that best match preferences. Consider efficiency, work-life balance, route quality, and United hub operations.

Focus on practical pilot concerns like pay efficiency vs time off, commuting, international premiums, and layover quality."""

    return prompt


def test_with_openai_api():
    """Test with real OpenAI API call using your existing llm_service."""

    # Check for API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        print("Set it with: export OPENAI_API_KEY='your-key-here'")
        return False

    print("🔑 OpenAI API key found")

    # Sample United trips with more variety
    sample_trips = [
        {
            "trip_id": "UA123",
            "days": 3,
            "credit_hours": 18.3,
            "routing": "DEN-LAX-DEN",
            "includes_weekend": False,
        },
        {
            "trip_id": "UA456",
            "days": 4,
            "credit_hours": 25.12,
            "routing": "DEN-LHR-FRA-DEN",
            "includes_weekend": True,
        },
        {
            "trip_id": "UA789",
            "days": 2,
            "credit_hours": 12.0,
            "routing": "DEN-PHX-DEN",
            "includes_weekend": False,
        },
        {
            "trip_id": "UA101",
            "days": 5,
            "credit_hours": 32.15,
            "routing": "DEN-NRT-ICN-DEN",
            "includes_weekend": False,
        },
    ]

    preferences = "I'm a Denver-based pilot who wants to maximize credit hours while maintaining work-life balance. I prefer international routes but want weekends off when possible."

    # Create prompt
    prompt = create_united_prompt(sample_trips, preferences, 4)

    print("🧪 Testing Enhanced United Airlines AI")
    print("=" * 60)
    print("TRIP ANALYSIS:")
    for trip in sample_trips:
        efficiency = trip["credit_hours"] / trip["days"]
        weekend = "🔴 Weekend" if trip["includes_weekend"] else "🟢 Weekdays"
        intl = (
            "🌍 International"
            if any(code in trip["routing"] for code in ["LHR", "FRA", "NRT", "ICN"])
            else "🇺🇸 Domestic"
        )
        print(
            f"  {trip['trip_id']}: {efficiency:.1f}h/day • {weekend} • {intl} • {trip['routing']}"
        )
    print("=" * 60)

    try:
        # Use your existing llm_service if available
        try:
            from llm_service import rank_trips_with_ai

            print("🤖 Using existing llm_service...")

            # Test with your existing system
            results = rank_trips_with_ai(sample_trips, preferences)

            print("✅ AI ranking successful!")
            print()
            print("🎯 RANKING RESULTS:")
            print("-" * 40)
            for i, result in enumerate(results[:4]):
                trip_id = result.get("trip_id", "?")
                score = result.get("score", "?")
                reasoning = result.get("reasoning", result.get("comment", "No reasoning"))
                print(f"  {i + 1}. {trip_id} (Score: {score})")
                print(f"     → {reasoning}")
            print("-" * 40)

            return True

        except ImportError:
            print("⚠️ llm_service not available, using direct API call...")

            # Direct OpenAI API call as backup
            try:
                from openai import OpenAI

                client = OpenAI()  # Simplified initialization

                print("🤖 Making direct API call...")

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": UNITED_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.1,
                    max_tokens=800,
                )

                response_content = response.choices[0].message.content
                print("✅ Direct API call successful!")
                print()
                print("🎯 AI RESPONSE:")
                print("-" * 40)
                print(response_content)
                print("-" * 40)

                # Try to parse JSON
                try:
                    data = json.loads(response_content)
                    rankings = data.get("rankings", [])

                    print()
                    print("📊 PARSED RANKINGS:")
                    for ranking in rankings:
                        rank = ranking.get("rank", "?")
                        trip_id = ranking.get("trip_id", "?")
                        score = ranking.get("score", "?")
                        reasoning = ranking.get("reasoning", "No reasoning provided")
                        efficiency = ranking.get("efficiency", "?")
                        print(f"  {rank}. {trip_id} (Score: {score}/100, {efficiency} hrs/day)")
                        print(f"     → {reasoning}")

                except json.JSONDecodeError as e:
                    print(f"⚠️ Could not parse JSON: {e}")

                return True

            except Exception as api_error:
                print(f"❌ Direct API call failed: {api_error}")
                return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def show_enhanced_prompt_example():
    """Show what the enhanced prompts look like."""

    sample_trips = [
        {
            "trip_id": "UA123",
            "days": 3,
            "credit_hours": 18.3,
            "routing": "DEN-LAX-DEN",
            "includes_weekend": False,
        },
        {
            "trip_id": "UA456",
            "days": 4,
            "credit_hours": 25.12,
            "routing": "DEN-LHR-FRA-DEN",
            "includes_weekend": True,
        },
        {
            "trip_id": "UA101",
            "days": 5,
            "credit_hours": 32.15,
            "routing": "DEN-NRT-ICN-DEN",
            "includes_weekend": False,
        },
    ]

    preferences = "Denver-based senior pilot seeking high-credit international routes with minimal weekend work"
    prompt = create_united_prompt(sample_trips, preferences, 3)

    print("🧪 Enhanced United Airlines Prompt Example")
    print("=" * 60)
    print(prompt)
    print("=" * 60)
    print(f"Prompt length: {len(prompt)} characters")
    print()
    print("🎯 Key Enhancements:")
    print("  ✅ United hub recognition (DEN)")
    print("  ✅ Route quality analysis (European/Asian premium)")
    print("  ✅ Efficiency calculations (hrs/day)")
    print("  ✅ Weekend impact assessment")
    print("  ✅ Pilot context understanding")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "example":
        show_enhanced_prompt_example()
    else:
        success = test_with_openai_api()
        if not success:
            print()
            print("💡 To see prompt example, run: python3 test_united_ai_fixed.py example")
