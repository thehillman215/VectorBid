"""
Enhanced Admin Portal for VectorBid - SESSION-BASED AUTH (FIXED)
Provides multi-file upload, analytics dashboard, and organization features.
Fixed: Uses Flask sessions instead of Bearer tokens for easier browser use.
"""

from flask import Blueprint, render_template, request, jsonify, current_app, session, redirect, url_for
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
    return '.' in filename and filename.rsplit(
        '.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_admin_token():
    """Get admin token from multiple sources with fallbacks."""
    # Try Flask config first (recommended for Flask apps)
    token = current_app.config.get('ADMIN_TOKEN')
    if token:
        return token

    # Try environment variables (Replit secrets)
    token = os.environ.get('ADMIN_TOKEN')
    if token:
        return token

    # Try os.getenv as fallback
    token = os.getenv('ADMIN_TOKEN')
    if token:
        return token

    return None


def is_admin_authenticated():
    """Check if current session is authenticated as admin."""
    return session.get('admin_authenticated') == True


def requires_admin_auth(f):
    """Decorator to require admin authentication - SESSION-BASED."""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Check if already authenticated via session
            if is_admin_authenticated():
                return f(*args, **kwargs)

            # Check for bearer token in header (for API calls)
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                admin_token = get_admin_token()
                if not admin_token:
                    return jsonify({
                        'error':
                        'Admin access not configured',
                        'details':
                        'ADMIN_TOKEN not found in Flask config or environment variables'
                    }), 500

                token = auth_header.split(' ')[1]
                if token == admin_token:
                    # Valid token - set session and continue
                    session['admin_authenticated'] = True
                    return f(*args, **kwargs)

            # Not authenticated - redirect to login
            if request.endpoint and 'login' not in request.endpoint:
                return redirect(url_for('admin_enhanced.login'))

            return jsonify({'error': 'Authentication required'}), 401

        except Exception as e:
            current_app.logger.error(f"Admin auth error: {str(e)}")
            return jsonify({
                'error': 'Authentication system error',
                'details': str(e)
            }), 500

    return decorated_function


@admin_enhanced_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page with session-based auth."""
    if request.method == 'GET':
        # If already logged in, redirect to dashboard
        if is_admin_authenticated():
            return redirect(url_for('admin_enhanced.dashboard'))
        return render_template('admin/login.html')

    # Handle POST login
    try:
        token = request.form.get('token') or request.json.get(
            'token') if request.is_json else None
        admin_token = get_admin_token()

        if not admin_token:
            return jsonify({'error': 'Admin access not configured'}), 500

        if token == admin_token:
            # Set session
            session['admin_authenticated'] = True
            session.permanent = True  # Make session persistent

            if request.is_json:
                return jsonify({
                    'success': True,
                    'redirect': url_for('admin_enhanced.dashboard')
                })
            else:
                return redirect(url_for('admin_enhanced.dashboard'))
        else:
            if request.is_json:
                return jsonify({'error': 'Invalid token'}), 401
            else:
                return render_template('admin/login.html',
                                       error='Invalid token')

    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return jsonify({'error': f'Login failed: {str(e)}'}), 500


@admin_enhanced_bp.route('/logout')
def logout():
    """Admin logout."""
    session.pop('admin_authenticated', None)
    return redirect(url_for('admin_enhanced.login'))


@admin_enhanced_bp.route('/dashboard')
@requires_admin_auth
def dashboard():
    """Enhanced admin dashboard with analytics - DATABASE COMPATIBLE."""
    try:
        # Import here to avoid circular imports
        from src.core.models import BidPacket, User, db

        # Get basic statistics using only columns that definitely exist
        total_packets = BidPacket.query.count()
        total_users = User.query.count()

        # Get recent packets (only use columns that exist in all setups)
        recent_packets = BidPacket.query.order_by(
            BidPacket.created_at.desc()).limit(5).all()

        # Simplified stats to avoid database schema issues
        stats_data = {
            'total_packets':
            total_packets,
            'total_users':
            total_users,
            'upload_stats': [{
                'airline': 'All Airlines',
                'count': total_packets
            }],  # Simplified
            'recent_packets': [
                {
                    'filename':
                    packet.filename,
                    'airline':
                    getattr(packet, 'airline', 'Unknown'),  # Safe access
                    'aircraft_type':
                    getattr(packet, 'aircraft_type', 'Unknown'),  # Safe access
                    'created_at':
                    packet.created_at.strftime('%Y-%m-%d %H:%M')
                    if hasattr(packet, 'created_at') and packet.created_at else
                    'Unknown'
                } for packet in recent_packets
            ]
        }

        return render_template('admin/enhanced_dashboard.html',
                               stats=stats_data)

    except Exception as e:
        current_app.logger.error(f"Dashboard error: {str(e)}")
        # Return a simplified dashboard on any database errors
        return render_template('admin/simple_dashboard.html', error=str(e))


@admin_enhanced_bp.route('/upload')
@requires_admin_auth
def upload_page():
    """Multi-file upload interface."""
    return render_template('admin/enhanced_upload.html')


@admin_enhanced_bp.route('/upload_files', methods=['POST'])
@requires_admin_auth
def upload_files():
    """Handle multiple file uploads with organization - DATABASE COMPATIBLE."""
    try:
        # Create upload directory if it doesn't exist
        upload_dir = Path(UPLOAD_FOLDER)
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Get form data
        airline = request.form.get('airline', 'Unknown')
        aircraft_type = request.form.get('aircraft_type', 'Unknown')
        files = request.files.getlist('files')

        if not files or files[0].filename == '':
            return jsonify({'error': 'No files selected'}), 400

        uploaded_files = []
        failed_files = []

        for file in files:
            if file and allowed_file(file.filename):
                try:
                    # Secure the filename
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    safe_filename = f"{timestamp}_{filename}"

                    # Save file
                    file_path = upload_dir / safe_filename
                    file.save(str(file_path))

                    # Create database record with safe field access
                    from src.core.models import BidPacket, db

                    # Only set fields that definitely exist
                    bid_packet_data = {
                        'filename': safe_filename,
                        'file_path': str(file_path),
                        'created_at': datetime.utcnow()
                    }

                    # Try to set optional fields if they exist in the model
                    try:
                        bid_packet_data['original_filename'] = filename
                        bid_packet_data['airline'] = airline
                        bid_packet_data['aircraft_type'] = aircraft_type
                        bid_packet_data['file_size'] = file_path.stat().st_size
                    except Exception:
                        pass  # Skip optional fields if they don't exist

                    bid_packet = BidPacket(**bid_packet_data)
                    db.session.add(bid_packet)
                    uploaded_files.append(filename)

                except Exception as e:
                    current_app.logger.error(
                        f"Failed to upload {file.filename}: {str(e)}")
                    failed_files.append({
                        'name': file.filename,
                        'error': str(e)
                    })
            else:
                failed_files.append({
                    'name': file.filename,
                    'error': 'Invalid file type'
                })

        # Commit database changes
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database commit failed: {str(e)}")
            return jsonify({'error': f'Database error: {str(e)}'}), 500

        return jsonify({
            'message': 'Upload completed',
            'total_uploaded': len(uploaded_files),
            'uploaded_files': uploaded_files,
            'failed_files': failed_files
        })

    except Exception as e:
        current_app.logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@admin_enhanced_bp.route('/files')
@requires_admin_auth
def list_files():
    """List all uploaded bid packets with filtering - DATABASE COMPATIBLE."""
    try:
        from src.core.models import BidPacket

        packets = BidPacket.query.order_by(BidPacket.created_at.desc()).all()

        files_data = []
        for packet in packets:
            file_info = {
                'id':
                packet.id,
                'filename':
                getattr(packet, 'original_filename', packet.filename),
                'airline':
                getattr(packet, 'airline', 'Unknown'),
                'aircraft_type':
                getattr(packet, 'aircraft_type', 'Unknown'),
                'file_size':
                getattr(packet, 'file_size', 0),
                'created_at':
                packet.created_at.strftime('%Y-%m-%d %H:%M')
                if hasattr(packet, 'created_at') and packet.created_at else
                'Unknown'
            }
            files_data.append(file_info)

        return jsonify({'files': files_data})

    except Exception as e:
        current_app.logger.error(f"List files error: {str(e)}")
        return jsonify({'error': f'Failed to list files: {str(e)}'}), 500


@admin_enhanced_bp.route('/delete_file/<int:file_id>', methods=['DELETE'])
@requires_admin_auth
def delete_file(file_id):
    """Delete a bid packet file - DATABASE COMPATIBLE."""
    try:
        from src.core.models import BidPacket, db

        packet = BidPacket.query.get_or_404(file_id)

        # Delete physical file if path exists
        file_path = getattr(packet, 'file_path', None)
        if file_path and Path(file_path).exists():
            Path(file_path).unlink()

        # Delete database record
        db.session.delete(packet)
        db.session.commit()

        return jsonify({'message': 'File deleted successfully'})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete file error: {str(e)}")
        return jsonify({'error': f'Failed to delete file: {str(e)}'}), 500
