"""
Unified Admin System for VectorBid
Professional implementation with Bearer token authentication

Author: VectorBid Engineering
Version: 2.0.0
"""

import logging
import os
import secrets
from datetime import datetime
from functools import wraps

from flask import (
    Blueprint,
    jsonify,
    redirect,
    render_template_string,
    request,
    session,
    url_for,
)

# Import the BidPacketManager
try:
    from src.lib.bid_packet_manager import BidPacketManager
except ImportError:
    try:
        # Fallback import path
        import sys
        sys.path.append('src/lib')
        from bid_packet_manager import BidPacketManager
    except ImportError:
        # If not found, we'll handle it gracefully
        BidPacketManager = None

# Configure logging
logger = logging.getLogger(__name__)

# ============================================
# CONFIGURATION
# ============================================


class AdminConfig:
    """Admin panel configuration"""

    # Authentication
    BEARER_TOKEN = os.environ.get('ADMIN_BEARER_TOKEN',
                                  'vb-admin-2025-secure-token')
    SESSION_LIFETIME_MINUTES = 60

    # File upload
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {'pdf', 'PDF'}

    # Rate limiting
    MAX_UPLOADS_PER_HOUR = 20


# ============================================
# BLUEPRINT SETUP
# ============================================

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ============================================
# AUTHENTICATION
# ============================================


def require_bearer_token(f):
    """Decorator for Bearer token authentication"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check Authorization header
        auth_header = request.headers.get('Authorization')

        # Also check for token in session (for web UI)
        session_token = session.get('admin_token')

        token = None

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]  # Remove 'Bearer ' prefix
        elif session_token:
            token = session_token

        if not token:
            if request.path.startswith('/admin/api/'):
                return jsonify({'error':
                                'No authorization token provided'}), 401
            return redirect(url_for('admin.login'))

        # Validate token
        if not secrets.compare_digest(token, AdminConfig.BEARER_TOKEN):
            if request.path.startswith('/admin/api/'):
                return jsonify({'error': 'Invalid token'}), 401
            session.pop('admin_token', None)
            return redirect(url_for('admin.login'))

        return f(*args, **kwargs)

    return decorated_function


# ============================================
# WEB UI ROUTES
# ============================================


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""

    if request.method == 'POST':
        token = request.form.get('token')

        if token and secrets.compare_digest(token, AdminConfig.BEARER_TOKEN):
            session['admin_token'] = token
            session['admin_login_time'] = datetime.utcnow().isoformat()
            logger.info("Admin logged in successfully")
            return redirect(url_for('admin.dashboard'))
        else:
            error = "Invalid token"
            logger.warning("Failed admin login attempt")
    else:
        error = None

    login_html = """
<!DOCTYPE html>
<html>
<head>
    <title>VectorBid Admin Login</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-card {
            background: white;
            border-radius: 15px;
            padding: 3rem;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            width: 100%;
            max-width: 400px;
        }
        .logo {
            text-align: center;
            margin-bottom: 2rem;
        }
        .logo h1 {
            color: #667eea;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="login-card">
        <div class="logo">
            <h1>✈️ VectorBid</h1>
            <p class="text-muted">Admin Access</p>
        </div>

        {% if error %}
        <div class="alert alert-danger">{{ error }}</div>
        {% endif %}

        <form method="POST">
            <div class="mb-3">
                <label for="token" class="form-label">Bearer Token</label>
                <input type="password" class="form-control" id="token" name="token" required 
                       placeholder="Enter admin bearer token">
                <small class="text-muted">Contact system administrator for token</small>
            </div>
            <button type="submit" class="btn btn-primary w-100">Login</button>
        </form>
    </div>
</body>
</html>
    """

    from flask import render_template_string
    return render_template_string(login_html, error=error)


@admin_bp.route('/logout')
def logout():
    """Admin logout"""
    session.pop('admin_token', None)
    session.pop('admin_login_time', None)
    logger.info("Admin logged out")
    return redirect(url_for('admin.login'))


@admin_bp.route('/')
@admin_bp.route('/dashboard')
@require_bearer_token
def dashboard():
    """Admin dashboard"""

    if not BidPacketManager:
        # Fallback data when BidPacketManager is not available
        packets = []
        contracts = []
    else:
        try:
            manager = BidPacketManager()
            packets = manager.get_available_bid_packets()
            contracts = []  # manager.get_contracts() - TODO: implement
        except Exception as e:
            logger.error(f"Error loading bid packets: {e}")
            packets = []
            contracts = []

    dashboard_html = r"""
<!DOCTYPE html>
<html>
<head>
    <title>VectorBid Admin Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css">
    <style>
        body { background: #f8f9fa; }
        .navbar { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .card { border-radius: 10px; border: none; box-shadow: 0 2px 10px rgba(0,0,0,0.08); }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 1rem;
        }
        .upload-zone {
            border: 2px dashed #667eea;
            border-radius: 10px;
            padding: 2rem;
            text-align: center;
            background: white;
            transition: all 0.3s;
        }
        .upload-zone:hover {
            background: #f0f0ff;
            border-color: #764ba2;
        }
        .upload-zone.dragover {
            background: #e0e0ff;
            border-color: #667eea;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-dark">
        <div class="container">
            <span class="navbar-brand">✈️ VectorBid Admin</span>
            <div>
                <span class="text-white me-3">Admin Panel</span>
                <a href="{{ url_for('admin.logout') }}" class="btn btn-outline-light btn-sm">Logout</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <!-- Statistics -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="stat-card">
                    <h5>Total Bid Packets</h5>
                    <h2>{{ packets|length }}</h2>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card">
                    <h5>Contracts</h5>
                    <h2>{{ contracts|length }}</h2>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card">
                    <h5>Active Airlines</h5>
                    <h2>{{ unique_airlines }}</h2>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card">
                    <h5>Storage Used</h5>
                    <h2>{{ storage_mb }} MB</h2>
                </div>
            </div>
        </div>

        <!-- Upload Section -->
        <div class="card mb-4">
            <div class="card-body">
                <h5 class="card-title">Upload Bid Packet</h5>

                <div class="upload-zone" id="uploadZone">
                    <i class="bi bi-cloud-upload" style="font-size: 3rem; color: #667eea;"></i>
                    <p class="mt-3">Drag and drop PDF files here or click to browse</p>
                    <input type="file" id="fileInput" accept=".pdf" style="display: none;">
                    <button class="btn btn-primary" onclick="document.getElementById('fileInput').click()">
                        Choose Files
                    </button>
                </div>

                <div id="uploadForm" style="display: none;" class="mt-3">
                    <div class="row">
                        <div class="col-md-4">
                            <label>Month (YYYYMM)</label>
                            <input type="text" id="monthTag" class="form-control" placeholder="202501" maxlength="6">
                        </div>
                        <div class="col-md-4">
                            <label>Airline</label>
                            <select id="airline" class="form-control">
                                <option value="">Select...</option>
                                <option value="United">United</option>
                                <option value="American">American</option>
                                <option value="Delta">Delta</option>
                                <option value="Southwest">Southwest</option>
                                <option value="Alaska">Alaska</option>
                            </select>
                        </div>
                        <div class="col-md-4">
                            <label>&nbsp;</label>
                            <button class="btn btn-success w-100" onclick="uploadFile()">Upload</button>
                        </div>
                    </div>
                </div>

                <div id="uploadStatus" class="mt-3"></div>
            </div>
        </div>

        <!-- Bid Packets Table -->
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Bid Packets</h5>

                <div class="table-responsive">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Airline</th>
                                <th>Month</th>
                                <th>Filename</th>
                                <th>Size</th>
                                <th>Uploaded</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for packet in packets %}
                            <tr>
                                <td>{{ packet.airline }}</td>
                                <td>{{ packet.year }}/{{ "%02d"|format(packet.month) }}</td>
                                <td>{{ packet.filename }}</td>
                                <td>{{ packet.size_mb }} MB</td>
                                <td>{{ packet.upload_date[:10] }}</td>
                                <td>
                                    <button class="btn btn-sm btn-primary" 
                                            onclick="downloadPacket('{{ packet.month_tag }}', '{{ packet.airline }}')">
                                        <i class="bi bi-download"></i>
                                    </button>
                                    <button class="btn btn-sm btn-danger" 
                                            onclick="deletePacket('{{ packet.month_tag }}', '{{ packet.airline }}')">
                                        <i class="bi bi-trash"></i>
                                    </button>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script>
        let selectedFile = null;

        // Drag and drop
        const uploadZone = document.getElementById('uploadZone');

        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('dragover');
        });

        uploadZone.addEventListener('dragleave', () => {
            uploadZone.classList.remove('dragover');
        });

        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragover');

            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFileSelect(files[0]);
            }
        });

        // File input
        document.getElementById('fileInput').addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFileSelect(e.target.files[0]);
            }
        });

        function handleFileSelect(file) {
            if (file.type !== 'application/pdf') {
                showStatus('Please select a PDF file', 'danger');
                return;
            }

            selectedFile = file;
            document.getElementById('uploadForm').style.display = 'block';
            showStatus(`Selected: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`, 'info');

            // Auto-fill month from filename if possible
            const match = file.name.match(/(\d{6})/);
            if (match) {
                document.getElementById('monthTag').value = match[1];
            }
        }

        async function uploadFile() {
            if (!selectedFile) {
                showStatus('Please select a file', 'danger');
                return;
            }

            const monthTag = document.getElementById('monthTag').value;
            const airline = document.getElementById('airline').value;

            if (!monthTag || monthTag.length !== 6) {
                showStatus('Please enter valid month (YYYYMM)', 'danger');
                return;
            }

            if (!airline) {
                showStatus('Please select an airline', 'danger');
                return;
            }

            const formData = new FormData();
            formData.append('file', selectedFile);
            formData.append('month_tag', monthTag);
            formData.append('airline', airline);

            showStatus('Uploading...', 'info');

            try {
                const response = await fetch('/admin/api/upload-bid-packet', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (result.success) {
                    showStatus('Upload successful!', 'success');
                    setTimeout(() => location.reload(), 1500);
                } else {
                    showStatus(result.error || 'Upload failed', 'danger');
                }
            } catch (error) {
                showStatus('Upload error: ' + error, 'danger');
            }
        }

        async function deletePacket(monthTag, airline) {
            if (!confirm(`Delete bid packet for ${airline} ${monthTag}?`)) {
                return;
            }

            try {
                const response = await fetch(`/admin/api/delete-bid-packet/${monthTag}/${airline}`, {
                    method: 'DELETE'
                });

                const result = await response.json();

                if (result.success) {
                    location.reload();
                } else {
                    alert(result.error || 'Delete failed');
                }
            } catch (error) {
                alert('Delete error: ' + error);
            }
        }

        function downloadPacket(monthTag, airline) {
            window.location.href = `/admin/api/download-bid-packet/${monthTag}/${airline}`;
        }

        function showStatus(message, type) {
            const statusDiv = document.getElementById('uploadStatus');
            statusDiv.className = `alert alert-${type}`;
            statusDiv.textContent = message;
            statusDiv.style.display = 'block';
        }
    </script>
</body>
</html>
    """


    # Calculate statistics
    storage_mb = sum(p.get('size_mb', 0) for p in packets) if packets else 0
    storage_mb = round(storage_mb, 1)

    airlines = set(p.get('airline', '') for p in packets if p.get('airline'))
    unique_airlines = len(airlines)


    # Calculate statistics
    storage_mb = sum(p.get('size_mb', 0) for p in packets) if packets else 0
    storage_mb = round(storage_mb, 1)

    airlines = set(p.get('airline', '') for p in packets if p.get('airline'))
    unique_airlines = len(airlines)

    return render_template_string(dashboard_html,
                                  packets=packets,
                                  contracts=contracts,
                                  storage_mb=storage_mb,
                                  unique_airlines=unique_airlines)


# ============================================
# API ROUTES
# ============================================


@admin_bp.route('/api/upload-bid-packet', methods=['POST'])
@require_bearer_token
def api_upload_bid_packet():
    """API endpoint for bid packet upload"""

    if not BidPacketManager:
        return jsonify({
            'success': False,
            'error': 'BidPacketManager not available'
        }), 500

    try:
        manager = BidPacketManager()

        file = request.files.get('file')
        month_tag = request.form.get('month_tag')
        airline = request.form.get('airline')

        if not file:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400

        if not month_tag:
            return jsonify({
                'success': False,
                'error': 'Month tag is required'
            }), 400

        if not airline:
            return jsonify({
                'success': False,
                'error': 'Airline is required'
            }), 400

        result = manager.upload_bid_packet(file, month_tag, airline)

        if result['success']:
            logger.info(f"Bid packet uploaded: {airline} {month_tag}")
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/upload-contract', methods=['POST'])
@require_bearer_token
def api_upload_contract():
    """API endpoint for contract upload"""

    if not BidPacketManager:
        return jsonify({
            'success': False,
            'error': 'BidPacketManager not available'
        }), 500

    try:
        manager = BidPacketManager()

        file = request.files.get('file')
        airline = request.form.get('airline')
        version = request.form.get('version')

        if not file:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400

        if not airline:
            return jsonify({
                'success': False,
                'error': 'Airline is required'
            }), 400

        result = manager.upload_contract(file, airline, version)

        if result['success']:
            logger.info(f"Contract uploaded: {airline}")
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Contract upload error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/delete-bid-packet/<month_tag>/<airline>',
                methods=['DELETE'])
@require_bearer_token
def api_delete_bid_packet(month_tag: str, airline: str):
    """API endpoint to delete bid packet"""

    if not BidPacketManager:
        return jsonify({
            'success': False,
            'error': 'BidPacketManager not available'
        }), 500

    try:
        manager = BidPacketManager()
        result = manager.delete_bid_packet(month_tag, airline)

        if result['success']:
            logger.info(f"Bid packet deleted: {airline} {month_tag}")
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Delete error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/download-bid-packet/<month_tag>/<airline>')
@require_bearer_token
def api_download_bid_packet(month_tag: str, airline: str):
    """API endpoint to download bid packet"""

    if not BidPacketManager:
        return jsonify({
            'success': False,
            'error': 'BidPacketManager not available'
        }), 500

    try:
        manager = BidPacketManager()
        file_data = manager.get_bid_packet_file(month_tag, airline)

        if file_data:
            from flask import Response
            data, filename = file_data
            return Response(data,
                            mimetype='application/pdf',
                            headers={
                                'Content-Disposition':
                                f'attachment; filename={filename}'
                            })
        else:
            return jsonify({'error': 'File not found'}), 404

    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/list-bid-packets')
@require_bearer_token
def api_list_bid_packets():
    """API endpoint to list all bid packets"""

    if not BidPacketManager:
        return jsonify({
            'success': False,
            'error': 'BidPacketManager not available'
        }), 500

    try:
        manager = BidPacketManager()
        packets = manager.get_available_bid_packets()
        return jsonify({
            'success': True,
            'packets': packets,
            'count': len(packets)
        }), 200

    except Exception as e:
        logger.error(f"List error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# LEGACY COMPATIBILITY
# ============================================


@admin_bp.route('/upload-bid', methods=['POST'])
@require_bearer_token
def legacy_upload_bid():
    """Legacy upload endpoint for backward compatibility"""
    return api_upload_bid_packet()


# Export the blueprint
unified_admin = admin_bp
