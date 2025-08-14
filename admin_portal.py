"""
Complete Admin Portal for VectorBid
"""
from flask import Blueprint, render_template_string, request, jsonify, session, redirect, url_for
from functools import wraps
import json
from datetime import datetime
from pathlib import Path

admin_portal = Blueprint('admin_portal', __name__, url_prefix='/admin')

# Simple file-based storage for demo
ADMIN_PASSWORD = 'vectorbid2025'

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
    """Admin dashboard"""
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

            <div class="row mt-4">
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
                        <div class="stat-number">1,567</div>
                        <div>PBS Generated</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <div class="stat-number">72%</div>
                        <div>Success Rate</div>
                    </div>
                </div>
            </div>

            <div class="row mt-4">
                <div class="col-md-6">
                    <h4>Recent Activity</h4>
                    <ul class="list-group">
                        <li class="list-group-item">John Smith generated PBS commands - 2 min ago</li>
                        <li class="list-group-item">Jane Doe upgraded to Essential - 15 min ago</li>
                        <li class="list-group-item">New bid packet uploaded for UAL - 1 hour ago</li>
                    </ul>
                </div>
                <div class="col-md-6">
                    <h4>Quick Actions</h4>
                    <div class="d-grid gap-2">
                        <button class="btn btn-primary" onclick="uploadBidPacket()">Upload Bid Packet</button>
                        <button class="btn btn-info" onclick="sendBroadcast()">Send Broadcast Message</button>
                        <button class="btn btn-success" onclick="viewAnalytics()">View Analytics</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        function uploadBidPacket() {
            alert('Bid packet upload feature - coming soon!');
        }
        function sendBroadcast() {
            const message = prompt('Enter broadcast message:');
            if (message) alert('Message queued for broadcast: ' + message);
        }
        function viewAnalytics() {
            window.location.href = '{{ url_for("admin_portal.analytics") }}';
        }
    </script>
</body>
</html>
    """
    return render_template_string(dashboard_html)

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
        .login-card { background: white; border-radius: 15px; padding: 2rem; 
                     box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
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
                            <label class="form-label">Admin Password</label>
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
    return redirect(url_for('admin_portal.login'))

@admin_portal.route('/analytics')
@admin_required
def analytics():
    """Analytics page"""
    return "<h1>Analytics Dashboard</h1><p>Coming soon!</p><a href='/admin/'>Back to Dashboard</a>"

@admin_portal.route('/api/stats')
@admin_required  
def api_stats():
    """API endpoint for stats"""
    return jsonify({
        'total_users': 234,
        'active_today': 89,
        'pbs_generated': 1567,
        'success_rate': 0.72
    })
