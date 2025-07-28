import json
import csv
import io
from flask import session, render_template, request, redirect, url_for, flash, make_response, jsonify
from flask_login import current_user
from werkzeug.utils import secure_filename
import os

from app import app, db
from replit_auth import require_login, make_replit_blueprint
from models import ScheduleData
from schedule_parser import parse_schedule_file
from llm_service import rank_trips_with_ai

# Register the Replit Auth blueprint
app.register_blueprint(make_replit_blueprint(), url_prefix="/auth")


# Make session permanent
@app.before_request
def make_session_permanent():
    session.permanent = True


@app.route('/')
def index():
    """Landing page with upload form for authenticated users, login prompt for others"""
    if current_user.is_authenticated:
        # Show upload form for logged-in users
        return render_template('index.html', user=current_user)
    else:
        # Show landing page with login button for anonymous users
        return render_template('index.html', user=None)


@app.route('/process', methods=['POST'])
@require_login
def process_schedule():
    """Handle file upload, parse schedule, and rank trips with AI"""
    try:
        # Check if file was uploaded
        if 'schedule_file' not in request.files:
            flash('No file uploaded. Please select a schedule file.', 'error')
            return redirect(url_for('index'))
        
        file = request.files['schedule_file']
        preferences = request.form.get('preferences', '').strip()
        
        if file.filename == '':
            flash('No file selected. Please choose a schedule file.', 'error')
            return redirect(url_for('index'))
        
        if not preferences:
            flash('Please enter your trip preferences.', 'error')
            return redirect(url_for('index'))
        
        # Validate file type
        allowed_extensions = {'.pdf', '.csv', '.txt'}
        if not file.filename:
            flash('Invalid filename.', 'error')
            return redirect(url_for('index'))
            
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            flash('Invalid file type. Please upload a PDF, CSV, or text file.', 'error')
            return redirect(url_for('index'))
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join('/tmp', filename)
        file.save(temp_path)
        
        try:
            # Parse the schedule file
            trips = parse_schedule_file(temp_path, file_ext)
            
            if not trips:
                flash('No trips found in the uploaded file. Please check the file format.', 'error')
                return redirect(url_for('index'))
            
            # Rank trips using AI
            ranking_results = rank_trips_with_ai(trips, preferences)
            
            # Store results in database
            schedule_data = ScheduleData()
            schedule_data.user_id = current_user.id
            schedule_data.filename = filename
            schedule_data.preferences = preferences
            schedule_data.trips_data = json.dumps(trips)
            schedule_data.ranking_results = json.dumps(ranking_results)
            db.session.add(schedule_data)
            db.session.commit()
            
            # Store in session for download
            session['last_ranking_id'] = schedule_data.id
            
            return render_template('results.html', 
                                 user=current_user,
                                 trips=trips,
                                 ranking=ranking_results,
                                 preferences=preferences,
                                 filename=filename)
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    except Exception as e:
        app.logger.error(f"Error processing schedule: {str(e)}")
        flash(f'Error processing schedule: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/download')
@require_login
def download_ranking():
    """Download the ranking results as CSV"""
    try:
        ranking_id = session.get('last_ranking_id')
        if not ranking_id:
            flash('No ranking data found. Please process a schedule first.', 'error')
            return redirect(url_for('index'))
        
        # Get the schedule data
        schedule_data = ScheduleData.query.filter_by(
            id=ranking_id,
            user_id=current_user.id
        ).first()
        
        if not schedule_data:
            flash('Ranking data not found.', 'error')
            return redirect(url_for('index'))
        
        # Parse the data
        trips = json.loads(schedule_data.trips_data)
        ranking = json.loads(schedule_data.ranking_results)
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Rank', 'Trip ID', 'Duration (Days)', 'Dates', 'Routing', 'Credit Hours', 'Includes Weekend', 'AI Comment'])
        
        # Write ranking data
        for i, ranked_trip in enumerate(ranking, 1):
            trip_id = ranked_trip['trip_id']
            comment = ranked_trip.get('comment', '')
            
            # Find the corresponding trip details
            trip_details = next((t for t in trips if t['id'] == trip_id), {})
            
            writer.writerow([
                i,
                trip_id,
                trip_details.get('duration', 'N/A'),
                trip_details.get('dates', 'N/A'),
                trip_details.get('routing', 'N/A'),
                trip_details.get('credit_hours', 'N/A'),
                'Yes' if trip_details.get('includes_weekend', False) else 'No',
                comment
            ])
        
        # Create response
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=trip_ranking_{ranking_id}.csv'
        
        return response
    
    except Exception as e:
        app.logger.error(f"Error downloading ranking: {str(e)}")
        flash(f'Error downloading ranking: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.errorhandler(404)
def not_found(error):
    return render_template('403.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    app.logger.error(f"Internal server error: {str(error)}")
    flash('An internal error occurred. Please try again.', 'error')
    return redirect(url_for('index'))
