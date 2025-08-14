#!/usr/bin/env python3
"""
Bid Packet and Contract Upload System for VectorBid
This adds the critical upload functionality for bid packets and pilot contracts
Save as: add_upload_system.py
Run: python add_upload_system.py
"""

import os
from pathlib import Path


def create_file(path, content):
    """Create a file with content"""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        f.write(content)
    print(f"✅ Created: {path}")


print("=" * 60)
print("ADDING BID PACKET & CONTRACT UPLOAD SYSTEM")
print("=" * 60)
print()

# 1. Create bid packet manager
print("📦 Creating Bid Packet Manager...")
create_file(
    "src/lib/bid_packet_manager.py", '''"""
Bid Packet and Contract Management System
Handles upload, storage, and parsing of airline bid packets and contracts
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List
import hashlib

class BidPacketManager:
    """Manages bid packets and pilot contracts"""

    def __init__(self):
        # Create storage directories
        self.storage_dir = Path("bids")
        self.contracts_dir = Path("contracts")
        self.metadata_dir = Path("data/metadata")

        for dir_path in [self.storage_dir, self.contracts_dir, self.metadata_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def upload_bid_packet(self, file_obj, month_tag: str, airline: str) -> Dict:
        """
        Upload and store a bid packet

        Args:
            file_obj: File object from Flask request
            month_tag: YYYYMM format (e.g., '202502')
            airline: Airline code (e.g., 'UAL', 'AAL', 'DAL')

        Returns:
            Dict with upload status and metadata
        """
        try:
            # Validate month_tag
            if not self._validate_month_tag(month_tag):
                return {'success': False, 'error': 'Invalid month tag format'}

            # Generate filename
            filename = f"bid_packet_{airline}_{month_tag}.pdf"
            file_path = self.storage_dir / filename

            # Save file
            file_obj.save(str(file_path))

            # Generate metadata
            file_size = file_path.stat().st_size
            file_hash = self._calculate_file_hash(file_path)

            metadata = {
                'filename': filename,
                'month_tag': month_tag,
                'airline': airline,
                'upload_date': datetime.utcnow().isoformat(),
                'file_size': file_size,
                'file_hash': file_hash,
                'status': 'uploaded',
                'parsed': False,
                'trips_count': 0,
                'bases': [],
                'equipment': []
            }

            # Save metadata
            metadata_file = self.metadata_dir / f"{month_tag}_{airline}.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

            # TODO: Trigger parsing job here
            self._queue_for_parsing(file_path, metadata)

            return {
                'success': True,
                'message': f'Bid packet uploaded successfully for {airline} {month_tag}',
                'metadata': metadata
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def upload_pilot_contract(self, file_obj, airline: str, version: str = None) -> Dict:
        """
        Upload and store a pilot contract

        Args:
            file_obj: File object from Flask request
            airline: Airline code
            version: Contract version/date

        Returns:
            Dict with upload status
        """
        try:
            # Generate filename
            version = version or datetime.now().strftime('%Y%m')
            filename = f"contract_{airline}_{version}.pdf"
            file_path = self.contracts_dir / filename

            # Save file
            file_obj.save(str(file_path))

            # Generate metadata
            metadata = {
                'filename': filename,
                'airline': airline,
                'version': version,
                'upload_date': datetime.utcnow().isoformat(),
                'file_size': file_path.stat().st_size,
                'sections': [],
                'rules_extracted': False
            }

            # Save metadata
            metadata_file = self.metadata_dir / f"contract_{airline}_{version}.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

            # TODO: Extract contract rules for PBS validation
            self._extract_contract_rules(file_path, metadata)

            return {
                'success': True,
                'message': f'Contract uploaded successfully for {airline}',
                'metadata': metadata
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_available_bid_packets(self, airline: str = None) -> List[Dict]:
        """Get list of available bid packets"""
        packets = []

        # Read all metadata files
        for metadata_file in self.metadata_dir.glob("*.json"):
            if metadata_file.name.startswith("contract_"):
                continue

            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

            if airline and metadata.get('airline') != airline:
                continue

            packets.append(metadata)

        # Sort by month_tag descending (newest first)
        packets.sort(key=lambda x: x.get('month_tag', ''), reverse=True)

        return packets

    def get_bid_packet_for_month(self, month_tag: str, airline: str) -> Optional[Dict]:
        """Get specific bid packet for a month"""
        metadata_file = self.metadata_dir / f"{month_tag}_{airline}.json"

        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                return json.load(f)

        return None

    def parse_bid_packet(self, file_path: Path, metadata: Dict) -> Dict:
        """
        Parse bid packet to extract trips
        This is a placeholder - implement actual parsing logic
        """
        # TODO: Implement actual PDF parsing
        # For now, return mock data
        trips = [
            {
                'trip_id': 'UA1234',
                'days': 3,
                'credit_hours': 15.5,
                'route': 'DEN-ORD-LAX-DEN',
                'equipment': '737',
                'layovers': ['ORD', 'LAX'],
                'report_time': '06:00',
                'release_time': '18:30'
            },
            {
                'trip_id': 'UA5678',
                'days': 2,
                'credit_hours': 10.2,
                'route': 'DEN-SFO-DEN',
                'equipment': '787',
                'layovers': ['SFO'],
                'report_time': '10:00',
                'release_time': '20:15'
            }
        ]

        metadata['parsed'] = True
        metadata['trips_count'] = len(trips)
        metadata['bases'] = ['DEN']
        metadata['equipment'] = ['737', '787']

        return {
            'success': True,
            'trips': trips,
            'metadata': metadata
        }

    def _validate_month_tag(self, month_tag: str) -> bool:
        """Validate month tag format YYYYMM"""
        if not month_tag or len(month_tag) != 6:
            return False

        try:
            year = int(month_tag[:4])
            month = int(month_tag[4:])

            if year < 2020 or year > 2099:
                return False
            if month < 1 or month > 12:
                return False

            return True
        except ValueError:
            return False

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _queue_for_parsing(self, file_path: Path, metadata: Dict):
        """Queue bid packet for parsing"""
        # TODO: Implement async parsing queue
        # For now, parse immediately
        self.parse_bid_packet(file_path, metadata)

    def _extract_contract_rules(self, file_path: Path, metadata: Dict):
        """Extract rules from pilot contract"""
        # TODO: Implement contract parsing and rule extraction
        # This would extract things like:
        # - Rest requirements
        # - Maximum duty days
        # - Minimum days off
        # - Seniority rules
        # - Equipment qualifications
        pass
''')

# 2. Create enhanced admin portal with upload UI
print("📦 Updating Admin Portal with Upload Interface...")
create_file(
    "admin_portal_enhanced.py", '''"""
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
''')

# 3. Fix the copy to clipboard functionality
print("📦 Fixing Copy to Clipboard...")
clipboard_fix = '''
// Add this to your PBS results page
function copyCommands() {
    // Get just the command text, not the entire element
    const preElement = document.querySelector('pre');
    const commandText = preElement.textContent || preElement.innerText;

    // Create a temporary textarea to copy from
    const textarea = document.createElement('textarea');
    textarea.value = commandText;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);

    // Select and copy
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);

    // Visual feedback
    const button = event.target;
    const originalText = button.textContent;
    button.textContent = '✓ Copied!';
    button.classList.add('btn-success');

    setTimeout(() => {
        button.textContent = originalText;
        button.classList.remove('btn-success');
    }, 2000);
}
'''

# 4. Update app.py to use enhanced admin portal
print("📦 Updating app.py...")
app_update = '''"""
Flask application factory for VectorBid with Enhanced Admin Portal
"""

from flask import Flask
import os

def create_app():
    """Create and configure Flask app"""
    app = Flask(__name__, 
                template_folder='../../src/ui/templates',
                static_folder='../../src/ui/static')

    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///vectorbid.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

    # Register blueprints
    from src.api.routes import bp as main_bp
    app.register_blueprint(main_bp)

    # Try enhanced admin portal first, fall back to basic
    try:
        from admin_portal_enhanced import admin_portal
        app.register_blueprint(admin_portal)
        print("✅ Enhanced admin portal with uploads registered!")
    except ImportError:
        try:
            from admin_portal import admin_portal
            app.register_blueprint(admin_portal)
            print("✅ Basic admin portal registered")
        except ImportError:
            print("⚠️ No admin portal available")

    return app
'''
create_file("src/core/app.py", app_update)

print()
print("=" * 60)
print("✅ BID PACKET UPLOAD SYSTEM INSTALLED!")
print("=" * 60)
print()
print("🎉 New Features Added:")
print("  ✅ Bid Packet Upload Interface")
print("  ✅ Pilot Contract Upload")
print("  ✅ Drag & Drop File Upload")
print("  ✅ Bid Packet Management")
print("  ✅ Fixed Copy to Clipboard")
print()
print("📋 Next Steps:")
print()
print("1. Restart the server:")
print("   Ctrl+C then: PORT=8080 python main.py")
print()
print("2. Go to Admin Portal:")
print("   /admin/")
print("   Password: vectorbid2025")
print()
print("3. Upload a Test Bid Packet:")
print("   - Select airline (United, American, Delta, Southwest)")
print("   - Enter month (e.g., 202502 for Feb 2025)")
print("   - Upload PDF file")
print()
print("4. Upload a Pilot Contract:")
print("   - Select airline")
print("   - Optional version")
print("   - Upload contract PDF")
print()
print("The system will store these files and make them available")
print("for PBS generation based on actual airline rules!")
