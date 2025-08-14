"""
Enhanced Admin Portal with Bid Packet Upload
"""
from flask import Blueprint, render_template_string, request, jsonify, session, redirect, url_for
from werkzeug.utils import secure_filename
from functools import wraps
import os
import sys
sys.path.append('src/lib')

from bid_packet_manager import BidPacketManager

admin_portal = Blueprint('admin_portal', __name__, url_prefix='/admin')

ADMIN_PASSWORD = 'vectorbid2025'
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_portal.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_portal.route('/')
@admin_portal.route('/dashboard')
@admin_required
def dashboard():
    """Enhanced admin dashboard with upload section"""

    # Get bid packet manager
    manager = BidPacketManager()
    packets = manager.get_available_bid_packets()

    dashboard_html = """
<!DOCTYPE html>
<html>
<head>
    <title>VectorBid Admin Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .dashboard-card { background: white; border-radius: 15px; padding: 2rem; margin: 2rem 0; }
        .stat-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; 
                     padding: 1.5rem; border-radius: 10px; text-align: center; margin-bottom: 1rem; }
        .stat-number { font-size: 2.5rem; font-weight: bold; }
        .upload-zone { 
            border: 2px dashed #667eea; 
            border-radius: 10px; 
            padding: 2rem; 
            text-align: center;
            background: #f8f9fa;
            cursor: pointer;
            transition: all 0.3s;
        }
        .upload-zone:hover { 
            background: #e9ecef;
            border-color: #764ba2;
        }
        .upload-zone.dragover {
            background: #667eea20;
            border-color: #667eea;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            <span class="navbar-brand">✈️ VectorBid Admin</span>
            <a href="{{ url_for('admin_portal.logout') }}" class="btn btn-outline-light btn-sm">Logout</a>
        </div>
    </nav>

    <div class="container">
        <div class="dashboard-card">
            <h2>Admin Dashboard</h2>

            <!-- Statistics -->
            <div class="row mt-4">
                <div class="col-md-3">
                    <div class="stat-card">
                        <div class="stat-number">{{ packets|length }}</div>
                        <div>Bid Packets</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <div class="stat-number">234</div>
                        <div>Total Pilots</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <div class="stat-number">89</div>
                        <div>Active Today</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <div class="stat-number">72%</div>
                        <div>Success Rate</div>
                    </div>
                </div>
            </div>

            <!-- Upload Section -->
            <div class="row mt-4">
                <div class="col-md-6">
                    <h4>Upload Bid Packet</h4>
                    <form id="bidPacketForm" enctype="multipart/form-data">
                        <div class="mb-3">
                            <label class="form-label">Airline</label>
                            <select class="form-control" id="airline" required>
                                <option value="">Select Airline</option>
                                <option value="UAL">United Airlines</option>
                                <option value="AAL">American Airlines</option>
                                <option value="DAL">Delta Air Lines</option>
                                <option value="SWA">Southwest Airlines</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Month (YYYYMM)</label>
                            <input type="text" class="form-control" id="month_tag" 
                                   placeholder="202502" pattern="[0-9]{6}" maxlength="6" required>
                        </div>
                        <div class="upload-zone" id="bidUploadZone">
                            <input type="file" id="bidFile" accept=".pdf" style="display: none;">
                            <i class="bi bi-cloud-upload" style="font-size: 2rem;"></i>
                            <p class="mt-2 mb-0">Click to select or drag & drop PDF file</p>
                            <small class="text-muted">Monthly bid packet PDF</small>
                        </div>
                        <button type="submit" class="btn btn-primary mt-3">Upload Bid Packet</button>
                    </form>
                </div>

                <div class="col-md-6">
                    <h4>Upload Pilot Contract</h4>
                    <form id="contractForm" enctype="multipart/form-data">
                        <div class="mb-3">
                            <label class="form-label">Airline</label>
                            <select class="form-control" id="contract_airline" required>
                                <option value="">Select Airline</option>
                                <option value="UAL">United Airlines</option>
                                <option value="AAL">American Airlines</option>
                                <option value="DAL">Delta Air Lines</option>
                                <option value="SWA">Southwest Airlines</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Contract Version (Optional)</label>
                            <input type="text" class="form-control" id="contract_version" 
                                   placeholder="2024-2028">
                        </div>
                        <div class="upload-zone" id="contractUploadZone">
                            <input type="file" id="contractFile" accept=".pdf" style="display: none;">
                            <i class="bi bi-file-text" style="font-size: 2rem;"></i>
                            <p class="mt-2 mb-0">Click to select or drag & drop PDF file</p>
                            <small class="text-muted">Pilot contract PDF</small>
                        </div>
                        <button type="submit" class="btn btn-success mt-3">Upload Contract</button>
                    </form>
                </div>
            </div>

            <!-- Available Bid Packets -->
            <div class="mt-5">
                <h4>Available Bid Packets</h4>
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>Month</th>
                                <th>Airline</th>
                                <th>Upload Date</th>
                                <th>Status</th>
                                <th>Trips</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for packet in packets %}
                            <tr>
                                <td>{{ packet.month_tag }}</td>
                                <td>{{ packet.airline }}</td>
                                <td>{{ packet.upload_date[:10] }}</td>
                                <td>
                                    {% if packet.parsed %}
                                    <span class="badge bg-success">Parsed</span>
                                    {% else %}
                                    <span class="badge bg-warning">Processing</span>
                                    {% endif %}
                                </td>
                                <td>{{ packet.trips_count }}</td>
                                <td>
                                    <button class="btn btn-sm btn-primary" onclick="viewPacket('{{ packet.month_tag }}')">View</button>
                                    <button class="btn btn-sm btn-danger" onclick="deletePacket('{{ packet.month_tag }}')">Delete</button>
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
        // Bid Packet Upload
        const bidUploadZone = document.getElementById('bidUploadZone');
        const bidFileInput = document.getElementById('bidFile');

        bidUploadZone.addEventListener('click', () => bidFileInput.click());

        bidUploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            bidUploadZone.classList.add('dragover');
        });

        bidUploadZone.addEventListener('dragleave', () => {
            bidUploadZone.classList.remove('dragover');
        });

        bidUploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            bidUploadZone.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                bidFileInput.files = e.dataTransfer.files;
                updateUploadZone(bidUploadZone, e.dataTransfer.files[0].name);
            }
        });

        bidFileInput.addEventListener('change', (e) => {
            if (e.target.files.length) {
                updateUploadZone(bidUploadZone, e.target.files[0].name);
            }
        });

        // Contract Upload (similar handlers)
        const contractUploadZone = document.getElementById('contractUploadZone');
        const contractFileInput = document.getElementById('contractFile');

        contractUploadZone.addEventListener('click', () => contractFileInput.click());

        // Form submission
        document.getElementById('bidPacketForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = new FormData();
            formData.append('file', bidFileInput.files[0]);
            formData.append('month_tag', document.getElementById('month_tag').value);
            formData.append('airline', document.getElementById('airline').value);

            try {
                const response = await fetch('/admin/api/upload-bid-packet', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();
                if (result.success) {
                    alert('Bid packet uploaded successfully!');
                    location.reload();
                } else {
                    alert('Error: ' + result.error);
                }
            } catch (error) {
                alert('Upload failed: ' + error);
            }
        });

        function updateUploadZone(zone, filename) {
            zone.innerHTML = `
                <i class="bi bi-check-circle" style="font-size: 2rem; color: green;"></i>
                <p class="mt-2 mb-0">Selected: ${filename}</p>
                <small class="text-muted">Ready to upload</small>
            `;
        }

        function viewPacket(monthTag) {
            window.location.href = `/admin/bid-packet/${monthTag}`;
        }

        function deletePacket(monthTag) {
            if (confirm('Are you sure you want to delete this bid packet?')) {
                // Implement delete functionality
                alert('Delete functionality coming soon');
            }
        }
    </script>
</body>
</html>
    """
    return render_template_string(dashboard_html, packets=packets)

@admin_portal.route('/api/upload-bid-packet', methods=['POST'])
@admin_required
def upload_bid_packet():
    """API endpoint for bid packet upload"""
    manager = BidPacketManager()

    file = request.files.get('file')
    month_tag = request.form.get('month_tag')
    airline = request.form.get('airline')

    if not file or not month_tag or not airline:
        return jsonify({'success': False, 'error': 'Missing required fields'})

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'Invalid file type. PDF only.'})

    result = manager.upload_bid_packet(file, month_tag, airline)
    return jsonify(result)

@admin_portal.route('/api/upload-contract', methods=['POST'])
@admin_required
def upload_contract():
    """API endpoint for contract upload"""
    manager = BidPacketManager()

    file = request.files.get('file')
    airline = request.form.get('airline')
    version = request.form.get('version', None)

    if not file or not airline:
        return jsonify({'success': False, 'error': 'Missing required fields'})

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'Invalid file type. PDF only.'})

    result = manager.upload_pilot_contract(file, airline, version)
    return jsonify(result)

@admin_portal.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login"""
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_portal.dashboard'))
        error = "Invalid password"
    else:
        error = None

    login_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Admin Login - VectorBid</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
               min-height: 100vh; display: flex; align-items: center; }
        .login-card { background: white; border-radius: 15px; padding: 2rem; }
    </style>
</head>
<body>
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-4">
                <div class="login-card">
                    <h3 class="text-center mb-4">✈️ VectorBid Admin</h3>
                    {% if error %}
                    <div class="alert alert-danger">{{ error }}</div>
                    {% endif %}
                    <form method="POST">
                        <div class="mb-3">
                            <label>Admin Password</label>
                            <input type="password" class="form-control" name="password" required>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">Login</button>
                    </form>
                    <div class="text-center mt-3">
                        <small class="text-muted">Default: vectorbid2025</small>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
    """
    return render_template_string(login_html, error=error)

@admin_portal.route('/logout')
def logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    return redirect('/admin/login')
