"""
Enhanced AI-powered trip ranking service for VectorBid.
Provides robust ranking with fallback strategies and improved prompt engineering.
"""

import json
import logging
import os

from openai import OpenAI, OpenAIError

logger = logging.getLogger(__name__)


class AITripRanker:
    """Enhanced AI-powered trip ranking service with robust error handling."""

    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.client = self._initialize_client()
        self.model = "gpt-4o-mini"  # Cost-effective choice for production
        self.fallback_model = "gpt-3.5-turbo"  # Backup model

    def _initialize_client(self) -> OpenAI | None:
        """Initialize OpenAI client with error handling."""
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set - AI ranking will use fallback")
            return None

        try:
            client = OpenAI(api_key=self.api_key)
            return client
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            return None

    def rank_trips(
        self, trips: list[dict], preferences: str, top_n: int = 15
    ) -> list[dict]:
        """
        Rank trips based on pilot preferences.

        Args:
            trips: List of parsed trip dictionaries
            preferences: Natural language preferences from pilot
            top_n: Number of top trips to return

        Returns:
            List of ranked trip dictionaries with scores and reasoning
        """
        if not trips:
            raise ValueError("No trips provided for ranking")

        if not preferences.strip():
            logger.warning("No preferences provided, using default ranking")
            return self._default_ranking(trips, top_n)

        # Use AI ranking if available, otherwise fall back
        if self.client:
            try:
                return self._ai_ranking(trips, preferences, top_n)
            except Exception as e:
                logger.error(f"AI ranking failed: {e}, using fallback")
                return self._fallback_ranking(trips, preferences, top_n)
        else:
            return self._fallback_ranking(trips, preferences, top_n)

    def _ai_ranking(
        self, trips: list[dict], preferences: str, top_n: int
    ) -> list[dict]:
        """Perform AI-powered trip ranking."""
        # Limit trips for token economy and processing speed
        trips_to_analyze = trips[:50] if len(trips) > 50 else trips

        # Prepare trip summaries for AI
        trip_summaries = self._prepare_trip_summaries(trips_to_analyze)

        # Create the ranking prompt
        prompt = self._create_ranking_prompt(trip_summaries, preferences, top_n)

        try:
            # Make API request with retry logic
            response = self._make_api_request(prompt, max_tokens=1200)

            # Parse and validate the response
            rankings = self._parse_ai_response(response, trips_to_analyze)

            # Limit to requested number
            return rankings[:top_n]

        except Exception as e:
            logger.error(f"AI ranking request failed: {e}")
            raise

    def _make_api_request(
        self, prompt: str, max_tokens: int = 1000, retries: int = 2
    ) -> str:
        """Make API request with retry logic."""
        for attempt in range(retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    temperature=0.1,  # Low temperature for consistency
                    max_tokens=max_tokens,
                    messages=[
                        {"role": "system", "content": self._get_system_prompt()},
                        {"role": "user", "content": prompt},
                    ],
                    response_format={"type": "json_object"},
                )

                content = response.choices[0].message.content
                if not content:
                    raise ValueError("Empty response from AI")

                return content

            except OpenAIError as e:
                if attempt < retries:
                    logger.warning(
                        f"API request failed (attempt {attempt + 1}), retrying: {e}"
                    )
                    continue
                else:
                    raise
            except Exception as e:
                if attempt < retries and "model" in str(e).lower():
                    # Try fallback model
                    logger.warning(f"Trying fallback model due to: {e}")
                    self.model = self.fallback_model
                    continue
                else:
                    raise

    def _get_system_prompt(self) -> str:
        """Get the system prompt for AI trip ranking."""
        return """You are VectorBid, an expert AI assistant helping airline pilots rank their monthly bid trips based on their personal preferences and quality of life factors.

Your expertise includes:
- Understanding pilot scheduling and work-life balance needs
- Knowledge of airline operations, layovers, and trip structures
- Awareness of factors like commuting, rest requirements, and family time
- Recognition of career stage differences (junior vs senior pilots)

Analyze each trip considering:
- Trip length and total days away from home
- Credit hours and pay efficiency (credit hours per day)
- Weekend and holiday coverage
- Routing and layover quality
- Departure/return times and commute impact
- Rest and recovery time between trips

Provide rankings that prioritize pilot wellbeing and stated preferences while considering practical factors like pay and schedule efficiency.

Return ONLY a JSON object with this exact structure:
{
  "rankings": [
    {
      "rank": 1,
      "trip_id": "105",
      "score": 95,
      "reasoning": "Perfect match for your preferences - 3 days with weekends off and good pay efficiency",
      "efficiency": 4.6,
      "key_factors": ["weekend_friendly", "good_pay", "short_trip"]
    }
  ],
  "analysis_summary": "Based on your preferences for work-life balance, I prioritized trips that..."
}

Be specific and practical in your reasoning. Focus on the factors that matter most to pilots."""

    def _create_ranking_prompt(
        self, trip_summaries: list[str], preferences: str, top_n: int
    ) -> str:
        """Create the user prompt for trip ranking."""
        trips_text = "\n".join(
            f"{i + 1}. {summary}" for i, summary in enumerate(trip_summaries)
        )

        return f"""Please analyze and rank these airline trips based on the pilot's preferences.

PILOT PREFERENCES:
{preferences}

AVAILABLE TRIPS:
{trips_text}

Please rank the top {top_n} trips that best match these preferences. Consider all aspects of pilot quality of life, work-life balance, pay efficiency, and practical factors like commuting and rest.

For each trip, calculate an efficiency score (credit_hours / days) and consider how well it matches the stated preferences."""

    def _prepare_trip_summaries(self, trips: list[dict]) -> list[str]:
        """Create concise but informative summaries of trips for AI processing."""
        summaries = []

        for trip in trips:
            # Calculate efficiency
            efficiency = trip.get("credit_hours", 0) / max(trip.get("days", 1), 1)

            summary_parts = [
                f"Trip {trip.get('trip_id', 'Unknown')}:",
                f"{trip.get('days', 0)}-day trip",
                f"{trip.get('credit_hours', 0)} credit hours",
                f"(efficiency: {efficiency:.1f} hrs/day)",
            ]

            # Add weekend information
            if trip.get("includes_weekend"):
                summary_parts.append("includes weekend")
            else:
                summary_parts.append("weekdays only")

            # Add routing if available
            if trip.get("routing"):
                summary_parts.append(f"routing: {trip['routing']}")

            summaries.append(" • ".join(summary_parts))

        return summaries

    def _parse_ai_response(
        self, response_content: str, original_trips: list[dict]
    ) -> list[dict]:
        """Parse and validate AI response."""
        try:
            data = json.loads(response_content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            raise ValueError("Invalid JSON response from AI") from e

        # Extract rankings from response
        rankings = data.get("rankings", [])
        if not isinstance(rankings, list):
            raise ValueError("AI response missing rankings array")

        # Create trip lookup for validation
        trip_lookup = {
            trip.get("trip_id", trip.get("id", "")): trip for trip in original_trips
        }

        validated_results = []
        for i, ranking in enumerate(rankings):
            if not isinstance(ranking, dict):
                logger.warning(f"Skipping invalid ranking item {i}")
                continue

            trip_id = str(ranking.get("trip_id", ""))
            if trip_id not in trip_lookup:
                logger.warning(f"Trip ID {trip_id} not found in original trips")
                continue

            # Build validated result
            result = {
                "rank": ranking.get("rank", i + 1),
                "trip_id": trip_id,
                "score": min(100, max(0, ranking.get("score", 50))),  # Clamp to 0-100
                "reasoning": ranking.get("reasoning", "Matches your preferences"),
                "efficiency": ranking.get("efficiency", 0.0),
                "key_factors": ranking.get("key_factors", []),
                "trip_data": trip_lookup[trip_id],
            }

            validated_results.append(result)

        if not validated_results:
            raise ValueError("No valid rankings found in AI response")

        # Sort by rank to ensure proper ordering
        validated_results.sort(key=lambda x: x["rank"])

        logger.info(f"Successfully parsed {len(validated_results)} AI rankings")
        return validated_results

    def _fallback_ranking(
        self, trips: list[dict], preferences: str, top_n: int
    ) -> list[dict]:
        """Provide intelligent fallback ranking when AI is unavailable."""
        logger.info("Using intelligent fallback ranking")

        # Analyze preferences for key terms
        prefs_lower = preferences.lower()

        def calculate_score(trip: dict) -> tuple[float, list[str]]:
            """Calculate heuristic score based on preferences."""
            score = 50.0  # Base score
            factors = []

            # Efficiency scoring (credit hours per day)
            credit_hours = trip.get("credit_hours", 0)
            days = trip.get("days", 1)
            efficiency = credit_hours / max(days, 1)

            if efficiency > 6.0:
                score += 20
                factors.append("high_efficiency")
            elif efficiency > 4.0:
                score += 10
                factors.append("good_efficiency")

            # Weekend preferences
            includes_weekend = trip.get("includes_weekend", False)
            if "weekend" in prefs_lower:
                if "no weekend" in prefs_lower or "weekends off" in prefs_lower:
                    if not includes_weekend:
                        score += 15
                        factors.append("weekend_friendly")
                    else:
                        score -= 10
                elif "weekend" in prefs_lower and includes_weekend:
                    score += 10
                    factors.append("weekend_included")

            # Trip length preferences
            if "short" in prefs_lower or "quick" in prefs_lower:
                if days <= 2:
                    score += 15
                    factors.append("short_trip")
                elif days >= 4:
                    score -= 5
            elif "long" in prefs_lower:
                if days >= 4:
                    score += 10
                    factors.append("long_trip")

            # Credit hours preferences
            if "high credit" in prefs_lower or "more hours" in prefs_lower:
                if credit_hours >= 20:
                    score += 15
                    factors.append("high_credit")
                elif credit_hours >= 15:
                    score += 10
                    factors.append("good_credit")

            return score, factors

        # Calculate scores for all trips
        scored_trips = []
        for trip in trips:
            score, factors = calculate_score(trip)

            scored_trips.append(
                {
                    "rank": 0,  # Will be set after sorting
                    "trip_id": trip.get("trip_id", trip.get("id", "Unknown")),
                    "score": round(score, 1),
                    "reasoning": self._generate_fallback_reasoning(
                        trip, factors, preferences
                    ),
                    "efficiency": trip.get("credit_hours", 0)
                    / max(trip.get("days", 1), 1),
                    "key_factors": factors,
                    "trip_data": trip,
                }
            )

        # Sort by score (descending)
        scored_trips.sort(key=lambda x: x["score"], reverse=True)

        # Set ranks
        for i, trip in enumerate(scored_trips):
            trip["rank"] = i + 1

        return scored_trips[:top_n]

    def _generate_fallback_reasoning(
        self, trip: dict, factors: list[str], preferences: str
    ) -> str:
        """Generate reasoning for fallback rankings."""
        reasons = []

        credit_hours = trip.get("credit_hours", 0)
        days = trip.get("days", 1)
        efficiency = credit_hours / max(days, 1)

        # Efficiency reasoning
        if efficiency > 6.0:
            reasons.append(f"excellent pay efficiency ({efficiency:.1f} hrs/day)")
        elif efficiency > 4.0:
            reasons.append(f"good pay efficiency ({efficiency:.1f} hrs/day)")

        # Factor-based reasoning
        factor_messages = {
            "weekend_friendly": "avoids weekends as requested",
            "weekend_included": "includes weekend work",
            "short_trip": "short trip duration",
            "long_trip": "longer trip for higher credit",
            "high_credit": "high credit hours",
            "good_credit": "solid credit hours",
            "high_efficiency": "very efficient credit/day ratio",
        }

        for factor in factors:
            if factor in factor_messages:
                reasons.append(factor_messages[factor])

        if not reasons:
            reasons.append(f"{days}-day trip with {credit_hours} credit hours")

        return f"Good match: {', '.join(reasons[:3])}"  # Limit to top 3 reasons

    def _default_ranking(self, trips: list[dict], top_n: int) -> list[dict]:
        """Provide basic ranking when no preferences given."""
        logger.info("Using default ranking (by efficiency)")

        # Sort by efficiency (credit hours per day)
        ranked_trips = sorted(
            trips,
            key=lambda t: t.get("credit_hours", 0) / max(t.get("days", 1), 1),
            reverse=True,
        )

        results = []
        for i, trip in enumerate(ranked_trips[:top_n]):
            efficiency = trip.get("credit_hours", 0) / max(trip.get("days", 1), 1)
            results.append(
                {
                    "rank": i + 1,
                    "trip_id": trip.get("trip_id", trip.get("id", "Unknown")),
                    "score": max(0, 90 - i * 3),  # Declining scores
                    "reasoning": f"Ranked by pay efficiency ({efficiency:.1f} credit hrs/day)",
                    "efficiency": efficiency,
                    "key_factors": ["efficiency_based"],
                    "trip_data": trip,
                }
            )

        return results


# Public interface functions
def rank_trips_with_ai(
    trips: list[dict], preferences: str, top_n: int = 15
) -> list[dict]:
    """
    Rank trips using AI with robust fallback handling.

    Args:
        trips: List of parsed trip dictionaries
        preferences: Natural language preferences from pilot
        top_n: Number of top trips to return (default 15)

    Returns:
        List of ranked trip dictionaries with scores and reasoning
    """
    if not trips:
        raise ValueError("No trips provided for ranking")

    ranker = AITripRanker()
    return ranker.rank_trips(trips, preferences, top_n)


def is_ai_available() -> bool:
    """Check if AI ranking is available."""
    return os.environ.get("OPENAI_API_KEY") is not None


def get_ranking_capabilities() -> dict[str, bool]:
    """Get available ranking capabilities."""
    return {
        "ai_ranking": is_ai_available(),
        "fallback_ranking": True,
        "preference_analysis": True,
        "efficiency_calculation": True,
    }
