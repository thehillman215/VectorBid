"""
Enhanced Admin Portal for VectorBid - FIXED VERSION
Provides multi-file upload, analytics dashboard, and organization features.
FIXES: Flask environment variable loading and authentication flow
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import json
from pathlib import Path
from functools import wraps

# Create the blueprint
admin_enhanced_bp = Blueprint('admin_enhanced', __name__, url_prefix='/admin')

# Configuration constants
UPLOAD_FOLDER = 'uploads/bid_packets'
ALLOWED_EXTENSIONS = {'txt', 'csv', 'pdf'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit(
        '.', 1)[1].lower() in ALLOWED_EXTENSIONS


def requires_admin_auth(f):
    """
    Decorator to require admin authentication.
    FIXED: Now properly accesses Flask environment variables
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Method 1: Try to get from Flask app config first (most reliable)
        admin_token = current_app.config.get('ADMIN_BEARER_TOKEN')

        # Method 2: Fallback to direct environment variable access
        if not admin_token:
            admin_token = os.environ.get('ADMIN_BEARER_TOKEN')

        # Method 3: Fallback to alternative environment variable name
        if not admin_token:
            admin_token = os.environ.get('ADMIN_TOKEN')

        if not admin_token:
            return jsonify({
                'error':
                'Admin access not configured',
                'debug':
                'ADMIN_BEARER_TOKEN not found in config or environment'
            }), 500

        # Check for bearer token in header
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            # For browser access, render simple login page
            if request.accept_mimetypes.accept_html:
                return render_admin_login('Authorization header required')
            return jsonify({'error': 'Authorization header required'}), 401

        if not auth_header.startswith('Bearer '):
            if request.accept_mimetypes.accept_html:
                return render_admin_login('Bearer token required')
            return jsonify(
                {'error':
                 'Bearer token required (use: Bearer YOUR_TOKEN)'}), 401

        token = auth_header.split(' ')[1]
        if token != admin_token:
            if request.accept_mimetypes.accept_html:
                return render_admin_login('Invalid token')
            return jsonify({'error': 'Invalid token'}), 401

        return f(*args, **kwargs)

    return decorated_function


def render_admin_login(error_msg=None):
    """Render a simple admin login page."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>VectorBid Admin Login</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h4>VectorBid Admin Access</h4>
                        </div>
                        <div class="card-body">
                            {('<div class="alert alert-danger">' + error_msg + '</div>') if error_msg else ''}

                            <p><strong>How to access admin features:</strong></p>
                            <ol>
                                <li>Add this header to your requests: <code>Authorization: Bearer YOUR_ADMIN_TOKEN</code></li>
                                <li>Use tools like curl/Postman with the Bearer token</li>
                                <li>The admin token is configured via ADMIN_BEARER_TOKEN environment variable</li>
                            </ol>

                            <div class="mb-3">
                                <label for="token" class="form-label">Admin Token:</label>
                                <input type="text" class="form-control" id="token" placeholder="Enter your admin token">
                            </div>

                            <button onclick="testAccess()" class="btn btn-primary">Test Access</button>
                            <a href="/admin/debug" class="btn btn-outline-info">Debug Info</a>

                            <div id="result" class="mt-3"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            function testAccess() {{
                const token = document.getElementById('token').value;
                if (!token) {{
                    alert('Please enter an admin token');
                    return;
                }}

                fetch('/admin/debug', {{
                    headers: {{
                        'Authorization': 'Bearer ' + token
                    }}
                }})
                .then(response => response.json())
                .then(data => {{
                    document.getElementById('result').innerHTML = 
                        '<pre class="bg-light p-3 rounded">' + JSON.stringify(data, null, 2) + '</pre>';

                    if (data.is_authenticated) {{
                        window.location.href = '/admin/dashboard';
                    }}
                }})
                .catch(error => {{
                    document.getElementById('result').innerHTML = 
                        '<div class="alert alert-danger">Error: ' + error + '</div>';
                }});
            }}
        </script>
    </body>
    </html>
    """


@admin_enhanced_bp.route('/dashboard')
@requires_admin_auth
def dashboard():
    """Enhanced admin dashboard with analytics."""
    try:
        # Import models here to avoid circular imports
        from src.core.models import User, BidAnalysis, BidPacket
        from src.core.app import db

        # Get statistics
        total_users = User.query.count()
        total_analyses = BidAnalysis.query.count()
        total_packets = BidPacket.query.count()

        # Recent activity (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_users = User.query.filter(
            User.created_at >= thirty_days_ago).count()
        recent_analyses = BidAnalysis.query.filter(
            BidAnalysis.created_at >= thirty_days_ago).count()

        # Get recent bid packets
        recent_packets = BidPacket.query.order_by(
            BidPacket.uploaded_at.desc()).limit(10).all()

        stats = {
            'total_users': total_users,
            'total_analyses': total_analyses,
            'total_packets': total_packets,
            'recent_users': recent_users,
            'recent_analyses': recent_analyses,
            'recent_packets': recent_packets
        }

        return render_template('admin/enhanced_dashboard.html', stats=stats)

    except Exception as e:
        current_app.logger.error(f"Admin dashboard error: {e}")
        return jsonify({'error': f'Dashboard error: {str(e)}'}), 500


@admin_enhanced_bp.route('/upload')
@requires_admin_auth
def upload_page():
    """Enhanced upload page with multi-file support."""
    try:
        # Get existing bid packets for display
        from src.core.models import BidPacket

        packets = BidPacket.query.order_by(
            BidPacket.uploaded_at.desc()).limit(20).all()

        return render_template('admin/enhanced_upload.html', packets=packets)

    except Exception as e:
        current_app.logger.error(f"Admin upload page error: {e}")
        return jsonify({'error': f'Upload page error: {str(e)}'}), 500


@admin_enhanced_bp.route('/api/upload', methods=['POST'])
@requires_admin_auth
def api_upload():
    """Enhanced API endpoint for file uploads."""
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400

        files = request.files.getlist('files')
        month_tag = request.form.get('month_tag', '')
        airline = request.form.get('airline', '')
        aircraft = request.form.get('aircraft', '')

        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No files selected'}), 400

        results = []

        for file in files:
            if file and file.filename:
                if allowed_file(file.filename):
                    filename = secure_filename(file.filename)

                    # Create upload directory if it doesn't exist
                    upload_dir = Path(UPLOAD_FOLDER)
                    upload_dir.mkdir(parents=True, exist_ok=True)

                    # Save file
                    file_path = upload_dir / filename
                    file.save(file_path)

                    # Save to database
                    from src.core.models import BidPacket
                    from src.core.app import db

                    bid_packet = BidPacket(filename=filename,
                                           month_tag=month_tag,
                                           file_path=str(file_path),
                                           airline=airline,
                                           aircraft=aircraft,
                                           uploaded_at=datetime.now())

                    db.session.add(bid_packet)
                    db.session.commit()

                    results.append({
                        'filename': filename,
                        'status': 'success',
                        'id': bid_packet.id
                    })
                else:
                    results.append({
                        'filename': file.filename,
                        'status': 'error',
                        'message': 'File type not allowed'
                    })

        return jsonify({
            'message': f'Processed {len(results)} files',
            'results': results
        })

    except Exception as e:
        current_app.logger.error(f"Admin upload error: {e}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@admin_enhanced_bp.route('/debug')
def debug_auth():
    """Debug endpoint to check authentication configuration."""
    # Get token from multiple sources
    config_token = current_app.config.get('ADMIN_BEARER_TOKEN')
    env_token = os.environ.get('ADMIN_BEARER_TOKEN')
    alt_token = os.environ.get('ADMIN_TOKEN')

    auth_header = request.headers.get('Authorization')
    provided_token = None
    if auth_header and auth_header.startswith('Bearer '):
        provided_token = auth_header.split(' ')[1]

    is_authenticated = False
    if config_token or env_token or alt_token:
        expected_token = config_token or env_token or alt_token
        is_authenticated = provided_token == expected_token

    debug_info = {
        'is_authenticated':
        is_authenticated,
        'config_has_token':
        bool(config_token),
        'env_has_token':
        bool(env_token),
        'alt_env_has_token':
        bool(alt_token),
        'token_provided':
        bool(provided_token),
        'auth_header_format':
        'correct'
        if auth_header and auth_header.startswith('Bearer ') else 'incorrect',
        'expected_token_preview':
        (config_token or env_token or alt_token or 'None')[:8] + '...' if
        (config_token or env_token or alt_token) else 'None',
        'provided_token_preview':
        provided_token[:8] + '...' if provided_token else 'None',
        'environment_variables': {
            'ADMIN_BEARER_TOKEN': 'set' if env_token else 'not set',
            'ADMIN_TOKEN': 'set' if alt_token else 'not set'
        }
    }

    return jsonify(debug_info)


@admin_enhanced_bp.route('/login')
def login():
    """Admin login page."""
    return render_admin_login()


@admin_enhanced_bp.route('/api/packets', methods=['GET'])
@requires_admin_auth
def list_packets():
    """List all bid packets with filtering."""
    try:
        from src.core.models import BidPacket

        # Get query parameters
        airline = request.args.get('airline')
        aircraft = request.args.get('aircraft')
        month = request.args.get('month')

        # Build query
        query = BidPacket.query

        if airline:
            query = query.filter(BidPacket.airline.ilike(f'%{airline}%'))
        if aircraft:
            query = query.filter(BidPacket.aircraft.ilike(f'%{aircraft}%'))
        if month:
            query = query.filter(BidPacket.month_tag.ilike(f'%{month}%'))

        packets = query.order_by(BidPacket.uploaded_at.desc()).all()

        packet_list = []
        for packet in packets:
            packet_list.append({
                'id':
                packet.id,
                'filename':
                packet.filename,
                'month_tag':
                packet.month_tag,
                'airline':
                packet.airline,
                'aircraft':
                packet.aircraft,
                'uploaded_at':
                packet.uploaded_at.isoformat(),
                'file_size':
                getattr(packet, 'file_size', 'Unknown')
            })

        return jsonify({'packets': packet_list, 'total': len(packet_list)})

    except Exception as e:
        current_app.logger.error(f"Admin list packets error: {e}")
        return jsonify({'error': f'Failed to list packets: {str(e)}'}), 500


@admin_enhanced_bp.route('/api/packets/<int:packet_id>', methods=['DELETE'])
@requires_admin_auth
def delete_packet(packet_id):
    """Delete a bid packet."""
    try:
        from src.core.models import BidPacket
        from src.core.app import db

        packet = BidPacket.query.get_or_404(packet_id)

        # Delete file from filesystem
        if packet.file_path and Path(packet.file_path).exists():
            Path(packet.file_path).unlink()

        # Delete from database
        db.session.delete(packet)
        db.session.commit()

        return jsonify({'message': 'Packet deleted successfully'})

    except Exception as e:
        current_app.logger.error(f"Admin delete packet error: {e}")
        return jsonify({'error': f'Failed to delete packet: {str(e)}'}), 500
