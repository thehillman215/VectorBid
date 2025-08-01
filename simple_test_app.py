#!/usr/bin/env python3
"""
VectorBid Simple Test App
Copy this entire code into a file called: simple_test_app.py
"""

from flask import Flask, render_template_string, request, jsonify
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple
from enum import Enum
import json


# Simplified Bid Engine (core logic only)
class FilterType(Enum):
    AWARD = "AWARD"
    AVOID = "AVOID"
    PREFER = "PREFER"


class FilterCriteria(Enum):
    WEEKENDS_OFF = "weekends_off"
    TRIP_LENGTH = "trip_length"
    LAYOVER_CITY = "layover_city"
    CREDIT_HOURS = "credit_hours"


@dataclass
class SimpleBidFilter:
    criteria: FilterCriteria
    filter_type: FilterType
    value: Any
    weight: float = 1.0

    def evaluate_trip(self, trip: Dict[str, Any]) -> Tuple[bool, float]:
        """Returns (matches, score)"""
        if self.criteria == FilterCriteria.WEEKENDS_OFF:
            trip_has_weekend = trip.get('includes_weekend', False)
            if self.filter_type == FilterType.AVOID and self.value == True:
                return not trip_has_weekend, self.weight if not trip_has_weekend else 0

        elif self.criteria == FilterCriteria.TRIP_LENGTH:
            trip_days = trip.get('days', 0)
            if self.filter_type == FilterType.PREFER:
                return trip_days == self.value, self.weight if trip_days == self.value else 0

        elif self.criteria == FilterCriteria.LAYOVER_CITY:
            layovers = trip.get('layover_cities', [])
            if self.filter_type == FilterType.PREFER:
                has_city = self.value in layovers
                return has_city, self.weight if has_city else 0

        return False, 0


@dataclass
class SimpleBidLayer:
    name: str
    filters: List[SimpleBidFilter] = field(default_factory=list)
    priority: int = 5

    def evaluate_trip(self, trip: Dict[str, Any]) -> Dict[str, Any]:
        total_score = 0
        matches = []

        for filter_obj in self.filters:
            match, score = filter_obj.evaluate_trip(trip)
            if match:
                matches.append(filter_obj.criteria.value)
                total_score += score * (self.priority / 10.0)

        return {
            'matches': len(matches) > 0,
            'score': total_score,
            'matching_filters': matches
        }


class SimpleBidEngine:

    def __init__(self):
        self.layers = []
        self._setup_default_layers()

    def _setup_default_layers(self):
        """Create some default preference layers"""
        # Layer 1: Avoid weekends
        weekend_layer = SimpleBidLayer(
            name="Weekend Avoidance",
            filters=[
                SimpleBidFilter(criteria=FilterCriteria.WEEKENDS_OFF,
                                filter_type=FilterType.AVOID,
                                value=True,
                                weight=8.0)
            ],
            priority=10)

        # Layer 2: Prefer certain cities
        city_layer = SimpleBidLayer(
            name="Favorite Cities",
            filters=[
                SimpleBidFilter(criteria=FilterCriteria.LAYOVER_CITY,
                                filter_type=FilterType.PREFER,
                                value="LAX",
                                weight=5.0),
                SimpleBidFilter(criteria=FilterCriteria.LAYOVER_CITY,
                                filter_type=FilterType.PREFER,
                                value="SFO",
                                weight=4.0)
            ],
            priority=7)

        # Layer 3: Prefer 3-day trips
        length_layer = SimpleBidLayer(
            name="Ideal Trip Length",
            filters=[
                SimpleBidFilter(criteria=FilterCriteria.TRIP_LENGTH,
                                filter_type=FilterType.PREFER,
                                value=3,
                                weight=3.0)
            ],
            priority=6)

        self.layers = [weekend_layer, city_layer, length_layer]

    def evaluate_trips(self, trips: List[Dict[str,
                                              Any]]) -> List[Dict[str, Any]]:
        """Evaluate all trips against our bid layers"""
        results = []

        for trip in trips:
            trip_result = trip.copy()
            total_score = 0
            all_matches = []
            layer_details = []

            for layer in self.layers:
                layer_eval = layer.evaluate_trip(trip)
                if layer_eval['matches']:
                    total_score += layer_eval['score']
                    all_matches.extend(layer_eval['matching_filters'])

                layer_details.append({
                    'layer_name': layer.name,
                    'matches': layer_eval['matches'],
                    'score': layer_eval['score'],
                    'filters': layer_eval['matching_filters']
                })

            # Set recommendation based on total score
            if total_score >= 15:
                recommendation = "AWARD"
            elif total_score >= 8:
                recommendation = "PREFER"
            elif total_score >= 3:
                recommendation = "CONSIDER"
            else:
                recommendation = "AVOID"

            trip_result.update({
                'total_score': round(total_score, 1),
                'recommendation': recommendation,
                'matching_criteria': list(set(all_matches)),
                'layer_breakdown': layer_details
            })

            results.append(trip_result)

        # Sort by score (highest first)
        results.sort(key=lambda x: x['total_score'], reverse=True)
        return results


# Flask App
app = Flask(__name__)

# Sample trip data
SAMPLE_TRIPS = [{
    'trip_id': 'T001',
    'days': 3,
    'credit_hours': 18.5,
    'includes_weekend': False,
    'layover_cities': ['LAX', 'DEN'],
    'routing': 'BOS-LAX-DEN-BOS',
    'departure_time': '08:00'
}, {
    'trip_id': 'T002',
    'days': 4,
    'credit_hours': 22.0,
    'includes_weekend': True,
    'layover_cities': ['ORD', 'ATL'],
    'routing': 'BOS-ORD-ATL-BOS',
    'departure_time': '23:30'
}, {
    'trip_id': 'T003',
    'days': 2,
    'credit_hours': 12.5,
    'includes_weekend': False,
    'layover_cities': ['SFO'],
    'routing': 'BOS-SFO-BOS',
    'departure_time': '14:00'
}, {
    'trip_id': 'T004',
    'days': 5,
    'credit_hours': 28.0,
    'includes_weekend': True,
    'layover_cities': ['MIA', 'LAX'],
    'routing': 'BOS-MIA-LAX-BOS',
    'departure_time': '06:00'
}]

# Initialize bid engine
bid_engine = SimpleBidEngine()


@app.route('/')
def home():
    """Home page with trip analysis"""
    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>VectorBid - Simple Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
            .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .trip { background: #ecf0f1; margin: 10px 0; padding: 15px; border-radius: 5px; border-left: 5px solid #3498db; }
            .trip.award { border-left-color: #27ae60; }
            .trip.prefer { border-left-color: #f39c12; }
            .trip.consider { border-left-color: #3498db; }
            .trip.avoid { border-left-color: #e74c3c; }
            .score { font-weight: bold; font-size: 1.2em; }
            .recommendation { display: inline-block; padding: 5px 10px; border-radius: 3px; color: white; font-weight: bold; }
            .recommendation.award { background: #27ae60; }
            .recommendation.prefer { background: #f39c12; }
            .recommendation.consider { background: #3498db; }
            .recommendation.avoid { background: #e74c3c; }
            .details { margin-top: 10px; font-size: 0.9em; color: #666; }
            .refresh-btn { background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
            .refresh-btn:hover { background: #2980b9; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🛩️ VectorBid - Enhanced Bid Engine Test</h1>
                <p>Testing our AI-powered pilot bidding assistant with sample trips</p>
            </div>

            <div style="margin-bottom: 20px;">
                <button class="refresh-btn" onclick="location.reload()">🔄 Refresh Analysis</button>
                <a href="/api/trips" style="margin-left: 10px; color: #3498db;">📊 View JSON API</a>
            </div>

            <h2>Trip Analysis Results</h2>
            <div id="trips">
                <!-- Trips will be loaded here -->
            </div>
        </div>

        <script>
            // Load trip analysis
            fetch('/api/trips')
                .then(response => response.json())
                .then(data => {
                    const container = document.getElementById('trips');
                    data.trips.forEach(trip => {
                        const div = document.createElement('div');
                        div.className = `trip ${trip.recommendation.toLowerCase()}`;

                        div.innerHTML = `
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <h3>Trip ${trip.trip_id}</h3>
                                    <p><strong>Route:</strong> ${trip.routing}</p>
                                    <p><strong>Duration:</strong> ${trip.days} days | <strong>Credit:</strong> ${trip.credit_hours} hrs | <strong>Weekend:</strong> ${trip.includes_weekend ? 'Yes' : 'No'}</p>
                                    <p><strong>Layovers:</strong> ${trip.layover_cities.join(', ')}</p>
                                </div>
                                <div style="text-align: right;">
                                    <div class="score">Score: ${trip.total_score}</div>
                                    <div class="recommendation ${trip.recommendation.toLowerCase()}">${trip.recommendation}</div>
                                </div>
                            </div>
                            <div class="details">
                                <strong>Matching Criteria:</strong> ${trip.matching_criteria.length ? trip.matching_criteria.join(', ') : 'None'}<br>
                                <strong>Layer Analysis:</strong> ${trip.layer_breakdown.map(l => `${l.layer_name}(${l.matches ? '✓' : '✗'})`).join(', ')}
                            </div>
                        `;

                        container.appendChild(div);
                    });
                });
        </script>
    </body>
    </html>
    """
    return render_template_string(template)


@app.route('/api/trips')
def api_trips():
    """API endpoint returning analyzed trips"""
    analyzed_trips = bid_engine.evaluate_trips(SAMPLE_TRIPS)

    return jsonify({
        'success': True,
        'trips': analyzed_trips,
        'summary': {
            'total_trips':
            len(analyzed_trips),
            'award_trips':
            len([t for t in analyzed_trips if t['recommendation'] == 'AWARD']),
            'prefer_trips':
            len([t for t in analyzed_trips
                 if t['recommendation'] == 'PREFER']),
            'consider_trips':
            len([
                t for t in analyzed_trips if t['recommendation'] == 'CONSIDER'
            ]),
            'avoid_trips':
            len([t for t in analyzed_trips if t['recommendation'] == 'AVOID'])
        }
    })


@app.route('/api/engine/status')
def api_engine_status():
    """Show bid engine configuration"""
    return jsonify({
        'success': True,
        'engine': {
            'total_layers':
            len(bid_engine.layers),
            'layers': [{
                'name': layer.name,
                'priority': layer.priority,
                'filters': len(layer.filters)
            } for layer in bid_engine.layers]
        }
    })


if __name__ == '__main__':
    print("🚀 Starting VectorBid Simple Test App...")
    print("🌐 Visit: http://localhost:5000")
    print("📊 API: http://localhost:5000/api/trips")
    app.run(debug=True, host='0.0.0.0', port=5000)
