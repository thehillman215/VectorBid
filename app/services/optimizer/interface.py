# ============================================
# MODULE 2: app/services/optimizer/interface.py
# ============================================
"""Public interface for the optimizer"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from .scoring import TripScorer
from .ranking import TripRanker
from .filters import FilterEngine
from .preferences import PreferenceParser


@dataclass
class OptimizationRequest:
    """Request object for optimization"""
    feature_bundle: Dict[str, Any]
    preferences: str
    trip_data: List[Dict[str, Any]]
    max_results: int = 50


@dataclass
class OptimizationResult:
    """Result object from optimization"""
    ranked_trips: List[Dict[str, Any]]
    scores: List[float]
    explanations: List[str]
    metadata: Dict[str, Any]


def select_topk(feature_bundle: Dict[str, Any],
                k: int = 50) -> List[Dict[str, Any]]:
    """
    Main entry point for optimization
    Maintains backward compatibility with existing code
    """
    # Parse preferences
    parser = PreferenceParser()
    weights = parser.parse(feature_bundle.get('preference_schema', {}))

    # Filter trips
    filter_engine = FilterEngine()
    filtered_trips = filter_engine.apply_filters(
        trips=feature_bundle.get('pairing_features', {}).get('pairings', []),
        rules=weights.hard_constraints)

    # Score trips
    scorer = TripScorer()
    scored_trips = scorer.score_trips(trips=filtered_trips,
                                      weights=weights.soft_preferences)

    # Rank trips
    ranker = TripRanker()
    ranked_trips = ranker.rank(scored_trips=scored_trips,
                               algorithm='weighted_sum',
                               top_k=k)

    return ranked_trips
