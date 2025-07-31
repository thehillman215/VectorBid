"""Flask routes for VectorBid."""

import csv
import io
import json
import logging
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
)
from flask_login import current_user

from schedule_parser import parse_schedule
from llm_service import rank_trips_with_ai
from services.db import get_profile, save_profile
from services.bids import get_matching_bid_packet

bp = Blueprint("main", __name__)


@bp.get("/")
def index():
    # Apply profile requirement check
    user_id = request.headers.get("X-Replit-User-Id")
    if user_id:
        profile = get_profile(user_id)
        if not profile or not profile.get('profile_completed', False):
            # First redirect to how-to page for new users
            return redirect(url_for('main.how_to'))
    
    # Get profile data and matching bid package for authenticated users
    profile = None
    bid_package = None
    if user_id:
        profile = get_profile(user_id)
        if profile and profile.get('profile_completed', False):
            bid_package = get_matching_bid_packet(profile)
    
    return render_template(
        "index.html", 
        user=current_user if current_user.is_authenticated else None,
        profile=profile,
        bid_package=bid_package
    )


@bp.get("/how-to")
def how_to():
    """Full-page how-to guide for new users."""
    return render_template("how_to.html")


@bp.post("/process")
def process_schedule():
    # Apply profile requirement check
    user_id = request.headers.get("X-Replit-User-Id")
    if user_id:
        profile = get_profile(user_id)
        if not profile.get('profile_completed', False):
            return redirect(url_for('welcome.wizard_start'))
    
    uploaded = request.files.get("schedule_file")
    preferences = request.form.get("preferences", "").strip()

    if not uploaded or not preferences:
        flash("Please provide both a schedule file and your preferences.", "error")
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
        flash("No trips extracted. Please verify the schedule format.", "error")
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
        for item in ranked
        if isinstance(item, dict) and "trip_id" in item
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
    return render_template(
        "results.html",
        trips=top_trips,
        preferences=preferences,
        user=current_user if current_user.is_authenticated else None,
    )


@bp.get("/download_csv")
def download_csv():
    # Apply profile requirement check
    user_id = request.headers.get("X-Replit-User-Id")
    if user_id:
        profile = get_profile(user_id)
        if not profile.get('profile_completed', False):
            return redirect(url_for('welcome.wizard_start'))
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
    if not user_id:
        return redirect(url_for("replit_auth.login"))
    
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
        from services.bids import get_bid_packet
        bid_packet = get_bid_packet(month_tag)
        
        if not bid_packet:
            flash("Bid package not found.", "error")
            return redirect(url_for('main.index'))
        
        # Parse the PDF content
        trip_data = parse_schedule(bid_packet.pdf_data, bid_packet.filename)
        
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
                'filename': bid_packet.filename,
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
            'work_life_balance': "I prioritize work-life balance with predictable schedules, weekends off when possible, and reasonable trip lengths that allow for good rest between duties.",
            'credit_hunter': "I want to maximize flight time and credit hours. I prefer longer trips, back-to-back flying, and sequences that build the most hours efficiently.",
            'adventure_seeker': "I love variety and new destinations. I prefer international routes, interesting layovers, and diverse trip patterns that take me to different places.",
            'commuter_friendly': "As a commuter, I need trips that work with my travel to/from base. I prefer trips that start/end at convenient times and allow for reliable commute connections."
        }
        
        if profile['persona'] in persona_preferences:
            preferences.append(persona_preferences[profile['persona']])
    
    # Add custom preferences if provided
    if profile.get('custom_preferences'):
        preferences.append(profile['custom_preferences'])
    
    # Add base-specific preferences
    if profile.get('base'):
        preferences.append(f"I'm based at {profile['base']} so trips starting/ending there are preferred.")
    
    # Add aircraft preferences
    if profile.get('fleet'):
        fleet_str = ', '.join(profile['fleet'])
        preferences.append(f"I'm qualified on {fleet_str} aircraft.")
    
    return ' '.join(preferences) if preferences else "Please rank trips based on general pilot preferences for good work-life balance."


@bp.route("/results")
def results():
    """Display trip ranking results."""
    # Apply profile requirement check
    user_id = get_current_user_id()
    if user_id:
        profile = get_profile(user_id)
        if not profile or not profile.get('profile_completed', False):
            return redirect(url_for('welcome.wizard_start'))
    
    if 'ranked_trips' not in session:
        flash("No analysis results found. Please analyze a bid package first.", "error")
        return redirect(url_for('main.index'))
    
    return render_template("results.html", 
                         ranked_trips=session['ranked_trips'],
                         analysis=session.get('trip_analysis', {}))


@bp.route("/welcome", methods=["GET", "POST"])
def welcome():
    """Profile setup page for new users."""
    user_id = request.headers.get("X-Replit-User-Id")
    if not user_id:
        return redirect(url_for('replit_auth.login'))
    
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
    
    # This route is now handled by the welcome wizard
    return redirect(url_for("welcome.wizard_start"))
