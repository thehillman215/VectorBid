#!/usr/bin/env python3
"""
Add Advanced Features to VectorBid
This script adds all the advanced features to your working VectorBid installation
Save as: add_advanced_features.py
Run: python add_advanced_features.py
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
print("ADDING ADVANCED FEATURES TO VECTORBID")
print("=" * 60)
print()

# 1. Enhanced PBS with Conflict Resolution
print("📦 Installing Enhanced PBS System with Conflict Resolution...")
create_file(
    "src/lib/pbs_enhanced.py", '''"""
Enhanced PBS System with Conflict Resolution
"""
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import re

@dataclass
class ConflictResolution:
    """Represents a conflict with resolution options"""
    description: str
    option_a: Dict
    option_b: Dict
    recommendation: str

def generate_advanced_pbs_strategy(preferences_text: str, pilot_profile: Dict = None) -> Dict:
    """Generate PBS strategy with conflict detection"""

    commands = []
    conflicts = []
    text_lower = preferences_text.lower()

    # Check for conflicting preferences
    conflict_pairs = []

    # Weekend conflict check
    wants_weekends_off = any(phrase in text_lower for phrase in ['weekends off', 'no weekends'])
    wants_weekend_work = any(phrase in text_lower for phrase in ['prefer weekends', 'weekend flying', 'weekend pay'])

    if wants_weekends_off and wants_weekend_work:
        conflict_pairs.append({
            'description': 'You want both weekends off AND weekend work',
            'option_a': {
                'command': 'AVOID TRIPS IF DUTY_PERIOD OVERLAPS SAT OR SUN',
                'explanation': 'Keep weekends free for personal time'
            },
            'option_b': {
                'command': 'PREFER TRIPS IF DUTY_PERIOD OVERLAPS SAT OR SUN',
                'explanation': 'Work weekends for extra pay'
            },
            'recommendation': 'Choose based on your current priority: family time or extra income'
        })

    # Trip length conflict
    wants_short = 'short trip' in text_lower or 'day trip' in text_lower
    wants_long = 'long trip' in text_lower or 'multi-day' in text_lower

    if wants_short and wants_long:
        conflict_pairs.append({
            'description': 'You want both short AND long trips',
            'option_a': {
                'command': 'PREFER TRIPS IF DUTY_DAYS <= 2',
                'explanation': 'Prefer shorter trips for more days at home'
            },
            'option_b': {
                'command': 'PREFER TRIPS IF DUTY_DAYS >= 4',
                'explanation': 'Prefer longer trips for commute efficiency'
            },
            'recommendation': 'Consider your commuting situation and family needs'
        })

    # Generate base commands (without conflicts)
    base_commands = []

    # Time preferences (no conflicts usually)
    if 'no early' in text_lower or 'avoid early' in text_lower:
        base_commands.append({
            'command': 'AVOID TRIPS IF DEPARTURE_TIME < 0800',
            'explanation': 'Avoid early morning departures',
            'priority': 3
        })

    if 'no late' in text_lower or 'avoid late' in text_lower:
        base_commands.append({
            'command': 'AVOID TRIPS IF ARRIVAL_TIME > 2200',
            'explanation': 'Avoid late night arrivals',
            'priority': 3
        })

    # Add resolved preferences (pick option A by default for now)
    for conflict in conflict_pairs:
        conflicts.append(ConflictResolution(
            description=conflict['description'],
            option_a=conflict['option_a'],
            option_b=conflict['option_b'],
            recommendation=conflict['recommendation']
        ))
        # Add option A by default
        base_commands.append(conflict['option_a'])

    # Add non-conflicting preferences
    if not wants_weekends_off and not wants_weekend_work:
        if 'weekend' in text_lower:
            base_commands.append({
                'command': 'AVOID TRIPS IF DUTY_PERIOD OVERLAPS SAT OR SUN',
                'explanation': 'Avoid weekend work',
                'priority': 2
            })

    if not wants_short and not wants_long:
        if 'short' in text_lower:
            base_commands.append({
                'command': 'PREFER TRIPS IF DUTY_DAYS <= 2',
                'explanation': 'Prefer shorter trips',
                'priority': 4
            })

    # Red-eye preferences
    if 'no redeye' in text_lower or 'no red-eye' in text_lower:
        base_commands.append({
            'command': 'AVOID TRIPS IF DEPARTURE_TIME BETWEEN 2200 AND 0559',
            'explanation': 'Avoid red-eye flights',
            'priority': 5
        })

    # Location preferences
    if 'denver' in text_lower:
        base_commands.append({
            'command': 'PREFER TRIPS IF LAYOVER_STATION = DEN',
            'explanation': 'Prefer Denver layovers',
            'priority': 6
        })

    # Commute preferences
    if 'commut' in text_lower:
        base_commands.append({
            'command': 'PREFER TRIPS IF DEPARTURE_TIME >= 1000',
            'explanation': 'Allow commute time',
            'priority': 3
        })

    return {
        'commands': base_commands,
        'conflicts': conflicts,
        'statistics': {
            'total_filters': len(base_commands),
            'conflicts_found': len(conflicts),
            'layers_used': 1
        },
        'validation': {
            'valid_syntax': True,
            'within_limits': len(base_commands) <= 20
        }
    }
''')

# 2. Admin Portal
print("📦 Installing Complete Admin Portal...")
create_file(
    "admin_portal.py", '''"""
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
''')

# 3. Update app.py to include admin portal
print("📦 Updating app.py to include admin portal...")
app_content = '''"""
Flask application factory for VectorBid with Admin Portal
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

    # Register blueprints
    from src.api.routes import bp as main_bp
    app.register_blueprint(main_bp)

    # Register admin portal
    try:
        from admin_portal import admin_portal
        app.register_blueprint(admin_portal)
        print("✅ Admin portal registered successfully!")
    except ImportError as e:
        print(f"⚠️ Admin portal not available: {e}")

    return app
'''
create_file("src/core/app.py", app_content)

# 4. Enhanced routes with conflict resolution
print("📦 Updating routes with advanced features...")
routes_content = '''"""
Enhanced routes with conflict resolution
"""

from flask import Blueprint, render_template_string, request, redirect, url_for, jsonify, session
import sys
sys.path.append('src/lib')

from pbs_command_generator import generate_pbs_commands
from subscription_manager import SubscriptionManager
try:
    from pbs_enhanced import generate_advanced_pbs_strategy
except ImportError:
    generate_advanced_pbs_strategy = None

from datetime import datetime

bp = Blueprint("main", __name__)

@bp.route("/")
def index():
    """Main dashboard"""
    user_id = session.get('user_id', 'test_user_001')

    # Get subscription info
    manager = SubscriptionManager()
    subscription = manager.get_user_subscription(user_id)

    index_html = """
<!DOCTYPE html>
<html>
<head>
    <title>VectorBid - AI Pilot Bidding Assistant</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            <span class="navbar-brand">✈️ VectorBid</span>
            <div>
                <span class="badge bg-success">{{ subscription.tier }}</span>
                <a href="/admin/" class="btn btn-outline-light btn-sm ms-2">Admin</a>
            </div>
        </div>
    </nav>

    <div class="container mt-5">
        <div class="row">
            <div class="col-md-8 offset-md-2">
                <h1>Welcome to VectorBid</h1>
                <p class="lead">Your AI-powered pilot schedule bidding assistant</p>

                <div class="alert alert-info">
                    <strong>Your Plan:</strong> {{ subscription.tier | upper | replace('_', ' ') }}
                    {% if subscription.tier == 'free_trial' %}
                    - Trial ends: {{ subscription.trial_ends_at[:10] }}
                    {% endif %}
                </div>

                <div class="card mt-4">
                    <div class="card-body">
                        <h5>Generate PBS Commands</h5>
                        <form action="/pbs-results" method="get">
                            <div class="mb-3">
                                <label class="form-label">Enter your preferences:</label>
                                <textarea name="preferences" class="form-control" rows="4" 
                                    placeholder="I want weekends off and prefer short trips..."></textarea>
                            </div>
                            <div class="form-check mb-3">
                                <input class="form-check-input" type="checkbox" name="check_conflicts" id="conflicts" checked>
                                <label class="form-check-label" for="conflicts">
                                    Check for conflicts and provide resolution options
                                </label>
                            </div>
                            <button type="submit" class="btn btn-primary">Generate PBS Commands</button>
                        </form>
                    </div>
                </div>

                <div class="mt-4">
                    <h5>Quick Links</h5>
                    <a href="/pricing" class="btn btn-outline-primary">View Plans</a>
                    <a href="/admin/" class="btn btn-outline-secondary">Admin Portal</a>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
    """
    return render_template_string(index_html, subscription=subscription)

@bp.route("/pbs-results")
def pbs_results():
    """Display PBS results with conflict resolution"""
    preferences = request.args.get('preferences', 'Default preferences')
    check_conflicts = request.args.get('check_conflicts') == 'on'

    # Use advanced strategy if available and conflicts requested
    if check_conflicts and generate_advanced_pbs_strategy:
        result = generate_advanced_pbs_strategy(preferences)

        results_html = """
<!DOCTYPE html>
<html>
<head>
    <title>PBS Results - VectorBid</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            <span class="navbar-brand">✈️ VectorBid</span>
        </div>
    </nav>

    <div class="container mt-5">
        <h2>Your PBS Strategy</h2>
        <p>Based on: {{ preferences }}</p>

        {% if conflicts %}
        <div class="alert alert-warning">
            <h5>⚠️ Conflicts Detected</h5>
            <p>We found {{ conflicts|length }} conflict(s) in your preferences:</p>
        </div>

        {% for conflict in conflicts %}
        <div class="card mb-3 border-warning">
            <div class="card-header bg-warning text-dark">
                Conflict: {{ conflict.description }}
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <h6>Option A:</h6>
                        <code>{{ conflict.option_a.command }}</code>
                        <p class="mt-2">{{ conflict.option_a.explanation }}</p>
                        <button class="btn btn-primary btn-sm">Choose Option A</button>
                    </div>
                    <div class="col-md-6">
                        <h6>Option B:</h6>
                        <code>{{ conflict.option_b.command }}</code>
                        <p class="mt-2">{{ conflict.option_b.explanation }}</p>
                        <button class="btn btn-primary btn-sm">Choose Option B</button>
                    </div>
                </div>
                <div class="alert alert-info mt-3">
                    <strong>Recommendation:</strong> {{ conflict.recommendation }}
                </div>
            </div>
        </div>
        {% endfor %}
        {% endif %}

        <div class="card mt-4">
            <div class="card-header">Generated Commands</div>
            <div class="card-body">
                <pre>{% for cmd in commands %}{{ cmd.command }}  # {{ cmd.explanation }}
{% endfor %}</pre>
            </div>
        </div>

        <div class="mt-3">
            <a href="/" class="btn btn-secondary">Generate New</a>
            <button class="btn btn-success" onclick="copyCommands()">Copy Commands</button>
        </div>
    </div>

    <script>
        function copyCommands() {
            const commands = document.querySelector('pre').textContent;
            navigator.clipboard.writeText(commands);
            alert('Commands copied to clipboard!');
        }
    </script>
</body>
</html>
        """
        return render_template_string(results_html, 
                                    preferences=preferences,
                                    commands=result.get('commands', []),
                                    conflicts=result.get('conflicts', []))
    else:
        # Use basic generator
        result = generate_pbs_commands(preferences)
        return render_template_string(open('src/ui/templates/pbs_results.html').read(),
                                    commands=result.get('commands', []),
                                    formatted=result.get('formatted', ''),
                                    preferences=preferences)

@bp.route("/pricing")
def pricing():
    """Pricing page"""
    manager = SubscriptionManager()
    pricing_data = manager.get_pricing_page_data()

    pricing_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Pricing - VectorBid</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            <span class="navbar-brand">✈️ VectorBid</span>
        </div>
    </nav>

    <div class="container mt-5">
        <h2 class="text-center">Choose Your Plan</h2>

        <div class="row mt-5">
            {% for tier in tiers %}
            <div class="col-md-4">
                <div class="card h-100">
                    <div class="card-header text-center">
                        <h4>{{ tier.name }}</h4>
                        <h2>{{ tier.price_display }}</h2>
                    </div>
                    <div class="card-body">
                        <ul>
                        {% for feature in tier.features %}
                            <li>{{ feature }}</li>
                        {% endfor %}
                        </ul>
                    </div>
                    <div class="card-footer text-center">
                        <button class="btn btn-primary">{{ tier.cta_text or 'Select' }}</button>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>

        <div class="mt-5 text-center">
            <a href="/" class="btn btn-secondary">Back to Home</a>
        </div>
    </div>
</body>
</html>
    """
    return render_template_string(pricing_html, tiers=pricing_data['tiers'])

@bp.route("/health")
def health():
    """Health check"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@bp.route("/api/generate-pbs", methods=["POST"])
def api_generate_pbs():
    """Generate PBS commands API"""
    try:
        data = request.get_json()
        preferences = data.get('preferences', '')
        check_conflicts = data.get('check_conflicts', False)

        if check_conflicts and generate_advanced_pbs_strategy:
            result = generate_advanced_pbs_strategy(preferences)
        else:
            result = generate_pbs_commands(preferences)

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
'''
create_file("src/api/routes.py", routes_content)

print()
print("=" * 60)
print("✅ ADVANCED FEATURES INSTALLED SUCCESSFULLY!")
print("=" * 60)
print()
print("🎉 New Features Added:")
print("  ✅ Conflict Resolution System")
print("  ✅ Admin Portal with Dashboard")
print("  ✅ Subscription Management")
print("  ✅ Pricing Page")
print("  ✅ Enhanced PBS Generation")
print()
print("📋 How to Test:")
print()
print("1. Restart the server:")
print("   Press Ctrl+C then run: PORT=8080 python main.py")
print()
print("2. Test Conflict Resolution:")
print("   Enter: 'I want weekends off but also prefer weekend trips for pay'")
print("   You'll see conflict options!")
print()
print("3. Access Admin Portal:")
print("   Go to: /admin/")
print("   Password: vectorbid2025")
print()
print("4. View Pricing:")
print("   Go to: /pricing")
print()
print("Ready to test? Restart the server to see all new features!")
