# ============================================
# MODULE 1: app/services/optimizer/__init__.py
# ============================================
from typing import List, Dict, Any, Optional
"""
Modular optimizer package for VectorBid
Splits optimization logic into independent, testable components
"""

from .interface import OptimizationRequest, OptimizationResult, select_topk
from .scoring import TripScorer, ScoringStrategy
from .ranking import TripRanker, RankingAlgorithm
from .filters import FilterEngine, FilterRule
from .preferences import PreferenceParser, PreferenceWeight

__all__ = [
    'OptimizationRequest', 'OptimizationResult', 'select_topk', 'TripScorer',
    'ScoringStrategy', 'TripRanker', 'RankingAlgorithm', 'FilterEngine',
    'FilterRule', 'PreferenceParser', 'PreferenceWeight'
]
