# bid_layers_routes.py
# Flask routes for Enhanced Bid Layers - Copy this entire file

from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from werkzeug.exceptions import BadRequest
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from bid_layers_system import (BidLayersSystem, BidLayer, BidFilter,
                               FilterType, FilterCriteria,
                               create_weekends_off_layer,
                               create_layover_preference_layer,
                               create_trip_length_layer)

# Create blueprint
bid_layers_bp = Blueprint('bid_layers', __name__, url_prefix='/bid-layers')

# In-memory storage (replace with database later)
user_bid_systems = {}


def get_current_user_id() -> str:
    """Get current user ID from session"""
    user_id = request.headers.get("X-Replit-User-Id")
    if user_id:
        return user_id
    return session.get('user_id', 'demo_user')


def get_user_bid_system(user_id: str) -> BidLayersSystem:
    """Get or create bid layers system for user"""
    if user_id not in user_bid_systems:
        system = BidLayersSystem()
        system.add_layer(create_weekends_off_layer(10))
        system.add_layer(
            create_layover_preference_layer(["LAX", "SFO", "DEN"], 8))
        system.add_layer(create_trip_length_layer(2, 4, 6))
        user_bid_systems[user_id] = system
    return user_bid_systems[user_id]


def get_sample_trips() -> List[Dict[str, Any]]:
    """Sample trips for testing"""
    return [{
        'trip_id': 'T001',
        'pairing_id': '001',
        'days': 3,
        'credit_hours': 18.5,
        'includes_weekend': False,
        'layover_cities': ['LAX', 'DEN'],
        'is_red_eye': False,
        'departure_time': '08:00',
        'routing': 'BOS-LAX-DEN-BOS',
        'aircraft_type': 'A320',
        'is_commutable': True,
        'is_international': False
    }, {
        'trip_id': 'T002',
        'pairing_id': '002',
        'days': 4,
        'credit_hours': 22.0,
        'includes_weekend': True,
        'layover_cities': ['ORD', 'ATL'],
        'is_red_eye': True,
        'departure_time': '23:30',
        'routing': 'BOS-ORD-ATL-BOS',
        'aircraft_type': 'B737',
        'is_commutable': False,
        'is_international': False
    }, {
        'trip_id': 'T003',
        'pairing_id': '003',
        'days': 2,
        'credit_hours': 12.5,
        'includes_weekend': False,
        'layover_cities': ['SFO'],
        'is_red_eye': False,
        'departure_time': '14:00',
        'routing': 'BOS-SFO-BOS',
        'aircraft_type': 'A321',
        'is_commutable': True,
        'is_international': False
    }, {
        'trip_id': 'T004',
        'pairing_id': '004',
        'days': 5,
        'credit_hours': 28.0,
        'includes_weekend': True,
        'layover_cities': ['LHR', 'CDG'],
        'is_red_eye': False,
        'departure_time': '19:00',
        'routing': 'BOS-LHR-CDG-BOS',
        'aircraft_type': 'B787',
        'is_commutable': True,
        'is_international': True
    }]


@bid_layers_bp.route('/')
def bid_layers_home():
    """Main bid layers page"""
    user_id = get_current_user_id()
    bid_system = get_user_bid_system(user_id)

    summary = bid_system.get_layer_summary()
    sample_trips = get_sample_trips()
    evaluated_trips = bid_system.evaluate_all_trips(sample_trips)
    pbs_output = bid_system.generate_pbs_output(evaluated_trips)

    stats = {
        'total_layers':
        summary['total_layers'],
        'active_layers':
        summary['active_layers'],
        'trips_analyzed':
        len(evaluated_trips),
        'highly_recommended':
        len([
            t for t in evaluated_trips
            if t['bid_recommendation'] == 'HIGHLY_RECOMMENDED'
        ]),
        'pbs_ready':
        summary['active_layers'] > 0
    }

    return render_template('bid_layers/index.html',
                           layers=summary['layers_detail'],
                           evaluated_trips=evaluated_trips[:10],
                           pbs_output=pbs_output,
                           stats=stats)


@bid_layers_bp.route('/api/layers', methods=['POST'])
def create_layer():
    """Create new layer"""
    try:
        user_id = get_current_user_id()
        bid_system = get_user_bid_system(user_id)

        data = request.get_json()
        if not data:
            raise BadRequest("No data provided")

        required_fields = ['name', 'priority', 'filters']
        for field in required_fields:
            if field not in data:
                raise BadRequest(f"Missing required field: {field}")

        filters = []
        for filter_data in data['filters']:
            try:
                criteria = FilterCriteria(filter_data['criteria'])
                filter_type = FilterType(filter_data['filter_type'])

                value = filter_data['value']
                if criteria in [
                        FilterCriteria.TRIP_LENGTH, FilterCriteria.CREDIT_HOURS
                ]:
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        value = 0
                elif criteria in [
                        FilterCriteria.WEEKENDS_OFF, FilterCriteria.RED_EYE,
                        FilterCriteria.INTERNATIONAL, FilterCriteria.COMMUTABLE
                ]:
                    value = str(value).lower() == 'true'

                bid_filter = BidFilter(
                    criteria=criteria,
                    filter_type=filter_type,
                    value=value,
                    operator=filter_data.get('operator', 'equals'),
                    weight=float(filter_data.get('weight', 3.0)),
                    description=filter_data.get('description', ''))
                filters.append(bid_filter)
            except ValueError as e:
                raise BadRequest(f"Invalid filter data: {e}")

        layer = BidLayer(layer_number=0,
                         name=data['name'],
                         filters=filters,
                         logic_operator=data.get('logic_operator', 'AND'),
                         priority=int(data['priority']),
                         description=data.get('description', ''),
                         is_active=data.get('is_active', True))

        success = bid_system.add_layer(layer)
        if not success:
            raise BadRequest("Maximum number of layers reached (50)")

        return jsonify({
            'success': True,
            'message': 'Layer created successfully',
            'layer_number': layer.layer_number
        })

    except BadRequest as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logging.exception("Error creating layer")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@bid_layers_bp.route('/api/layers/<int:layer_number>', methods=['DELETE'])
def delete_layer(layer_number: int):
    """Delete layer"""
    try:
        user_id = get_current_user_id()
        bid_system = get_user_bid_system(user_id)

        success = bid_system.remove_layer(layer_number)
        if not success:
            return jsonify({'success': False, 'error': 'Layer not found'}), 404

        return jsonify({
            'success': True,
            'message': 'Layer deleted successfully'
        })

    except Exception as e:
        logging.exception("Error deleting layer")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@bid_layers_bp.route('/api/layers/<int:layer_number>/toggle', methods=['POST'])
def toggle_layer(layer_number: int):
    """Toggle layer active status"""
    try:
        user_id = get_current_user_id()
        bid_system = get_user_bid_system(user_id)

        layer_to_toggle = None
        for layer in bid_system.layers:
            if layer.layer_number == layer_number:
                layer_to_toggle = layer
                break

        if not layer_to_toggle:
            return jsonify({'success': False, 'error': 'Layer not found'}), 404

        layer_to_toggle.is_active = not layer_to_toggle.is_active

        return jsonify({
            'success':
            True,
            'is_active':
            layer_to_toggle.is_active,
            'message':
            f'Layer {"activated" if layer_to_toggle.is_active else "deactivated"}'
        })

    except Exception as e:
        logging.exception("Error toggling layer")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@bid_layers_bp.route('/api/analyze', methods=['POST'])
def analyze_trips():
    """Analyze trips with bid layers"""
    try:
        user_id = get_current_user_id()
        bid_system = get_user_bid_system(user_id)

        data = request.get_json() or {}
        trips = data.get('trips', get_sample_trips())

        evaluated_trips = bid_system.evaluate_all_trips(trips)
        pbs_output = bid_system.generate_pbs_output(evaluated_trips)

        stats = {
            'total_trips':
            len(evaluated_trips),
            'highly_recommended':
            len([
                t for t in evaluated_trips
                if t['bid_recommendation'] == 'HIGHLY_RECOMMENDED'
            ]),
            'recommended':
            len([
                t for t in evaluated_trips
                if t['bid_recommendation'] == 'RECOMMENDED'
            ]),
            'consider':
            len([
                t for t in evaluated_trips
                if t['bid_recommendation'] == 'CONSIDER'
            ]),
            'avoid':
            len([
                t for t in evaluated_trips
                if t['bid_recommendation'] == 'AVOID'
            ])
        }

        return jsonify({
            'success': True,
            'evaluated_trips': evaluated_trips,
            'pbs_output': pbs_output,
            'stats': stats
        })

    except Exception as e:
        logging.exception("Error analyzing trips")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


# Template filters
def format_recommendation(recommendation):
    formats = {
        'HIGHLY_RECOMMENDED': {
            'text': 'Excellent Match',
            'class': 'bg-success'
        },
        'RECOMMENDED': {
            'text': 'Good Match',
            'class': 'bg-primary'
        },
        'CONSIDER': {
            'text': 'Consider',
            'class': 'bg-warning'
        },
        'AVOID': {
            'text': 'Avoid',
            'class': 'bg-danger'
        }
    }
    return formats.get(recommendation, {
        'text': recommendation,
        'class': 'bg-secondary'
    })


def format_score(score):
    if score >= 8.0:
        return {'class': 'score-excellent', 'text': f'{score:.1f}'}
    elif score >= 5.0:
        return {'class': 'score-good', 'text': f'{score:.1f}'}
    elif score >= 2.0:
        return {'class': 'score-fair', 'text': f'{score:.1f}'}
    else:
        return {'class': 'score-poor', 'text': f'{score:.1f}'}


@bid_layers_bp.app_template_filter('format_recommendation')
def format_recommendation_filter(recommendation):
    return format_recommendation(recommendation)


@bid_layers_bp.app_template_filter('format_score')
def format_score_filter(score):
    return format_score(score)
