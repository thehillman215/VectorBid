# bid_layers_system.py
# Enhanced Bid Layers System for VectorBid - Copy this entire file

from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
from datetime import datetime, time, date
import json


class FilterType(Enum):
    """Types of filters that can be applied to trips"""
    AWARD = "AWARD"
    AVOID = "AVOID"
    REQUIRE = "REQUIRE"
    PREFER = "PREFER"
    LIMIT = "LIMIT"


class FilterCriteria(Enum):
    """Available criteria for filtering trips"""
    DAYS_OFF = "days_off"
    WEEKENDS_OFF = "weekends_off"
    TRIP_LENGTH = "trip_length"
    DEPARTURE_TIME = "departure_time"
    ARRIVAL_TIME = "arrival_time"
    LAYOVER_CITY = "layover_city"
    DEPARTURE_CITY = "departure_city"
    ARRIVAL_CITY = "arrival_city"
    OVERNIGHT_CITY = "overnight_city"
    CREDIT_HOURS = "credit_hours"
    BLOCK_HOURS = "block_hours"
    DUTY_TIME = "duty_time"
    RED_EYE = "red_eye"
    INTERNATIONAL = "international"
    DOMESTIC = "domestic"
    TURN_TIME = "turn_time"
    AIRCRAFT_TYPE = "aircraft_type"
    COMMUTABLE = "commutable"
    BACK_TO_BACK = "back_to_back"
    SPECIFIC_DATES = "specific_dates"


@dataclass
class BidFilter:
    """Individual filter within a bid layer"""
    criteria: FilterCriteria
    filter_type: FilterType
    value: Any
    operator: str = "equals"
    weight: float = 1.0
    description: str = ""

    def matches_trip(self, trip: Dict[str, Any]) -> Tuple[bool, str]:
        trip_value = self._extract_trip_value(trip)
        matches = self._evaluate_condition(trip_value)
        explanation = self._generate_explanation(trip_value, matches)
        return matches, explanation

    def _extract_trip_value(self, trip: Dict[str, Any]) -> Any:
        if self.criteria == FilterCriteria.TRIP_LENGTH:
            return trip.get('days', 0)
        elif self.criteria == FilterCriteria.CREDIT_HOURS:
            return trip.get('credit_hours', 0)
        elif self.criteria == FilterCriteria.DEPARTURE_TIME:
            return trip.get('departure_time', '00:00')
        elif self.criteria == FilterCriteria.LAYOVER_CITY:
            return trip.get('layover_cities', [])
        elif self.criteria == FilterCriteria.RED_EYE:
            return trip.get('is_red_eye', False)
        elif self.criteria == FilterCriteria.WEEKENDS_OFF:
            return trip.get('includes_weekend', False)
        elif self.criteria == FilterCriteria.COMMUTABLE:
            return trip.get('is_commutable', True)
        elif self.criteria == FilterCriteria.INTERNATIONAL:
            return trip.get('is_international', False)
        return None

    def _evaluate_condition(self, trip_value: Any) -> bool:
        if self.operator == "equals":
            return trip_value == self.value
        elif self.operator == "greater_than":
            return float(trip_value) > float(self.value)
        elif self.operator == "less_than":
            return float(trip_value) < float(self.value)
        elif self.operator == "contains":
            if isinstance(trip_value, list):
                return self.value in trip_value
            return str(self.value).lower() in str(trip_value).lower()
        elif self.operator == "not_contains":
            if isinstance(trip_value, list):
                return self.value not in trip_value
            return str(self.value).lower() not in str(trip_value).lower()
        return False

    def _generate_explanation(self, trip_value: Any, matches: bool) -> str:
        action = "MATCHES" if matches else "DOES NOT MATCH"
        criteria_name = self.criteria.value.replace('_', ' ').title()
        return f"{action}: {criteria_name} {self.operator} {self.value} (trip has: {trip_value})"


@dataclass
class BidLayer:
    """A single bid layer containing multiple filters and logic"""
    layer_number: int
    name: str
    filters: List[BidFilter] = field(default_factory=list)
    logic_operator: str = "AND"
    priority: int = 1
    description: str = ""
    is_active: bool = True

    def evaluate_trip(self, trip: Dict[str,
                                       Any]) -> Tuple[bool, List[str], float]:
        if not self.is_active or not self.filters:
            return False, ["Layer is inactive or has no filters"], 0.0

        filter_results = []
        explanations = []

        for filter_obj in self.filters:
            matches, explanation = filter_obj.matches_trip(trip)
            filter_results.append(matches)
            explanations.append(f"  {explanation}")

        if self.logic_operator == "AND":
            layer_matches = all(filter_results)
        elif self.logic_operator == "OR":
            layer_matches = any(filter_results)
        else:
            layer_matches = False

        score = 0.0
        if layer_matches:
            total_weight = sum(f.weight for f in self.filters
                               if filter_results[i]
                               for i, f in enumerate(self.filters))
            score = total_weight * (self.priority / 10.0)

        layer_explanation = f"Layer {self.layer_number} ({self.name}): {'MATCHES' if layer_matches else 'NO MATCH'}"
        explanations.insert(0, layer_explanation)

        return layer_matches, explanations, score


@dataclass
class BidLayersSystem:
    """Complete bid layers system supporting up to 50 layers"""
    layers: List[BidLayer] = field(default_factory=list)
    max_layers: int = 50

    def add_layer(self, layer: BidLayer) -> bool:
        if len(self.layers) >= self.max_layers:
            return False
        layer.layer_number = len(self.layers) + 1
        self.layers.append(layer)
        return True

    def remove_layer(self, layer_number: int) -> bool:
        self.layers = [
            layer for layer in self.layers
            if layer.layer_number != layer_number
        ]
        for i, layer in enumerate(self.layers):
            layer.layer_number = i + 1
        return True

    def evaluate_all_trips(
            self, trips: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        evaluated_trips = []

        for trip in trips:
            trip_result = {
                **trip, 'layer_matches': [],
                'total_score': 0.0,
                'matching_layers': [],
                'detailed_explanations': [],
                'bid_recommendation': 'CONSIDER'
            }

            total_score = 0.0
            matching_layers = []
            all_explanations = []

            for layer in sorted(self.layers,
                                key=lambda x: x.priority,
                                reverse=True):
                matches, explanations, score = layer.evaluate_trip(trip)

                trip_result['layer_matches'].append({
                    'layer_number':
                    layer.layer_number,
                    'layer_name':
                    layer.name,
                    'matches':
                    matches,
                    'score':
                    score,
                    'explanations':
                    explanations
                })

                if matches:
                    matching_layers.append(layer.layer_number)
                    total_score += score

                all_explanations.extend(explanations)

            trip_result['total_score'] = total_score
            trip_result['matching_layers'] = matching_layers
            trip_result['detailed_explanations'] = all_explanations

            if total_score >= 8.0:
                trip_result['bid_recommendation'] = 'HIGHLY_RECOMMENDED'
            elif total_score >= 5.0:
                trip_result['bid_recommendation'] = 'RECOMMENDED'
            elif total_score >= 2.0:
                trip_result['bid_recommendation'] = 'CONSIDER'
            else:
                trip_result['bid_recommendation'] = 'AVOID'

            evaluated_trips.append(trip_result)

        evaluated_trips.sort(key=lambda x: x['total_score'], reverse=True)
        return evaluated_trips

    def generate_pbs_output(self, evaluated_trips: List[Dict[str,
                                                             Any]]) -> str:
        pbs_groups = []

        highly_recommended = [
            t for t in evaluated_trips
            if t['bid_recommendation'] == 'HIGHLY_RECOMMENDED'
        ]
        recommended = [
            t for t in evaluated_trips
            if t['bid_recommendation'] == 'RECOMMENDED'
        ]

        group_num = 1

        if highly_recommended:
            pbs_groups.append(f"Group {group_num}: # Top Priority Trips")
            for trip in highly_recommended[:10]:
                trip_id = trip.get(
                    'pairing_id',
                    trip.get('trip_id', f"Trip{trip.get('id', 'Unknown')}"))
                pbs_groups.append(f"  AWARD {trip_id}")
            group_num += 1

        if recommended:
            pbs_groups.append(f"Group {group_num}: # Good Match Trips")
            for trip in recommended[:15]:
                trip_id = trip.get(
                    'pairing_id',
                    trip.get('trip_id', f"Trip{trip.get('id', 'Unknown')}"))
                pbs_groups.append(f"  AWARD {trip_id}")
            group_num += 1

        for layer in sorted(self.layers,
                            key=lambda x: x.priority,
                            reverse=True):
            if not layer.is_active:
                continue

            pbs_groups.append(f"Group {group_num}: # {layer.name}")

            for filter_obj in layer.filters:
                pbs_command = self._convert_filter_to_pbs(filter_obj)
                if pbs_command:
                    pbs_groups.append(f"  {pbs_command}")

            group_num += 1

        return "\n".join(pbs_groups)

    def _convert_filter_to_pbs(self, filter_obj: BidFilter) -> str:
        if filter_obj.filter_type == FilterType.AWARD:
            if filter_obj.criteria == FilterCriteria.LAYOVER_CITY:
                return f"AWARD Pairings IF Layover={filter_obj.value}"
            elif filter_obj.criteria == FilterCriteria.WEEKENDS_OFF:
                return "AWARD Days Off IF Weekend"
            elif filter_obj.criteria == FilterCriteria.TRIP_LENGTH:
                if filter_obj.operator == "greater_than":
                    return f"AWARD Pairings IF Days>={filter_obj.value}"
                elif filter_obj.operator == "less_than":
                    return f"AWARD Pairings IF Days<={filter_obj.value}"
        elif filter_obj.filter_type == FilterType.AVOID:
            if filter_obj.criteria == FilterCriteria.RED_EYE:
                return "AVOID Pairings IF RedEye=True"
            elif filter_obj.criteria == FilterCriteria.WEEKENDS_OFF and filter_obj.value:
                return "AVOID Pairings IF Weekend=True"
        return f"# {filter_obj.description}"

    def get_layer_summary(self) -> Dict[str, Any]:
        return {
            'total_layers':
            len(self.layers),
            'active_layers':
            len([l for l in self.layers if l.is_active]),
            'max_layers':
            self.max_layers,
            'layers_detail': [{
                'layer_number':
                layer.layer_number,
                'name':
                layer.name,
                'filters_count':
                len(layer.filters),
                'priority':
                layer.priority,
                'is_active':
                layer.is_active,
                'description':
                layer.description,
                'filters': [{
                    'criteria': f.criteria.value,
                    'filter_type': f.filter_type.value,
                    'value': f.value,
                    'operator': f.operator,
                    'description': f.description
                } for f in layer.filters]
            } for layer in self.layers]
        }


# Factory functions
def create_weekends_off_layer(priority: int = 10) -> BidLayer:
    weekend_filter = BidFilter(criteria=FilterCriteria.WEEKENDS_OFF,
                               filter_type=FilterType.AVOID,
                               value=True,
                               operator="equals",
                               weight=5.0,
                               description="Avoid trips that include weekends")

    return BidLayer(layer_number=0,
                    name="Weekends Off",
                    filters=[weekend_filter],
                    priority=priority,
                    description="Keep my weekends free for family time")


def create_layover_preference_layer(cities: List[str],
                                    priority: int = 7) -> BidLayer:
    filters = []
    for city in cities:
        filter_obj = BidFilter(criteria=FilterCriteria.LAYOVER_CITY,
                               filter_type=FilterType.PREFER,
                               value=city,
                               operator="contains",
                               weight=3.0,
                               description=f"Prefer layovers in {city}")
        filters.append(filter_obj)

    return BidLayer(layer_number=0,
                    name="Favorite Cities",
                    filters=filters,
                    logic_operator="OR",
                    priority=priority,
                    description="Prefer trips to cities I enjoy visiting")


def create_trip_length_layer(min_days: int,
                             max_days: int,
                             priority: int = 5) -> BidLayer:
    min_filter = BidFilter(criteria=FilterCriteria.TRIP_LENGTH,
                           filter_type=FilterType.REQUIRE,
                           value=min_days,
                           operator="greater_than",
                           weight=2.0,
                           description=f"At least {min_days} days")

    max_filter = BidFilter(criteria=FilterCriteria.TRIP_LENGTH,
                           filter_type=FilterType.REQUIRE,
                           value=max_days,
                           operator="less_than",
                           weight=2.0,
                           description=f"No more than {max_days} days")

    return BidLayer(layer_number=0,
                    name="Ideal Trip Length",
                    filters=[min_filter, max_filter],
                    logic_operator="AND",
                    priority=priority,
                    description="Control how long my trips are")
