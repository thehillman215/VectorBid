# ============================================
# MODULE 4: app/services/optimizer/ranking.py
# ============================================
"""Trip ranking algorithms"""

from typing import List, Dict, Any
from enum import Enum


class RankingAlgorithm(Enum):
    """Available ranking algorithms"""
    SIMPLE = "simple"
    WEIGHTED_SUM = "weighted_sum"
    PARETO = "pareto"
    HYBRID = "hybrid"


class TripRanker:
    """Ranks scored trips using various algorithms"""

    def rank(self,
             scored_trips: List[Dict],
             algorithm: str = 'weighted_sum',
             top_k: int = 50) -> List[Dict]:
        """Rank trips and return top K"""

        if algorithm == 'simple':
            ranked = self._simple_rank(scored_trips)
        elif algorithm == 'pareto':
            ranked = self._pareto_rank(scored_trips)
        elif algorithm == 'hybrid':
            ranked = self._hybrid_rank(scored_trips)
        else:
            ranked = self._weighted_sum_rank(scored_trips)

        # Add rank numbers
        for i, trip in enumerate(ranked[:top_k]):
            trip['rank'] = i + 1
            trip['percentile'] = 100 * (1 - i / len(ranked))

        return ranked[:top_k]

    def _simple_rank(self, trips: List[Dict]) -> List[Dict]:
        """Simple score-based ranking"""
        return sorted(trips,
                      key=lambda x: x.get('optimization_score', 0),
                      reverse=True)

    def _weighted_sum_rank(self, trips: List[Dict]) -> List[Dict]:
        """Weighted sum ranking with tie-breaking"""
        return sorted(
            trips,
            key=lambda x: (
                x.get('optimization_score', 0),
                -x.get('days', 999),  # Prefer shorter trips as tie-breaker
                x.get('credit_hours', 0)  # Then higher credit
            ),
            reverse=True)

    def _pareto_rank(self, trips: List[Dict]) -> List[Dict]:
        """Pareto-optimal ranking (multi-objective)"""
        # Implementation for Pareto frontier
        return self._simple_rank(trips)  # Fallback for now

    def _hybrid_rank(self, trips: List[Dict]) -> List[Dict]:
        """Hybrid ranking combining multiple strategies"""
        # Implementation for hybrid approach
        return self._weighted_sum_rank(trips)
