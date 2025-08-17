"""
Test Enhanced United Airlines LLM with Real OpenAI API
"""

import json
import os

from openai import OpenAI

# United Airlines specific system prompt
UNITED_SYSTEM_PROMPT = """You are VectorBid, an expert AI assistant specializing in United Airlines pilot trip bidding.

You understand United Airlines operations, including:
- Hub operations at DEN, IAH, SFO, ORD, EWR, IAD
- International routes and layover cities  
- Aircraft types (737, 757, 767, 777, 787, A320)
- Pilot quality of life factors
- Seniority-based bidding strategies

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

Be specific about United Airlines operations and provide actionable insights."""


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
        weekend_status = (
            "includes weekend" if trip.get("includes_weekend") else "weekdays only"
        )

        # Add United-specific insights
        route_notes = []
        if "DEN" in routing:
            route_notes.append("Denver hub")
        if "LHR" in routing or "FRA" in routing:
            route_notes.append("premium European route")
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
    """Test with real OpenAI API call."""

    # Check for API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        print("Set it with: export OPENAI_API_KEY='your-key-here'")
        return

    print("🔑 OpenAI API key found")

    # Sample United trips from our earlier test
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
    print("PROMPT PREVIEW:")
    print(prompt[:300] + "..." if len(prompt) > 300 else prompt)
    print("=" * 60)

    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)

        print("🤖 Calling OpenAI API...")

        # Make API call
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Cost-effective model
            messages=[
                {"role": "system", "content": UNITED_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,  # Low temperature for consistent results
            max_tokens=1000,
        )

        # Get response
        response_content = response.choices[0].message.content
        print("✅ API call successful!")
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
                print(f"  {rank}. {trip_id} (Score: {score}/100)")
                print(f"     → {reasoning}")

            # Calculate costs
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens

            # GPT-4o-mini pricing (approximate)
            input_cost = (input_tokens / 1000) * 0.00015  # $0.15 per 1K input tokens
            output_cost = (output_tokens / 1000) * 0.0006  # $0.60 per 1K output tokens
            total_cost = input_cost + output_cost

            print()
            print("💰 API USAGE:")
            print(
                f"  Tokens: {input_tokens} input + {output_tokens} output = {total_tokens} total"
            )
            print(
                f"  Cost: ~${total_cost:.4f} (input: ${input_cost:.4f}, output: ${output_cost:.4f})"
            )

        except json.JSONDecodeError as e:
            print(f"⚠️ Could not parse JSON response: {e}")
            print("Raw response shown above")

    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False

    return True


def test_without_api():
    """Test prompt generation without API call."""
    print("🧪 Testing Prompt Generation (No API)")
    print("=" * 50)

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
    ]

    preferences = "Denver-based pilot wanting international routes with weekends off"
    prompt = create_united_prompt(sample_trips, preferences, 2)

    print("GENERATED PROMPT:")
    print(prompt)
    print("=" * 50)
    print(f"Prompt length: {len(prompt)} characters")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "no-api":
        test_without_api()
    else:
        success = test_with_openai_api()
        if not success:
            print()
            print("💡 To test without API, run: python3 test_united_ai.py no-api")
