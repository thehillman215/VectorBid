"""Preference parsing and weight extraction"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Import FilterRule from filters module
from .filters import FilterRule

@dataclass
class PreferenceWeight:
    """Preference weights and constraints"""
    hard_constraints: List[Any]
    soft_preferences: Dict[str, float]
    metadata: Dict[str, Any]

class PreferenceParser:
    """Parses preference schema into weights"""
    
    def parse(self, preference_schema: Dict[str, Any]) -> PreferenceWeight:
        """Parse preference schema into weight object"""
        
        # Extract hard constraints
        hard_constraints = self._extract_hard_constraints(
            preference_schema.get('hard_constraints', {})
        )
        
        # Extract soft preferences with weights
        soft_preferences = self._extract_soft_preferences(
            preference_schema.get('soft_prefs', {})
        )
        
        # Add any derived preferences
        soft_preferences.update(self._derive_preferences(preference_schema))
        
        return PreferenceWeight(
            hard_constraints=hard_constraints,
            soft_preferences=soft_preferences,
            metadata={
                'pilot_id': preference_schema.get('pilot_id'),
                'base': preference_schema.get('base'),
                'seat': preference_schema.get('seat')
            }
        )
    
    def _extract_hard_constraints(self, constraints: Dict) -> List[Any]:
        """Convert hard constraints to filter rules"""
        rules = []
        
        if constraints.get('no_red_eyes'):
            rules.append(FilterRule('is_redeye', 'eq', False))
        
        if constraints.get('no_weekends'):
            rules.append(FilterRule('includes_weekend', 'eq', False))
        
        if constraints.get('max_days'):
            rules.append(FilterRule('days', 'lt', constraints['max_days']))
        
        return rules
    
    def _extract_soft_preferences(self, prefs: Dict) -> Dict[str, float]:
        """Extract soft preferences with weights"""
        weights = {}
        
        for key, value in prefs.items():
            if isinstance(value, dict):
                weights[key] = value.get('weight', 1.0)
            else:
                weights[key] = float(value)
        
        return weights
    
    def _derive_preferences(self, schema: Dict) -> Dict[str, float]:
        """Derive additional preferences from schema"""
        derived = {}
        
        # Commuter preferences
        if schema.get('is_commuter'):
            derived['commutable'] = 1.0
            derived['short_trips'] = 0.8
        
        # Seniority-based preferences
        seniority = schema.get('seniority_percentile', 0.5)
        if seniority > 0.7:  # Senior pilots
            derived['prime_time_off'] = 1.0
        else:  # Junior pilots
            derived['max_credit'] = 0.8
        
        return derived
