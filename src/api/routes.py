from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, make_response
from datetime import datetime
import logging
from src.lib.pbs_20_layer_system import generate_pbs_compliant_bid_layers

# Import existing functions (preserve your existing imports)
try:
    from src.lib.llm_service import rank_trips_with_ai
except ImportError:
    def rank_trips_with_ai(trips, preferences):
        return []

try:
    from src.lib.schedule_parser.pdf_parser import parse_pdf_schedule
    from src.lib.schedule_parser.csv_parser import parse_csv_schedule
    from src.lib.schedule_parser.txt_parser import parse_txt_schedule
except ImportError:
    def parse_pdf_schedule(file_path):
        return []
    def parse_csv_schedule(file_path):
        return []
    def parse_txt_schedule(file_path):
        return []

try:
    from src.lib.services.db import get_profile, save_profile
except ImportError:
    def get_profile(user_id):
        return {}
    def save_profile(user_id, profile_data):
        pass

try:
    from src.auth.auth_helpers import get_current_user_id
except ImportError:
    def get_current_user_id():
        return '44040350'  # fallback for testing

# Create blueprint
bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

@bp.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')

@bp.route('/onboarding')
def onboarding():
    """User onboarding flow."""
    user_id = get_current_user_id()
    if not user_id:
        return redirect(url_for('main.index'))
    
    try:
        profile = get_profile(user_id)
        return render_template('onboarding.html', profile=profile)
    except:
        return render_template('onboarding.html', profile={})

@bp.route('/process', methods=['POST'])
def process():
    """Process uploaded schedule file with preferences."""
    preferences = request.form.get('preferences', '').strip()
    
    if not preferences:
        flash('Please enter your preferences', 'error')
        return redirect(url_for('main.index'))

    # Handle file upload
    schedule_file = request.files.get('schedule_file')
    trips = []
    
    if schedule_file and schedule_file.filename:
        try:
            filename = schedule_file.filename.lower()
            file_content = schedule_file.read()
            
            # Save temporarily and parse
            temp_path = f'/tmp/{schedule_file.filename}'
            with open(temp_path, 'wb') as f:
                f.write(file_content)
            
            if filename.endswith('.pdf'):
                trips = parse_pdf_schedule(temp_path)
            elif filename.endswith('.csv'):
                trips = parse_csv_schedule(temp_path)
            elif filename.endswith('.txt'):
                trips = parse_txt_schedule(temp_path)
                
        except Exception as e:
            logger.error(f"File processing error: {e}")
            flash('Error processing file. Using sample data.', 'warning')
    
    # If no trips from file, create sample data
    if not trips:
        trips = [
            {"trip_id": "001", "days": 3, "credit_hours": 12.5, "routing": "DEN-LAX-SFO-DEN"},
            {"trip_id": "002", "days": 2, "credit_hours": 8.0, "routing": "DEN-ORD-DEN"},
            {"trip_id": "003", "days": 4, "credit_hours": 18.0, "routing": "DEN-JFK-MIA-DEN"}
        ]

    # Store analysis data in session
    session['trip_analysis'] = {
        'preferences': preferences,
        'total_trips': len(trips),
        'bid_package': {'month_tag': 'current'},
        'trips': trips
    }

    return redirect(url_for('main.results'))

@bp.route("/results")
def results():
    """Display PBS 2.0 compliant layer results - VectorBid's core value."""
    user_id = get_current_user_id() or '44040350'
    
    analysis_data = session.get('last_analysis') or session.get('trip_analysis')
    
    if analysis_data:
        preferences = analysis_data.get('preferences', '')
        
        try:
            pilot_profile = get_profile(user_id) if user_id else {}
        except:
            pilot_profile = {}
        
        # Generate PBS 2.0 compliant 20-layer strategy
        bid_layers = generate_pbs_compliant_bid_layers(preferences, pilot_profile)
        
        session['last_analysis'] = {
            'preferences': preferences,
            'bid_layers': bid_layers,
            'trips_analyzed': analysis_data.get('total_trips', 0),
            'month_tag': analysis_data.get('bid_package', {}).get('month_tag', 'current')
        }
        
        return render_template(
            "pbs_20_layer_template.html",
            bid_layers=bid_layers,
            preferences=preferences,
            analysis={'trips_analyzed': analysis_data.get('total_trips', 0)},
            month_tag=analysis_data.get('bid_package', {}).get('month_tag', 'current'),
            pilot_profile=pilot_profile
        )
    else:
        flash('Please run an analysis first to generate your PBS strategy.', 'info')
        return redirect(url_for('main.index'))

@bp.route('/download_pbs_20_strategy')
def download_pbs_20_strategy():
    """Download complete PBS 2.0 strategy."""
    analysis_data = session.get('last_analysis')
    if not analysis_data:
        flash('No analysis data found.', 'error')
        return redirect(url_for('main.index'))

    preferences = analysis_data.get('preferences', '')
    bid_layers = analysis_data.get('bid_layers', [])
    
    # Create download content
    content = f"""VectorBid PBS 2.0 Strategy
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Preferences: "{preferences}"

PBS 2.0 COMPLIANT 20-LAYER STRATEGY:
{'='*50}

"""
    
    for layer in bid_layers:
        content += f"""
LAYER {layer['layer']}: {layer['description']}
Strategy: {layer['strategy']}
Probability: {layer['probability']}

PBS Commands:
"""
        for i, filter_cmd in enumerate(layer['filters'], 1):
            content += f"  {i}. {filter_cmd}\n"
        content += "\n"
    
    response = make_response(content)
    response.headers['Content-Type'] = 'text/plain'
    response.headers['Content-Disposition'] = f'attachment; filename=pbs20_strategy_{datetime.now().strftime("%Y%m%d")}.txt'
    return response

# Legacy compatibility
def natural_language_to_pbs_filters(preferences_text, pilot_profile=None, trip_data=None):
    """Legacy function for backward compatibility."""
    bid_layers = generate_pbs_compliant_bid_layers(preferences_text, pilot_profile, trip_data)
    return bid_layers[0]['filters'] if bid_layers else ["PREFER MAX_DAYS_OFF"]

@bp.route('/how-to')
def how_to():
    """How-to guide."""
    return render_template('how_to.html')
