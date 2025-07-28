
"""Flask routes for VectorBid."""
import csv
import io
import json
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from flask_login import current_user

from schedule_parser import parse_schedule_file
from llm_service import rank_trips_with_ai

bp = Blueprint('main', __name__)

@bp.get('/')
def index():
    return render_template('index.html', user=current_user if current_user.is_authenticated else None)


@bp.post('/process')
def process_schedule():
    uploaded = request.files.get('schedule_file')
    preferences = request.form.get('preferences', '').strip()

    if not uploaded or not preferences:
        flash('Please provide both a schedule file and your preferences.', 'error')
        return redirect(url_for('main.index'))

    try:
        trips = parse_schedule_file(uploaded)
    except Exception as exc:
        logging.exception('Parsing error')
        flash(f'Error parsing schedule: {exc}', 'error')
        return redirect(url_for('main.index'))

    if not trips:
        flash('No trips extracted. Please verify the schedule format.', 'error')
        return redirect(url_for('main.index'))

    try:
        ranked = rank_trips_with_ai(trips, preferences)
    except Exception as exc:
        logging.exception('LLM ranking error')
        flash(f'AI ranking failed: {exc}', 'error')
        return redirect(url_for('main.index'))

    # Create mapping of ranked trips
    ranked_by_id = {str(item['trip_id']): item for item in ranked if isinstance(item, dict) and 'trip_id' in item}
    
    # Match trips with rankings
    top_trips = []
    for trip in trips:
        trip_id = str(trip['trip_id'])
        if trip_id in ranked_by_id:
            ranked_info = ranked_by_id[trip_id]
            combined_trip = trip.copy()
            combined_trip['rank'] = ranked_info.get('rank', 99)
            combined_trip['comment'] = ranked_info.get('comment', 'No comment')
            top_trips.append(combined_trip)
    
    # If no trips matched, show first few trips with default ranking
    if not top_trips and trips:
        for i, trip in enumerate(trips[:5]):
            combined_trip = trip.copy()
            combined_trip['rank'] = i + 1
            combined_trip['comment'] = 'Trip available for bidding'
            top_trips.append(combined_trip)

    # Sort by rank
    top_trips.sort(key=lambda x: x.get('rank', 99))

    session['ranked_trips'] = top_trips  # store for download
    return render_template('results.html', trips=top_trips, preferences=preferences)


@bp.get('/download_csv')
def download_csv():
    trips = session.get('ranked_trips')
    if not trips:
        flash('No ranked trips to download.', 'error')
        return redirect(url_for('main.index'))

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=['rank', 'trip_id', 'days', 'credit_hours', 'routing', 'includes_weekend', 'comment'])
    writer.writeheader()
    writer.writerows(trips)
    buffer.seek(0)
    return send_file(
        io.BytesIO(buffer.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='vectorbid_ranked_trips.csv'
    )
