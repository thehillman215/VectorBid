"""
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
