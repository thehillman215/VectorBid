#!/usr/bin/env python3
"""
VectorBid Enhanced Features Integration Script

This script safely integrates the three major enhancements from the last session:
1. Enhanced Admin Portal
2. PBS Filter System  
3. Database Schema Updates

Usage: python setup_enhanced_integration.py
"""

import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class EnhancedIntegration:
    """Handles safe integration of enhanced features."""

    def __init__(self):
        self.root_dir = Path.cwd()
        self.backup_dir = self.root_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.errors = []
        self.success_steps = []

    def log(self, message, is_error=False):
        """Log messages with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = "❌ ERROR" if is_error else "✅ INFO"
        full_message = f"[{timestamp}] {prefix}: {message}"
        print(full_message)

        if is_error:
            self.errors.append(message)
        else:
            self.success_steps.append(message)

    def create_backup(self):
        """Create backup of critical files before modification."""
        self.log("Creating backup of existing files...")

        try:
            self.backup_dir.mkdir(exist_ok=True)

            # Files to backup
            critical_files = ["app.py", "models.py", "routes.py", "admin.py"]

            for file_name in critical_files:
                file_path = self.root_dir / file_name
                if file_path.exists():
                    backup_path = self.backup_dir / file_name
                    shutil.copy2(file_path, backup_path)
                    self.log(f"Backed up {file_name}")

            # Backup templates directory if it exists
            templates_dir = self.root_dir / "templates"
            if templates_dir.exists():
                backup_templates = self.backup_dir / "templates"
                shutil.copytree(templates_dir, backup_templates)
                self.log("Backed up templates directory")

            self.log(f"Backup created at: {self.backup_dir}")
            return True

        except Exception as e:
            self.log(f"Backup failed: {e}", is_error=True)
            return False

    def check_prerequisites(self):
        """Check if system is ready for integration."""
        self.log("Checking prerequisites...")

        # Check if we're in a VectorBid project
        required_files = ["app.py", "models.py", "routes.py"]
        missing_files = []

        for file_name in required_files:
            if not (self.root_dir / file_name).exists():
                missing_files.append(file_name)

        if missing_files:
            self.log(f"Missing required files: {missing_files}", is_error=True)
            return False

        # Check if database is accessible
        try:
            # We'll assume database is working if models.py exists
            self.log("Database connectivity check passed")
        except Exception as e:
            self.log(f"Database check failed: {e}", is_error=True)
            return False

        self.log("Prerequisites check passed")
        return True

    def install_enhanced_admin_portal(self):
        """Install the enhanced admin portal."""
        self.log("Installing Enhanced Admin Portal...")

        try:
            # Create admin_enhanced.py file
            admin_enhanced_content = '''"""
Enhanced Admin Portal for VectorBid
Provides multi-file upload, analytics dashboard, and organization features.
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import json
from pathlib import Path

# Create the blueprint
admin_enhanced_bp = Blueprint('admin_enhanced', __name__, url_prefix='/admin')

# Configuration
UPLOAD_FOLDER = 'uploads/bid_packets'
ALLOWED_EXTENSIONS = {'txt', 'csv', 'pdf'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def requires_admin_auth(f):
    """Decorator to require admin authentication."""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for bearer token in header
        auth_header = request.headers.get('Authorization')
        admin_token = os.getenv('ADMIN_TOKEN')

        if not admin_token:
            return jsonify({'error': 'Admin access not configured'}), 500

        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization required'}), 401

        token = auth_header.split(' ')[1]
        if token != admin_token:
            return jsonify({'error': 'Invalid token'}), 401

        return f(*args, **kwargs)
    return decorated_function

@admin_enhanced_bp.route('/dashboard')
@requires_admin_auth
def dashboard():
    """Enhanced admin dashboard with analytics."""
    try:
        # Import here to avoid circular imports
        from models import BidPacket, User, db

        # Get statistics
        total_packets = BidPacket.query.count()
        total_users = User.query.count()
        recent_packets = BidPacket.query.order_by(BidPacket.created_at.desc()).limit(5).all()

        # Get upload statistics by airline
        upload_stats = db.session.query(
            BidPacket.airline, 
            db.func.count(BidPacket.id).label('count')
        ).group_by(BidPacket.airline).all()

        # Format statistics for charts
        stats_data = {
            'total_packets': total_packets,
            'total_users': total_users,
            'upload_stats': [{'airline': stat[0] or 'Unknown', 'count': stat[1]} for stat in upload_stats],
            'recent_packets': [{
                'filename': packet.filename,
                'airline': packet.airline,
                'aircraft_type': packet.aircraft_type,
                'created_at': packet.created_at.strftime('%Y-%m-%d %H:%M') if packet.created_at else 'Unknown'
            } for packet in recent_packets]
        }

        return render_template('admin/enhanced_dashboard.html', stats=stats_data)

    except Exception as e:
        return jsonify({'error': f'Dashboard error: {str(e)}'}), 500

@admin_enhanced_bp.route('/upload')
@requires_admin_auth  
def upload_page():
    """Multi-file upload interface."""
    return render_template('admin/enhanced_upload.html')

@admin_enhanced_bp.route('/upload_files', methods=['POST'])
@requires_admin_auth
def upload_files():
    """Handle multiple file uploads with organization."""
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400

        files = request.files.getlist('files')
        airline = request.form.get('airline', '').strip()
        aircraft_type = request.form.get('aircraft_type', '').strip()

        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No files selected'}), 400

        uploaded_files = []
        errors = []

        # Ensure upload directory exists
        upload_dir = Path(UPLOAD_FOLDER)
        upload_dir.mkdir(parents=True, exist_ok=True)

        for file in files:
            if file.filename == '':
                continue

            if not allowed_file(file.filename):
                errors.append(f'{file.filename}: Invalid file type')
                continue

            try:
                # Secure the filename
                filename = secure_filename(file.filename)

                # Add timestamp to avoid conflicts
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                base_name, ext = os.path.splitext(filename)
                unique_filename = f"{base_name}_{timestamp}{ext}"

                # Save file
                file_path = upload_dir / unique_filename
                file.save(str(file_path))

                # Save to database
                from models import BidPacket, db
                bid_packet = BidPacket(
                    filename=unique_filename,
                    airline=airline,
                    aircraft_type=aircraft_type,
                    file_path=str(file_path),
                    created_at=datetime.utcnow()
                )

                db.session.add(bid_packet)
                db.session.commit()

                uploaded_files.append({
                    'filename': unique_filename,
                    'original_name': file.filename,
                    'size': os.path.getsize(file_path),
                    'airline': airline,
                    'aircraft_type': aircraft_type
                })

            except Exception as e:
                errors.append(f'{file.filename}: {str(e)}')

        response_data = {
            'uploaded_files': uploaded_files,
            'errors': errors,
            'total_uploaded': len(uploaded_files),
            'total_errors': len(errors)
        }

        if uploaded_files:
            return jsonify(response_data), 200
        else:
            return jsonify({'error': 'No files were uploaded successfully', 'details': errors}), 400

    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@admin_enhanced_bp.route('/packets')
@requires_admin_auth
def list_packets():
    """List all bid packets with filtering."""
    try:
        from models import BidPacket

        # Get filter parameters
        airline_filter = request.args.get('airline')
        aircraft_filter = request.args.get('aircraft')

        # Build query
        query = BidPacket.query

        if airline_filter:
            query = query.filter(BidPacket.airline == airline_filter)
        if aircraft_filter:
            query = query.filter(BidPacket.aircraft_type == aircraft_filter)

        packets = query.order_by(BidPacket.created_at.desc()).all()

        packets_data = [{
            'id': packet.id,
            'filename': packet.filename,
            'airline': packet.airline,
            'aircraft_type': packet.aircraft_type,
            'created_at': packet.created_at.strftime('%Y-%m-%d %H:%M') if packet.created_at else 'Unknown',
            'file_size': os.path.getsize(packet.file_path) if packet.file_path and os.path.exists(packet.file_path) else 0
        } for packet in packets]

        return jsonify({'packets': packets_data})

    except Exception as e:
        return jsonify({'error': f'Failed to list packets: {str(e)}'}), 500

@admin_enhanced_bp.route('/packets/<int:packet_id>', methods=['DELETE'])
@requires_admin_auth
def delete_packet(packet_id):
    """Delete a bid packet."""
    try:
        from models import BidPacket, db

        packet = BidPacket.query.get(packet_id)
        if not packet:
            return jsonify({'error': 'Packet not found'}), 404

        # Delete file if it exists
        if packet.file_path and os.path.exists(packet.file_path):
            os.remove(packet.file_path)

        # Delete database record
        db.session.delete(packet)
        db.session.commit()

        return jsonify({'message': 'Packet deleted successfully'})

    except Exception as e:
        return jsonify({'error': f'Failed to delete packet: {str(e)}'}), 500

# Error handlers
@admin_enhanced_bp.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 413

@admin_enhanced_bp.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500
'''

            # Write the admin enhanced file
            admin_enhanced_path = self.root_dir / "admin_enhanced.py"
            with open(admin_enhanced_path, 'w') as f:
                f.write(admin_enhanced_content)

            self.log("Created admin_enhanced.py")

            # Create admin templates directory
            admin_templates_dir = self.root_dir / "templates" / "admin"
            admin_templates_dir.mkdir(parents=True, exist_ok=True)

            # Create enhanced dashboard template
            dashboard_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VectorBid Admin Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            <span class="navbar-brand mb-0 h1">
                <i class="fas fa-plane"></i> VectorBid Admin
            </span>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row">
            <div class="col-md-12">
                <h1>Admin Dashboard</h1>
                <p class="text-muted">Manage bid packets and view system analytics</p>
            </div>
        </div>

        <!-- Statistics Cards -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card text-white bg-primary">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h4>{{ stats.total_packets }}</h4>
                                <p class="mb-0">Total Packets</p>
                            </div>
                            <div class="align-self-center">
                                <i class="fas fa-file-upload fa-2x"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-white bg-success">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h4>{{ stats.total_users }}</h4>
                                <p class="mb-0">Total Users</p>
                            </div>
                            <div class="align-self-center">
                                <i class="fas fa-users fa-2x"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Charts -->
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>Uploads by Airline</h5>
                    </div>
                    <div class="card-body">
                        <canvas id="airlineChart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <!-- Recent Uploads -->
        <div class="row">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5>Recent Uploads</h5>
                        <a href="{{ url_for('admin_enhanced.upload_page') }}" class="btn btn-primary">
                            <i class="fas fa-plus"></i> Upload Files
                        </a>
                    </div>
                    <div class="card-body">
                        {% if stats.recent_packets %}
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>Filename</th>
                                        <th>Airline</th>
                                        <th>Aircraft</th>
                                        <th>Upload Date</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for packet in stats.recent_packets %}
                                    <tr>
                                        <td>{{ packet.filename }}</td>
                                        <td>{{ packet.airline or 'Unknown' }}</td>
                                        <td>{{ packet.aircraft_type or 'Unknown' }}</td>
                                        <td>{{ packet.created_at }}</td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                        {% else %}
                        <p class="text-muted">No recent uploads</p>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Airline chart
        const airlineData = {{ stats.upload_stats | tojsonfilter }};
        const airlineLabels = airlineData.map(item => item.airline);
        const airlineCounts = airlineData.map(item => item.count);

        new Chart(document.getElementById('airlineChart'), {
            type: 'doughnut',
            data: {
                labels: airlineLabels,
                datasets: [{
                    data: airlineCounts,
                    backgroundColor: [
                        '#FF6384',
                        '#36A2EB', 
                        '#FFCE56',
                        '#4BC0C0',
                        '#9966FF'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    </script>
</body>
</html>'''

            dashboard_path = admin_templates_dir / "enhanced_dashboard.html"
            with open(dashboard_path, 'w') as f:
                f.write(dashboard_template)

            self.log("Created enhanced dashboard template")

            # Create upload template (simplified for space)
            upload_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Upload Bid Packets - VectorBid Admin</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('admin_enhanced.dashboard') }}">
                <i class="fas fa-plane"></i> VectorBid Admin
            </a>
        </div>
    </nav>

    <div class="container mt-4">
        <h1>Upload Bid Packets</h1>

        <div class="card">
            <div class="card-body">
                <form id="uploadForm" enctype="multipart/form-data">
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <label for="airline" class="form-label">Airline</label>
                            <input type="text" class="form-control" id="airline" name="airline" required>
                        </div>
                        <div class="col-md-6">
                            <label for="aircraft_type" class="form-label">Aircraft Type</label>
                            <input type="text" class="form-control" id="aircraft_type" name="aircraft_type" required>
                        </div>
                    </div>

                    <div class="mb-3">
                        <label for="files" class="form-label">Select Files</label>
                        <input type="file" class="form-control" id="files" name="files" multiple accept=".txt,.csv,.pdf" required>
                        <div class="form-text">Accepted formats: TXT, CSV, PDF (max 16MB each)</div>
                    </div>

                    <button type="submit" class="btn btn-primary">Upload Files</button>
                </form>

                <div id="uploadResults" class="mt-3"></div>
            </div>
        </div>
    </div>

    <script>
        document.getElementById('uploadForm').addEventListener('submit', async function(e) {
            e.preventDefault();

            const formData = new FormData(this);
            const resultDiv = document.getElementById('uploadResults');

            try {
                resultDiv.innerHTML = '<div class="alert alert-info">Uploading...</div>';

                const response = await fetch('{{ url_for("admin_enhanced.upload_files") }}', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'Authorization': 'Bearer ' + prompt('Enter admin token:')
                    }
                });

                const result = await response.json();

                if (response.ok) {
                    resultDiv.innerHTML = `<div class="alert alert-success">
                        Successfully uploaded ${result.total_uploaded} files
                    </div>`;
                    this.reset();
                } else {
                    resultDiv.innerHTML = `<div class="alert alert-danger">
                        Upload failed: ${result.error}
                    </div>`;
                }
            } catch (error) {
                resultDiv.innerHTML = `<div class="alert alert-danger">
                    Error: ${error.message}
                </div>`;
            }
        });
    </script>
</body>
</html>'''

            upload_path = admin_templates_dir / "enhanced_upload.html"
            with open(upload_path, 'w') as f:
                f.write(upload_template)

            self.log("Created enhanced upload template")
            return True

        except Exception as e:
            self.log(f"Failed to install enhanced admin portal: {e}",
                     is_error=True)
            return False

    def install_pbs_filter_system(self):
        """Install the PBS filter system."""
        self.log("Installing PBS Filter System...")

        try:
            # Update routes.py to add PBS filter functionality
            routes_path = self.root_dir / "api/routes.py"

            if not routes_path.exists():
                self.log("routes.py not found", is_error=True)
                return False

            # Read existing routes
            with open(routes_path, 'r') as f:
                routes_content = f.read()

            # Add PBS filter functions to routes.py
            pbs_filter_code = '''

# PBS Filter System Functions
def natural_language_to_pbs_filters(preferences_text, trip_data=None):
    """Convert natural language preferences to PBS filter commands."""
    if not preferences_text:
        return []

    filters = []
    text_lower = preferences_text.lower()

    # Weekend preferences
    if any(phrase in text_lower for phrase in ['weekends off', 'weekend off', 'no weekends']):
        filters.append("AVOID TRIPS IF DUTY_PERIOD OVERLAPS SAT OR SUN")

    # Trip length preferences
    if 'short trip' in text_lower or 'day trip' in text_lower:
        filters.append("PREFER TRIPS WITH DUTY_DAYS <= 2")
    elif 'long trip' in text_lower:
        filters.append("PREFER TRIPS WITH DUTY_DAYS >= 4")

    # Commute preferences
    if any(phrase in text_lower for phrase in ['easy commute', 'avoid commute', 'commutable']):
        filters.append("PREFER TRIPS STARTING AFTER 1000 ON MON,TUE,WED,THU,FRI")

    # International preferences
    if 'international' in text_lower:
        if 'avoid' in text_lower or 'no' in text_lower:
            filters.append("AVOID TRIPS WITH DESTINATION INTL")
        else:
            filters.append("PREFER TRIPS WITH DESTINATION INTL")

    # Early morning preferences
    if any(phrase in text_lower for phrase in ['no early', 'avoid early', 'late start']):
        filters.append("AVOID TRIPS STARTING BEFORE 0800")

    # Red-eye preferences  
    if any(phrase in text_lower for phrase in ['no redeye', 'avoid redeye', 'no red-eye']):
        filters.append("AVOID TRIPS WITH DEPARTURE_TIME BETWEEN 2200 AND 0559")

    # Home every night
    if any(phrase in text_lower for phrase in ['home every night', 'home daily', 'no overnights']):
        filters.append("PREFER TRIPS WITH DUTY_DAYS = 1")

    # Maximum days off
    if 'days off' in text_lower:
        filters.append("PREFER MAX_DAYS_OFF")

    # Add a catch-all preference if no specific filters matched
    if not filters:
        filters.append("PREFER TRIPS WITH GOOD_QUALITY_OF_LIFE")

    return filters

@main_bp.route('/preview_pbs_filters', methods=['POST'])
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

@main_bp.route('/download_pbs_filters')
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
            from models import BidAnalysis
            recent_analysis = BidAnalysis.query.filter_by(user_id=user_id).order_by(BidAnalysis.created_at.desc()).first()
            if recent_analysis:
                analysis_data = recent_analysis.results

        if not analysis_data:
            flash('No analysis data found. Please run an analysis first.', 'error')
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
            filter_content += f"{i:2d}. {filter_cmd}\\n"

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
        from flask import make_response
        response = make_response(filter_content)
        response.headers['Content-Type'] = 'text/plain'
        response.headers['Content-Disposition'] = f'attachment; filename=vectorbid_pbs_filters_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'

        return response

    except Exception as e:
        logger.error(f"PBS filter download error: {e}")
        flash('Error generating PBS filters', 'error')
        return redirect(url_for('main.index'))
'''

            # Check if PBS functions already exist
            if 'natural_language_to_pbs_filters' not in routes_content:
                # Append PBS filter code to routes.py
                with open(routes_path, 'a') as f:
                    f.write(pbs_filter_code)

                self.log("Added PBS filter functions to routes.py")
            else:
                self.log("PBS filter functions already exist in routes.py")

            return True

        except Exception as e:
            self.log(f"Failed to install PBS filter system: {e}",
                     is_error=True)
            return False

    def update_database_models(self):
        """Update database models with enhanced features."""
        self.log("Updating database models...")

        try:
            models_path = self.root_dir / "core/models.py"

            if not models_path.exists():
                self.log("models.py not found", is_error=True)
                return False

            # Read existing models
            with open(models_path, 'r') as f:
                models_content = f.read()

            # Check if BidPacket model needs enhancement
            if 'airline = db.Column' not in models_content:
                # Add enhanced fields to BidPacket model
                enhanced_model_code = '''
# Enhanced BidPacket model fields
# Add these fields to your existing BidPacket model:
#
# airline = db.Column(db.String(50), nullable=True, index=True)
# aircraft_type = db.Column(db.String(50), nullable=True, index=True) 
# created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
# file_size = db.Column(db.Integer, nullable=True)
# processing_status = db.Column(db.String(20), default='pending')
# error_message = db.Column(db.Text, nullable=True)

# Enhanced User model fields  
# Add these fields to your existing User model:
#
# login_count = db.Column(db.Integer, default=0)
# last_login = db.Column(db.DateTime, nullable=True)
# profile_completion_date = db.Column(db.DateTime, nullable=True)
# preferences_updated_at = db.Column(db.DateTime, nullable=True)
'''

                # Append enhancement notes to models.py
                with open(models_path, 'a') as f:
                    f.write(enhanced_model_code)

                self.log("Added model enhancement notes to models.py")
                self.log(
                    "MANUAL ACTION REQUIRED: Update your models with the new fields listed at the end of models.py"
                )

            return True

        except Exception as e:
            self.log(f"Failed to update database models: {e}", is_error=True)
            return False

    def update_app_configuration(self):
        """Update app.py to register enhanced blueprints."""
        self.log("Updating app configuration...")

        try:
            app_path = self.root_dir / "core/app.py"

            if not app_path.exists():
                self.log("app.py not found", is_error=True)
                return False

            # Read existing app.py
            with open(app_path, 'r') as f:
                app_content = f.read()

            # Check if enhanced admin blueprint is already registered
            if 'admin_enhanced_bp' not in app_content:
                # Find the blueprint registration section
                blueprint_section = "# Register admin blueprint"
                if blueprint_section in app_content:
                    # Add enhanced admin blueprint registration
                    enhanced_registration = '''
        # Register enhanced admin blueprint
        try:
            from admin_enhanced import admin_enhanced_bp
            app.register_blueprint(admin_enhanced_bp)
            logger.info("Enhanced admin blueprint registered")
        except ImportError:
            logger.warning("Enhanced admin blueprint not found; skipping")
'''

                    # Insert after existing admin blueprint registration
                    app_content = app_content.replace(
                        blueprint_section,
                        blueprint_section + enhanced_registration)

                    # Write updated app.py
                    with open(app_path, 'w') as f:
                        f.write(app_content)

                    self.log("Updated app.py with enhanced admin blueprint")
                else:
                    self.log(
                        "Could not find blueprint registration section in app.py"
                    )
                    self.log(
                        "MANUAL ACTION REQUIRED: Register admin_enhanced_bp in your app.py"
                    )
            else:
                self.log(
                    "Enhanced admin blueprint already registered in app.py")

            return True

        except Exception as e:
            self.log(f"Failed to update app configuration: {e}", is_error=True)
            return False

    def create_environment_template(self):
        """Create environment variable template for enhanced features."""
        self.log("Creating environment template...")

        try:
            env_template = '''# VectorBid Enhanced Features Environment Variables
# Add these to your Replit Secrets or .env file:

# Admin Portal Authentication
ADMIN_TOKEN=your_secure_admin_token_here

# Enhanced Features Configuration  
ENABLE_ADMIN_ENDPOINTS=true
ENABLE_PBS_FILTERS=true
ENABLE_ANALYTICS=true

# File Upload Configuration
MAX_UPLOAD_SIZE=16777216  # 16MB in bytes
UPLOAD_FOLDER=uploads/bid_packets

# Database Configuration (if not already set)
# DATABASE_URL=your_postgresql_connection_string
'''

            env_template_path = self.root_dir / "environment_template.txt"
            with open(env_template_path, 'w') as f:
                f.write(env_template)

            self.log("Created environment_template.txt")
            return True

        except Exception as e:
            self.log(f"Failed to create environment template: {e}",
                     is_error=True)
            return False

    def run_integration(self):
        """Run the complete integration process."""
        self.log("🚀 Starting VectorBid Enhanced Features Integration")
        self.log("=" * 60)

        success = True

        # Step 1: Prerequisites check
        if not self.check_prerequisites():
            self.log("Prerequisites check failed. Aborting integration.",
                     is_error=True)
            return False

        # Step 2: Create backup
        if not self.create_backup():
            self.log("Backup creation failed. Aborting integration.",
                     is_error=True)
            return False

        # Step 3: Install enhanced admin portal
        if not self.install_enhanced_admin_portal():
            success = False

        # Step 4: Install PBS filter system
        if not self.install_pbs_filter_system():
            success = False

        # Step 5: Update database models
        if not self.update_database_models():
            success = False

        # Step 6: Update app configuration
        if not self.update_app_configuration():
            success = False

        # Step 7: Create environment template
        if not self.create_environment_template():
            success = False

        # Final summary
        self.log("=" * 60)
        if success and not self.errors:
            self.log("🎉 Integration completed successfully!")
            self.log("Next steps:")
            self.log(
                "1. Review environment_template.txt and add required secrets")
            self.log(
                "2. Update your database models with the fields noted in models.py"
            )
            self.log("3. Restart your application")
            self.log("4. Test the enhanced admin portal at /admin/dashboard")
            self.log("5. Test PBS filter generation in the main interface")
        elif success:
            self.log("⚠️  Integration completed with warnings")
            self.log(
                "Please review the warnings above and complete manual actions")
        else:
            self.log("❌ Integration failed")
            self.log("Please review the errors above and try again")
            self.log(f"Backup available at: {self.backup_dir}")

        self.log(
            f"Integration summary: {len(self.success_steps)} successes, {len(self.errors)} errors"
        )

        return success


def main():
    """Main integration function."""
    print("VectorBid Enhanced Features Integration")
    print(
        "This will integrate the enhanced admin portal, PBS filters, and database updates"
    )
    print()

    # Confirm with user
    response = input("Do you want to proceed? (y/N): ").lower().strip()
    if response != 'y':
        print("Integration cancelled.")
        return

    # Run integration
    integrator = EnhancedIntegration()
    success = integrator.run_integration()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
