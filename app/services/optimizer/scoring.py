# ============================================
# MODULE 3: app/services/optimizer/scoring.py
# ============================================
"""Trip scoring engine"""

from typing import List, Dict, Any
from enum import Enum


class ScoringStrategy(Enum):
    """Available scoring strategies"""
    WEIGHTED_SUM = "weighted_sum"
    MULTIPLICATIVE = "multiplicative"
    LEXICOGRAPHIC = "lexicographic"


class TripScorer:
    """Scores trips based on preferences"""

    def __init__(self,
                 strategy: ScoringStrategy = ScoringStrategy.WEIGHTED_SUM):
        self.strategy = strategy

    def score_trips(self, trips: List[Dict],
                    weights: Dict[str, float]) -> List[Dict]:
        """Score each trip based on weighted preferences"""
        scored_trips = []

        for trip in trips:
            score = self._calculate_score(trip, weights)
            trip_with_score = trip.copy()
            trip_with_score['optimization_score'] = score
            trip_with_score['score_breakdown'] = self._get_score_breakdown(
                trip, weights)
            scored_trips.append(trip_with_score)

        return scored_trips

    def _calculate_score(self, trip: Dict, weights: Dict[str, float]) -> float:
        """Calculate single trip score"""
        if self.strategy == ScoringStrategy.WEIGHTED_SUM:
            return self._weighted_sum_score(trip, weights)
        elif self.strategy == ScoringStrategy.MULTIPLICATIVE:
            return self._multiplicative_score(trip, weights)
        else:
            return self._lexicographic_score(trip, weights)

    def _weighted_sum_score(self, trip: Dict, weights: Dict[str,
                                                            float]) -> float:
        """Standard weighted sum scoring"""
        total_score = 0.0

        # Weekend preference
        if weights.get('weekend_protection', 0) > 0:
            if not trip.get('includes_weekend', False):
                total_score += weights['weekend_protection'] * 100

        # Credit preference
        if weights.get('max_credit', 0) > 0:
            credit = trip.get('credit_hours', 0)
            total_score += weights['max_credit'] * credit

        # Layover preferences
        if weights.get('layover_pref', 0) > 0:
            preferred_layovers = ['DEN', 'ORD', 'LAX']
            routing = trip.get('routing', '')
            for city in preferred_layovers:
                if city in routing:
                    total_score += weights['layover_pref'] * 20

        # Trip length preference
        if weights.get('short_trips', 0) > 0:
            days = trip.get('days', 0)
            if days <= 3:
                total_score += weights['short_trips'] * 30

        return total_score

    def _multiplicative_score(self, trip: Dict, weights: Dict[str,
                                                              float]) -> float:
        """Multiplicative scoring for non-compensatory preferences"""
        score = 1.0
        # Implementation here
        return score

    def _lexicographic_score(self, trip: Dict, weights: Dict[str,
                                                             float]) -> float:
        """Lexicographic scoring for strict priority ordering"""
        # Implementation here
        return 0.0

    def _get_score_breakdown(self, trip: Dict, weights: Dict[str,
                                                             float]) -> Dict:
        """Get detailed breakdown of score components"""
        breakdown = {}
        if weights.get('weekend_protection', 0) > 0:
            breakdown['weekend'] = not trip.get('includes_weekend', False)
        if weights.get('max_credit', 0) > 0:
            breakdown['credit'] = trip.get('credit_hours', 0)
        return breakdown
