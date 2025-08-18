# ============================================
# MODULE 5: app/services/optimizer/filters.py
# ============================================
"""Filter engine for hard constraints"""

from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class FilterRule:
    """Single filter rule"""
    field: str
    operator: str  # 'eq', 'ne', 'gt', 'lt', 'in', 'not_in'
    value: Any


class FilterEngine:
    """Applies hard constraint filters to trips"""

    def apply_filters(self, trips: List[Dict],
                      rules: List[FilterRule]) -> List[Dict]:
        """Apply all filter rules to trips"""
        filtered = trips

        for rule in rules:
            filtered = self._apply_single_filter(filtered, rule)

        return filtered

    def _apply_single_filter(self, trips: List[Dict],
                             rule: FilterRule) -> List[Dict]:
        """Apply a single filter rule"""
        result = []

        for trip in trips:
            if self._matches_rule(trip, rule):
                result.append(trip)

        return result

    def _matches_rule(self, trip: Dict, rule: FilterRule) -> bool:
        """Check if trip matches filter rule"""
        value = trip.get(rule.field)

        if rule.operator == 'eq':
            return value == rule.value
        elif rule.operator == 'ne':
            return value != rule.value
        elif rule.operator == 'gt':
            return value > rule.value
        elif rule.operator == 'lt':
            return value < rule.value
        elif rule.operator == 'in':
            return value in rule.value
        elif rule.operator == 'not_in':
            return value not in rule.value
        else:
            return True
