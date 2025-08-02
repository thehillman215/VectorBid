"""Flask routes for VectorBid."""

import csv
import io
import json
import logging
from datetime import datetime
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_file,
    current_app,
    jsonify,
    make_response,
)
from flask_login import current_user

from src.lib.schedule_parser import parse_schedule
from src.lib.llm_service import rank_trips_with_ai
from src.lib.services.db import get_profile, save_profile
from src.lib.services.bids import get_matching_bid_packet
from src.auth.auth_helpers import get_current_user_id, requires_onboarding

# Configure logger
logger = logging.getLogger(__name__)

bp = Blueprint("main", __name__)


@bp.get("/")
def index():
    # Always use test user for open testing
    user_id = '44040350'

    # Get profile and create default if doesn't exist
    profile = get_profile(user_id)
    if not profile:
        # Create a default profile for testing
        default_profile = {
            'airline': 'United Airlines',
            'base': 'Denver (DEN)',
            'seat': 'Captain',
            'fleet': ['737', '787'],
            'seniority': 'Mid-level',
            'persona': 'quality_of_life',
            'onboard_complete': True,
            'profile_completed': True
        }
        save_profile(user_id, default_profile)
        profile = default_profile

    # Get matching bid package
    bid_package = get_matching_bid_packet(profile)

    return render_template("index.html",
                           user=user_id,
                           profile=profile,
                           bid_package=bid_package)


@bp.get("/how-to")
def how_to():
    """Full-page how-to guide for new users."""
    return render_template("how_to.html")


@bp.get("/debug")
def debug():
    """Debug page to check authentication and headers."""
    user_id = get_current_user_id()
    headers = dict(request.headers)
    profile = None

    if user_id:
        profile = get_profile(user_id)

    return f"""
    <html>
    <head><title>Debug Info</title></head>
    <body style="background: #1a1a1a; color: white; font-family: monospace; padding: 20px;">
        <h2>VectorBid Debug Information</h2>

        <h3>Authentication Status:</h3>
        <p>User ID: <strong>{user_id or 'Not authenticated'}</strong></p>

        <h3>Received Headers:</h3>
        <ul>
        {''.join([f'<li>{k}: {v}</li>' for k, v in headers.items()])}
        </ul>

        <h3>Profile Data:</h3>
        <pre>{profile if profile else 'No profile data'}</pre>

        <h3>Test Links:</h3>
        <p><a href="/" style="color: lightblue;">← Back to Home</a></p>
        <p><a href="/onboarding" style="color: lightblue;">Test Onboarding →</a></p>

        <h3>Manual Test:</h3>
        <p>To test with authentication, add header: X-Replit-User-Id: 44040350</p>
    </body>
    </html>
    """


@bp.route("/onboarding")
@bp.route("/onboarding/<int:step>")
def onboarding(step=1):
    """Onboarding wizard for new users and profile updates."""
    user_id = get_current_user_id()

    # Test mode: if URL has ?test=true, use test user ID
    if request.args.get('test') == 'true':
        user_id = '44040350'

    if not user_id:
        return redirect(url_for('main.index'))

    # Get current profile
    profile = get_profile(user_id)

    # Handle step navigation
    step = max(1, min(3, step))

    return render_template("onboarding.html", step=step, profile=profile)


@bp.post("/onboarding")
def onboarding_submit():
    """Handle onboarding form submissions."""
    user_id = get_current_user_id()

    # Test mode: if form has test=true, use test user ID
    if request.form.get('test') == 'true':
        user_id = '44040350'

    if not user_id:
        return redirect(url_for('main.index'))

    step = int(request.form.get('step', 1))
    profile = get_profile(user_id)

    if step == 1:
        # Save basic info
        save_profile(
            user_id, {
                'airline': request.form.get('airline'),
                'base': request.form.get('base'),
                'seat': request.form.get('seat'),
            })
        return redirect(url_for('main.onboarding', step=2))

    elif step == 2:
        # Save fleet and seniority
        fleet_str = request.form.get('fleet', '')
        fleet = [f.strip() for f in fleet_str.split(',') if f.strip()]

        save_profile(user_id, {
            'fleet': fleet,
            'seniority': int(request.form.get('seniority', 0)),
        })
        return redirect(url_for('main.onboarding', step=3))

    elif step == 3:
        # Complete onboarding
        profile = get_profile(user_id)
        was_already_complete = profile.get('onboard_complete', False)

        save_profile(
            user_id,
            {
                'onboard_complete': True,
                'profile_completed': True,  # Legacy compatibility
            })

        if was_already_complete:
            flash("Profile updated successfully!", "success")
        else:
            flash("Welcome to VectorBid! Your profile is now set up.",
                  "success")

        return redirect(url_for('main.index'))

    return redirect(url_for('main.onboarding'))


@bp.post("/process")
@requires_onboarding
def process_schedule():
    user_id = get_current_user_id()

    uploaded = request.files.get("schedule_file")
    preferences = request.form.get("preferences", "").strip()

    if not uploaded or not preferences:
        flash("Please provide both a schedule file and your preferences.",
              "error")
        return redirect(url_for("main.index"))

    try:
        filename = uploaded.filename or "unknown.txt"
        raw_trips = parse_schedule(uploaded.read(), filename)
        # Convert new parser format to expected format for compatibility
        trips = []
        for trip in raw_trips:
            formatted_trip = {
                "trip_id": trip.get("id", ""),
                "days": trip.get("days", 0),
                "credit_hours": trip.get("credit", 0.0),
                "routing": trip.get("routing", ""),
                "dates": trip.get("dates", ""),
                "includes_weekend": trip.get("includes_weekend", False),
                "raw": trip.get("raw", ""),
            }
            trips.append(formatted_trip)
    except Exception as exc:
        logging.exception("Parsing error")
        flash(f"Error parsing schedule: {exc}", "error")
        return redirect(url_for("main.index"))

    if not trips:
        flash("No trips extracted. Please verify the schedule format.",
              "error")
        return redirect(url_for("main.index"))

    try:
        ranked = rank_trips_with_ai(trips, preferences)
    except Exception as exc:
        logging.exception("LLM ranking error")
        flash(f"AI ranking failed: {exc}", "error")
        return redirect(url_for("main.index"))

    # Create mapping of ranked trips
    ranked_by_id = {
        str(item["trip_id"]): item
        for item in ranked if isinstance(item, dict) and "trip_id" in item
    }

    # Match trips with rankings
    top_trips = []
    for trip in trips:
        trip_id = str(trip["trip_id"])
        if trip_id in ranked_by_id:
            ranked_info = ranked_by_id[trip_id]
            combined_trip = trip.copy()
            combined_trip["rank"] = ranked_info.get("rank", 99)
            combined_trip["comment"] = ranked_info.get("comment", "No comment")
            top_trips.append(combined_trip)

    # If no trips matched, show first few trips with default ranking
    if not top_trips and trips:
        for i, trip in enumerate(trips[:5]):
            combined_trip = trip.copy()
            combined_trip["rank"] = i + 1
            combined_trip["comment"] = "Trip available for bidding"
            top_trips.append(combined_trip)

    # Sort by rank
    top_trips.sort(key=lambda x: x.get("rank", 99))

    session["ranked_trips"] = top_trips  # store for download

    # Generate PBS filters from preferences
    pbs_filters = natural_language_to_pbs_filters(preferences, trips)

    # Store PBS analysis in session for download
    session['last_analysis'] = {
        'preferences': preferences,
        'pbs_filters': pbs_filters,
        'trips_analyzed': len(trips),
        'month_tag': 'uploaded_file'
    }

    # Return PBS results instead of trip rankings
    return render_template("pbs_results.html",
                           filters=pbs_filters,
                           preferences=preferences,
                           analysis={'trips_analyzed': len(trips)},
                           month_tag='uploaded_file')


@bp.get("/download_csv")
def download_csv():
    # Apply profile requirement check
    user_id = request.headers.get("X-Replit-User-Id")
    if user_id:
        profile = get_profile(user_id)
        if not profile.get('profile_completed', False):
            return redirect(url_for('main.onboarding'))
    trips = session.get("ranked_trips")
    if not trips:
        flash("No ranked trips to download.", "error")
        return redirect(url_for("main.index"))

    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=[
            "rank",
            "trip_id",
            "days",
            "credit_hours",
            "routing",
            "includes_weekend",
            "comment",
        ],
    )
    writer.writeheader()
    writer.writerows(trips)
    buffer.seek(0)
    return send_file(
        io.BytesIO(buffer.getvalue().encode()),
        mimetype="text/csv",
        as_attachment=True,
        download_name="vectorbid_ranked_trips.csv",
    )


@bp.route("/analyze_bid_package", methods=["POST"])
def analyze_bid_package():
    """Analyze bid package with AI based on user preferences."""
    user_id = get_current_user_id()

    # Test mode: if form has test=true, use test user ID
    if request.form.get('test') == 'true':
        user_id = '44040350'

    if not user_id:
        flash("Please log in to analyze bid packages.", "error")
        return redirect(url_for("main.index"))

    # Get profile and preferences
    profile = get_profile(user_id)
    if not profile or not profile.get('profile_completed', False):
        flash("Please complete your profile first.", "error")
        return redirect(url_for('welcome.wizard_start'))

    month_tag = request.form.get('month_tag')
    if not month_tag:
        flash("No bid package selected.", "error")
        return redirect(url_for('main.index'))

    try:
        # Get the bid package content
        from src.lib.services.bids import get_bid_packet_info, get_bid_packet_path
        bid_packet_info = get_bid_packet_info(month_tag)
        bid_packet_path = get_bid_packet_path(month_tag)

        if not bid_packet_info or not bid_packet_path:
            flash("Bid package not found.", "error")
            return redirect(url_for('main.index'))

        # Read the PDF content
        with open(bid_packet_path, 'rb') as f:
            pdf_data = f.read()

        # Parse the PDF content
        trip_data = parse_schedule(pdf_data, bid_packet_info['filename'])

        if not trip_data:
            flash("Could not parse trip data from bid package.", "error")
            return redirect(url_for('main.index'))

        # Get user preferences based on profile
        preferences = build_preferences_from_profile(profile)

        # Rank trips using AI
        ranked_trips = rank_trips_with_ai(trip_data, preferences)

        if not ranked_trips:
            flash("Could not analyze trips. Please try again.", "error")
            return redirect(url_for('main.index'))

        # Store results in session for results page
        session['ranked_trips'] = ranked_trips
        session['trip_analysis'] = {
            'total_trips': len(trip_data),
            'preferences': preferences,
            'bid_package': {
                'filename': bid_packet_info['filename'],
                'month_tag': month_tag
            }
        }

        return redirect(url_for('main.results'))

    except Exception as e:
        flash(f"Error analyzing bid package: {str(e)}", "error")
        return redirect(url_for('main.index'))


def build_preferences_from_profile(profile):
    """Build preference string from user profile."""
    preferences = []

    # Add persona-based preferences
    if profile.get('persona'):
        persona_preferences = {
            'work_life_balance':
            "I prioritize work-life balance with predictable schedules, weekends off when possible, and reasonable trip lengths that allow for good rest between duties.",
            'credit_hunter':
            "I want to maximize flight time and credit hours. I prefer longer trips, back-to-back flying, and sequences that build the most hours efficiently.",
            'adventure_seeker':
            "I love variety and new destinations. I prefer international routes, interesting layovers, and diverse trip patterns that take me to different places.",
            'commuter_friendly':
            "As a commuter, I need trips that work with my travel to/from base. I prefer trips that start/end at convenient times and allow for reliable commute connections."
        }

        if profile['persona'] in persona_preferences:
            preferences.append(persona_preferences[profile['persona']])

    # Add custom preferences if provided
    if profile.get('custom_preferences'):
        preferences.append(profile['custom_preferences'])

    # Add base-specific preferences
    if profile.get('base'):
        preferences.append(
            f"I'm based at {profile['base']} so trips starting/ending there are preferred."
        )

    # Add aircraft preferences
    if profile.get('fleet'):
        fleet_str = ', '.join(profile['fleet'])
        preferences.append(f"I'm qualified on {fleet_str} aircraft.")

    return ' '.join(
        preferences
    ) if preferences else "Please rank trips based on general pilot preferences for good work-life balance."


@bp.route("/results")
def results():
    """Display PBS filter results - ALWAYS show PBS commands, never trip lists."""
    # Always use test user for open testing
    user_id = '44040350'

    # Check if we have real analysis data from analyze_bid_package
    if 'trip_analysis' in session and 'ranked_trips' in session:
        # We have real data from analyze_bid_package - show PBS filters
        trip_analysis = session['trip_analysis']
        preferences = trip_analysis.get('preferences', '')

        # Generate PBS filters from the preferences
        pbs_filters = natural_language_to_pbs_filters(preferences,
                                                      session['ranked_trips'])

        # Store PBS analysis in session for download
        session['last_analysis'] = {
            'preferences':
            preferences,
            'pbs_filters':
            pbs_filters,
            'trips_analyzed':
            trip_analysis.get('total_trips', 0),
            'month_tag':
            trip_analysis.get('bid_package', {}).get('month_tag',
                                                     'analyzed_package')
        }

        # Show PBS results
        return render_template(
            "pbs_results.html",
            filters=pbs_filters,
            preferences=preferences,
            analysis={'trips_analyzed': trip_analysis.get('total_trips', 0)},
            month_tag=trip_analysis.get('bid_package',
                                        {}).get('month_tag',
                                                'analyzed_package'))

    # Fallback: show sample data if no real analysis exists
    if 'ranked_trips' not in session:
        # Create sample trip data for open testing
        session['ranked_trips'] = [{
            'trip_id':
            'UA101',
            'pairing_id':
            'UA101',
            'days':
            3,
            'credit_hours':
            15.2,
            'routing':
            'DEN-ORD-LAX-DEN',
            'dates':
            'Jan 15-17',
            'includes_weekend':
            True,
            'aircraft':
            '737',
            'score':
            9,
            'comment':
            'Perfect for work-life balance with weekend return'
        }, {
            'trip_id':
            'UA205',
            'pairing_id':
            'UA205',
            'days':
            4,
            'credit_hours':
            22.8,
            'routing':
            'DEN-SFO-NRT-SFO-DEN',
            'dates':
            'Jan 18-21',
            'includes_weekend':
            False,
            'aircraft':
            '787',
            'score':
            8,
            'comment':
            'International route with good layover in Tokyo'
        }, {
            'trip_id':
            'UA312',
            'pairing_id':
            'UA312',
            'days':
            2,
            'credit_hours':
            12.5,
            'routing':
            'DEN-PHX-DEN',
            'dates':
            'Jan 22-23',
            'includes_weekend':
            False,
            'aircraft':
            '737',
            'score':
            7,
            'comment':
            'Quick turnaround, good for commuters'
        }, {
            'trip_id':
            'UA428',
            'pairing_id':
            'UA428',
            'days':
            3,
            'credit_hours':
            18.7,
            'routing':
            'DEN-IAH-MIA-IAH-DEN',
            'dates':
            'Jan 24-26',
            'includes_weekend':
            True,
            'aircraft':
            '737',
            'score':
            6,
            'comment':
            'Miami layover but weekend work required'
        }, {
            'trip_id':
            'UA535',
            'pairing_id':
            'UA535',
            'days':
            4,
            'credit_hours':
            25.3,
            'routing':
            'DEN-LHR-FRA-LHR-DEN',
            'dates':
            'Jan 27-30',
            'includes_weekend':
            False,
            'aircraft':
            '787',
            'score':
            8,
            'comment':
            'European route with excellent credit hours'
        }]
        session['trip_analysis'] = {
            'total_trips': 5,
            'preferences':
            'I prefer good work-life balance with weekends off and reasonable trip lengths',
            'optimization_score': 87,
            'bid_package': {
                'filename': 'Sample_Bid_Package.pdf',
                'month_tag': 'demo_package'
            }
        }

    # Always generate PBS filters from preferences (real or sample)
    trip_analysis = session.get('trip_analysis', {})
    ranked_trips = session.get('ranked_trips', [])

    # Get preferences from analysis or create default
    preferences = trip_analysis.get(
        'preferences',
        'I prefer good work-life balance with weekends off and reasonable trip lengths'
    )

    # Generate PBS filters from preferences
    pbs_filters = natural_language_to_pbs_filters(preferences, ranked_trips)

    # Store PBS analysis in session for download
    session['last_analysis'] = {
        'preferences':
        preferences,
        'pbs_filters':
        pbs_filters,
        'trips_analyzed':
        len(ranked_trips),
        'month_tag':
        trip_analysis.get('bid_package', {}).get('month_tag', 'demo_package')
    }

    # ALWAYS show PBS results template - never trip lists
    return render_template("pbs_results.html",
                           filters=pbs_filters,
                           preferences=preferences,
                           analysis={'trips_analyzed': len(ranked_trips)},
                           month_tag=trip_analysis.get('bid_package', {}).get(
                               'month_tag', 'demo_package'))


@bp.route("/save-custom-ranking", methods=["POST"])
def save_custom_ranking():
    """Save user's custom trip ranking preferences."""
    try:
        user_id = get_current_user_id()

        # Test mode: always allow in test scenarios
        if not user_id:
            user_id = '44040350'  # Use test user ID

        custom_ranking = request.get_json()
        if not custom_ranking:
            return {"error": "No ranking data provided"}, 400

        # Store custom ranking in session for now
        # In a full implementation, you'd save this to the database
        session['custom_ranking'] = custom_ranking
        session['ranking_mode'] = 'custom'

        return {
            "success": True,
            "message": "Custom ranking saved successfully"
        }

    except Exception as e:
        current_app.logger.error(f"Save ranking error: {str(e)}")
        return {"error": f"Failed to save ranking: {str(e)}"}, 500


@bp.get("/test-results")
def test_results():
    """Quick test route for results page - bypasses authentication and shows sample data."""
    # Create sample trip data for testing
    sample_trips = [{
        'trip_id':
        'UA101',
        'pairing_id':
        'UA101',
        'days':
        3,
        'credit_hours':
        15.2,
        'routing':
        'DEN-ORD-LAX-DEN',
        'dates':
        'Jan 15-17',
        'includes_weekend':
        True,
        'aircraft':
        '737',
        'score':
        9,
        'comment':
        'Perfect for work-life balance with weekend return'
    }, {
        'trip_id': 'UA205',
        'pairing_id': 'UA205',
        'days': 4,
        'credit_hours': 22.8,
        'routing': 'DEN-SFO-NRT-SFO-DEN',
        'dates': 'Jan 18-21',
        'includes_weekend': False,
        'aircraft': '787',
        'score': 8,
        'comment': 'International route with good layover in Tokyo'
    }, {
        'trip_id': 'UA312',
        'pairing_id': 'UA312',
        'days': 2,
        'credit_hours': 12.5,
        'routing': 'DEN-PHX-DEN',
        'dates': 'Jan 22-23',
        'includes_weekend': False,
        'aircraft': '737',
        'score': 7,
        'comment': 'Quick turnaround, good for commuters'
    }, {
        'trip_id': 'UA428',
        'pairing_id': 'UA428',
        'days': 3,
        'credit_hours': 18.7,
        'routing': 'DEN-IAH-MIA-IAH-DEN',
        'dates': 'Jan 24-26',
        'includes_weekend': True,
        'aircraft': '737',
        'score': 6,
        'comment': 'Miami layover but weekend work required'
    }, {
        'trip_id': 'UA535',
        'pairing_id': 'UA535',
        'days': 4,
        'credit_hours': 25.3,
        'routing': 'DEN-LHR-FRA-LHR-DEN',
        'dates': 'Jan 27-30',
        'includes_weekend': False,
        'aircraft': '787',
        'score': 8,
        'comment': 'European route with excellent credit hours'
    }]

    sample_analysis = {
        'total_trips': 5,
        'optimization_score': 87,
        'bid_package': {
            'filename': 'Sample_Bid_Package.pdf'
        }
    }

    return render_template("results_minimal.html",
                           ranked_trips=sample_trips,
                           analysis=sample_analysis)


@bp.route("/welcome", methods=["GET", "POST"])
def welcome():
    """Profile setup page for new users."""
    user_id = request.headers.get("X-Replit-User-Id")
    if not user_id:
        return redirect(url_for('main.index'))

    if request.method == "GET":
        # Load existing profile data
        profile = get_profile(user_id)
        return render_template("welcome.html", profile=profile)

    # Handle POST - save profile data
    profile_data = {
        "airline": request.form.get("airline", "").strip() or None,
        "fleet": request.form.getlist("fleet"),  # Multiple selections
        "seat": request.form.get("seat", "").strip() or None,
        "base": request.form.get("base", "").strip() or None,
        "seniority": None,
        "profile_completed": True
    }

    # Parse seniority as integer
    seniority_str = request.form.get("seniority", "").strip()
    if seniority_str and seniority_str.isdigit():
        profile_data["seniority"] = int(seniority_str)

    try:
        save_profile(user_id, profile_data)
        flash("Profile updated successfully!", "success")
        return redirect(url_for("main.index"))
    except Exception as e:
        flash(f"Error saving profile: {str(e)}", "error")
        return render_template("welcome.html", profile=get_profile(user_id))


# PBS Filter System Functions
def natural_language_to_pbs_filters(preferences_text, trip_data=None):
    """Convert natural language preferences to PBS filter commands."""
    if not preferences_text:
        return []

    filters = []
    text_lower = preferences_text.lower()

    # Weekend preferences
    if any(phrase in text_lower
           for phrase in ['weekends off', 'weekend off', 'no weekends']):
        filters.append("AVOID TRIPS IF DUTY_PERIOD OVERLAPS SAT OR SUN")

    # Trip length preferences
    if 'short trip' in text_lower or 'day trip' in text_lower:
        filters.append("PREFER TRIPS WITH DUTY_DAYS <= 2")
    elif 'long trip' in text_lower:
        filters.append("PREFER TRIPS WITH DUTY_DAYS >= 4")

    # Commute preferences
    if any(phrase in text_lower
           for phrase in ['easy commute', 'avoid commute', 'commutable']):
        filters.append(
            "PREFER TRIPS STARTING AFTER 1000 ON MON,TUE,WED,THU,FRI")

    # International preferences
    if 'international' in text_lower:
        if 'avoid' in text_lower or 'no' in text_lower:
            filters.append("AVOID TRIPS WITH DESTINATION INTL")
        else:
            filters.append("PREFER TRIPS WITH DESTINATION INTL")

    # Early morning preferences
    if any(phrase in text_lower
           for phrase in ['no early', 'avoid early', 'late start']):
        filters.append("AVOID TRIPS STARTING BEFORE 0800")

    # Red-eye preferences
    if any(phrase in text_lower
           for phrase in ['no redeye', 'avoid redeye', 'no red-eye']):
        filters.append("AVOID TRIPS WITH DEPARTURE_TIME BETWEEN 2200 AND 0559")

    # Home every night
    if any(phrase in text_lower
           for phrase in ['home every night', 'home daily', 'no overnights']):
        filters.append("PREFER TRIPS WITH DUTY_DAYS = 1")

    # Maximum days off
    if 'days off' in text_lower:
        filters.append("PREFER MAX_DAYS_OFF")

    # Add a catch-all preference if no specific filters matched
    if not filters:
        filters.append("PREFER TRIPS WITH GOOD_QUALITY_OF_LIFE")

    return filters


@bp.route('/preview_pbs_filters', methods=['POST'])
def preview_pbs_filters():
    """Preview PBS filters from preferences without full analysis."""
    try:
        data = request.get_json()
        preferences = data.get('preferences', '')

        if not preferences:
            return jsonify({'error': 'No preferences provided'}), 400

        # Generate PBS filters
        filters = natural_language_to_pbs_filters(preferences)

        return jsonify({
            'filters': filters,
            'preview': True,
            'count': len(filters)
        })

    except Exception as e:
        logger.error(f"PBS filter preview error: {e}")
        return jsonify({'error': 'Failed to generate preview'}), 500


@bp.route('/download_pbs_filters')
def download_pbs_filters():
    """Download PBS filters as text file instead of CSV."""
    try:
        # Get the most recent analysis for this user
        user_id = get_current_user_id()
        if not user_id:
            flash('Please log in to download filters', 'error')
            return redirect(url_for('replit_auth.login'))

        # Try to get the last analysis from session or database
        analysis_data = session.get('last_analysis')
        if not analysis_data:
            # Fallback: try to get from database
            from src.core.models import BidAnalysis
            recent_analysis = BidAnalysis.query.filter_by(
                user_id=user_id).order_by(
                    BidAnalysis.created_at.desc()).first()
            if recent_analysis:
                analysis_data = recent_analysis.results

        if not analysis_data:
            flash('No analysis data found. Please run an analysis first.',
                  'error')
            return redirect(url_for('main.index'))

        # Get preferences from analysis data
        preferences = analysis_data.get('preferences', '')

        # Generate PBS filters
        filters = natural_language_to_pbs_filters(preferences)

        # Create PBS filter file content
        filter_content = f"""VectorBid PBS Filters
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Preferences: {preferences}

PBS Filter Commands:
{'=' * 50}

"""

        for i, filter_cmd in enumerate(filters, 1):
            filter_content += f"{i:2d}. {filter_cmd}\n"

        filter_content += f"""

{'=' * 50}
Usage Instructions:
1. Copy the filter commands above
2. Log into your airline's PBS system
3. Paste these commands into your bid preferences
4. Adjust priority order as needed
5. Submit your bid

Note: These filters are generated based on your preferences.
Please review and modify as needed for your specific situation.
"""

        # Create response with text file
        response = make_response(filter_content)
        response.headers['Content-Type'] = 'text/plain'
        response.headers[
            'Content-Disposition'] = f'attachment; filename=vectorbid_pbs_filters_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'

        return response

    except Exception as e:
        logger.error(f"PBS filter download error: {e}")
        flash('Error generating PBS filters', 'error')
        return redirect(url_for('main.index'))
