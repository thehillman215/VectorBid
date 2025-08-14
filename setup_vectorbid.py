#!/usr/bin/env python3
"""
VectorBid Quick Setup Script
This creates all the necessary files for your VectorBid installation
Save this as: setup_vectorbid.py
Then run: python setup_vectorbid.py
"""

import os
import sys
from pathlib import Path


def create_file(path, content):
    """Create a file with the given content"""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        f.write(content)
    print(f"✅ Created: {path}")


def main():
    print("=" * 60)
    print("VECTORBID QUICK SETUP")
    print("=" * 60)
    print("\nThis will create all necessary files for VectorBid\n")

    # Create directory structure
    directories = [
        "src/lib", "src/api", "src/auth", "src/core", "src/ui/templates/admin",
        "src/ui/static", "data", "bids", "uploads", "backups"
    ]

    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {dir_path}")

    print("\n📝 Creating core files...\n")

    # 1. Create PBS Command Generator
    create_file(
        "src/lib/pbs_command_generator.py", '''"""
PBS Command Generator for VectorBid
Generates PBS commands from natural language preferences
"""

import re
from typing import List, Dict, Optional

def generate_pbs_commands(preferences_text: str, pilot_profile: Dict = None) -> Dict:
    """Generate PBS commands from natural language preferences"""

    if not preferences_text:
        return {
            'commands': [{'command': 'PREFER TRIPS IF QUALITY_OF_LIFE = HIGH', 
                         'explanation': 'Default preference',
                         'priority': 10,
                         'category': 'default'}],
            'formatted': 'PREFER TRIPS IF QUALITY_OF_LIFE = HIGH',
            'errors': [],
            'stats': {'total_commands': 1, 'categories': 1, 'has_conflicts': False, 'preference_coverage': 50.0}
        }

    commands = []
    text_lower = preferences_text.lower()

    # Weekend preferences
    if any(phrase in text_lower for phrase in ['weekends off', 'no weekends', 'avoid weekends']):
        commands.append({
            'command': 'AVOID TRIPS IF DUTY_PERIOD OVERLAPS SAT OR SUN',
            'explanation': 'Avoid weekend work',
            'priority': 2,
            'category': 'weekends'
        })

    # Early morning preferences  
    if any(phrase in text_lower for phrase in ['no early', 'avoid early', 'late start']):
        commands.append({
            'command': 'AVOID TRIPS IF DEPARTURE_TIME < 0800',
            'explanation': 'Avoid early morning departures',
            'priority': 3,
            'category': 'time_of_day'
        })

    # Late night preferences
    if any(phrase in text_lower for phrase in ['no late', 'avoid late', 'early finish']):
        commands.append({
            'command': 'AVOID TRIPS IF ARRIVAL_TIME > 2200',
            'explanation': 'Avoid late night arrivals',
            'priority': 3,
            'category': 'time_of_day'
        })

    # Trip length preferences
    if 'short trip' in text_lower or 'day trip' in text_lower:
        commands.append({
            'command': 'PREFER TRIPS IF DUTY_DAYS <= 2',
            'explanation': 'Prefer shorter trips',
            'priority': 4,
            'category': 'trip_length'
        })
    elif 'long trip' in text_lower:
        commands.append({
            'command': 'PREFER TRIPS IF DUTY_DAYS >= 4',
            'explanation': 'Prefer longer trips',
            'priority': 4,
            'category': 'trip_length'
        })

    # Red-eye preferences
    if any(phrase in text_lower for phrase in ['no redeye', 'avoid redeye', 'no red-eye']):
        commands.append({
            'command': 'AVOID TRIPS IF DEPARTURE_TIME BETWEEN 2200 AND 0559',
            'explanation': 'Avoid red-eye flights',
            'priority': 5,
            'category': 'time_of_day'
        })

    # Commute preferences
    if any(phrase in text_lower for phrase in ['commut', 'drive to', 'travel to']):
        commands.append({
            'command': 'PREFER TRIPS IF DEPARTURE_TIME >= 1000',
            'explanation': 'Allow time for commuting',
            'priority': 3,
            'category': 'commute'
        })

    # Location preferences
    location_map = {
        'denver': 'DEN',
        'chicago': 'ORD', 
        'los angeles': 'LAX',
        'san francisco': 'SFO',
        'houston': 'IAH'
    }

    for city, code in location_map.items():
        if city in text_lower or code.lower() in text_lower:
            commands.append({
                'command': f'PREFER TRIPS IF LAYOVER_STATION = {code}',
                'explanation': f'Prefer {city} layovers',
                'priority': 6,
                'category': 'locations'
            })

    # Add profile-based preferences
    if pilot_profile:
        if pilot_profile.get('base'):
            # Extract airport code from something like "Denver (DEN)"
            import re
            match = re.search(r'\\(([A-Z]{3})\\)', pilot_profile['base'])
            if match:
                base_code = match.group(1)
                commands.append({
                    'command': f'PREFER TRIPS IF BASE = {base_code}',
                    'explanation': f'Home base preference',
                    'priority': 7,
                    'category': 'locations'
                })

        if pilot_profile.get('fleet'):
            for aircraft in pilot_profile['fleet']:
                commands.append({
                    'command': f'PREFER TRIPS IF EQUIPMENT = {aircraft}',
                    'explanation': f'Qualified equipment: {aircraft}',
                    'priority': 8,
                    'category': 'equipment'
                })

    # Add default if no commands generated
    if not commands:
        commands.append({
            'command': 'PREFER TRIPS IF QUALITY_OF_LIFE = HIGH',
            'explanation': 'Default quality of life preference',
            'priority': 10,
            'category': 'default'
        })

    # Format commands
    formatted = "# VectorBid PBS Commands\\n"
    formatted += f"# Generated from: {preferences_text[:50]}...\\n\\n"

    for cmd in sorted(commands, key=lambda x: x['priority']):
        formatted += f"{cmd['command']}  # {cmd['explanation']}\\n"

    return {
        'commands': commands,
        'formatted': formatted,
        'errors': [],
        'stats': {
            'total_commands': len(commands),
            'categories': len(set(cmd['category'] for cmd in commands)),
            'has_conflicts': False,
            'preference_coverage': min(100, len(commands) * 20)
        }
    }
''')

    # 2. Create Subscription Manager
    create_file(
        "src/lib/subscription_manager.py", '''"""
Subscription Management System for VectorBid
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Optional, List, Tuple
import json
from pathlib import Path

class SubscriptionTier(Enum):
    FREE_TRIAL = "free_trial"
    ESSENTIAL = "essential"
    PRO = "pro"

class SubscriptionManager:
    """Manages user subscriptions"""

    def __init__(self):
        self.data_file = Path("data/subscriptions.json")
        self.data_file.parent.mkdir(exist_ok=True)

    def create_new_user_subscription(self, user_id: str) -> Dict:
        """Create a new free trial subscription"""
        subscription = {
            'user_id': user_id,
            'tier': SubscriptionTier.FREE_TRIAL.value,
            'status': 'active',
            'started_at': datetime.utcnow().isoformat(),
            'trial_ends_at': (datetime.utcnow() + timedelta(days=60)).isoformat(),
            'current_period_end': (datetime.utcnow() + timedelta(days=60)).isoformat(),
            'usage': {'monthly_generations': 0}
        }

        self._save_subscription(subscription)
        return subscription

    def get_user_subscription(self, user_id: str) -> Optional[Dict]:
        """Get user subscription"""
        subs = self._load_subscriptions()

        if user_id not in subs:
            return self.create_new_user_subscription(user_id)

        return subs[user_id]

    def check_feature_access(self, user_id: str, feature: str) -> Tuple[bool, str]:
        """Check if user has access to feature"""
        subscription = self.get_user_subscription(user_id)

        if subscription['status'] != 'active':
            return False, "Subscription expired"

        # For MVP, all features available during trial
        return True, "Access granted"

    def _save_subscription(self, subscription: Dict):
        """Save subscription to file"""
        subs = self._load_subscriptions()
        subs[subscription['user_id']] = subscription

        with open(self.data_file, 'w') as f:
            json.dump(subs, f, indent=2)

    def _load_subscriptions(self) -> Dict:
        """Load subscriptions from file"""
        if self.data_file.exists():
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return {}

    def get_pricing_page_data(self) -> Dict:
        """Get pricing page data"""
        return {
            'tiers': [
                {
                    'id': 'free_trial',
                    'name': 'Free Trial',
                    'price': 0,
                    'price_display': 'Free for 60 days',
                    'features': [
                        'Upload schedule files',
                        'Basic PBS command generation',
                        'Save preferences',
                        'View bid packets'
                    ]
                },
                {
                    'id': 'essential',
                    'name': 'Essential',
                    'price': 19.99,
                    'price_display': '$19.99/mo',
                    'features': [
                        'Everything in Free Trial',
                        'Advanced PBS generation',
                        'Unlimited preferences',
                        'Conflict resolution',
                        '12-month history',
                        'Priority support'
                    ]
                },
                {
                    'id': 'pro',
                    'name': 'Professional',
                    'price': 39.99,
                    'price_display': '$39.99/mo',
                    'features': [
                        'Everything in Essential',
                        'Advanced analytics',
                        'Career progression tracking',
                        'API access',
                        'Phone support'
                    ]
                }
            ]
        }
''')

    # 3. Create Admin Analytics
    create_file(
        "src/lib/admin_analytics.py", '''"""
Admin Analytics System for VectorBid
"""

from datetime import datetime
from typing import Dict, List

class PilotAnalytics:
    """Analytics for individual pilots"""

    def get_pilot_analytics(self, user_id: str) -> Dict:
        """Get pilot analytics"""
        return {
            'user_id': user_id,
            'success_metrics': {
                'overall_success_rate': 0.72,
                'trend': 'improving',
                'average_satisfaction': 8.2
            },
            'preference_patterns': {
                'most_common_preferences': [
                    {'preference': 'Weekends off', 'frequency': 0.92},
                    {'preference': 'No early mornings', 'frequency': 0.78}
                ]
            },
            'career_progression': {
                'seniority_progression': {
                    'current_seniority': 245,
                    'percentile': 72
                }
            },
            'usage_statistics': {
                'account_created': '2024-01-15',
                'bids_generated': 24,
                'last_active': datetime.utcnow().isoformat()
            }
        }

class BroadcastSystem:
    """Broadcast messaging system"""

    def __init__(self):
        self.messages = []

    def create_broadcast(self, message_type: str, content: str) -> Dict:
        """Create a broadcast message"""
        message = {
            'id': f'msg_{len(self.messages) + 1}',
            'type': message_type,
            'content': content,
            'created_at': datetime.utcnow().isoformat()
        }
        self.messages.append(message)
        return message

    def get_broadcast_analytics(self) -> Dict:
        """Get broadcast analytics"""
        return {
            'total_sent': len(self.messages),
            'recent_messages': self.messages[-5:]
        }

class AdminDashboard:
    """Main admin dashboard"""

    def __init__(self):
        self.pilot_analytics = PilotAnalytics()
        self.broadcast_system = BroadcastSystem()

    def get_dashboard_data(self) -> Dict:
        """Get dashboard data"""
        return {
            'system_stats': {
                'total_users': 234,
                'active_users_30d': 89,
                'bids_generated': 1567
            },
            'broadcast_stats': self.broadcast_system.get_broadcast_analytics()
        }
''')

    # 4. Create simplified routes
    create_file(
        "src/api/routes.py", '''"""
Main routes for VectorBid
"""

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session
import sys
sys.path.append('src/lib')

try:
    from pbs_command_generator import generate_pbs_commands
    from subscription_manager import SubscriptionManager
except ImportError:
    print("Warning: Some modules not yet installed")
    generate_pbs_commands = None
    SubscriptionManager = None

bp = Blueprint("main", __name__)

@bp.route("/")
def index():
    """Main dashboard"""
    # For testing, use a default user
    user_id = session.get('user_id', 'test_user_001')
    return render_template("index.html", user=user_id)

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

        if generate_pbs_commands:
            result = generate_pbs_commands(preferences)
        else:
            result = {
                'commands': [{'command': 'PREFER TRIPS IF QUALITY_OF_LIFE = HIGH',
                             'explanation': 'Default preference'}],
                'stats': {'total_commands': 1}
            }

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route("/pbs-results")
def pbs_results():
    """Display PBS results"""
    # Get from session or generate default
    preferences = request.args.get('preferences', 'Default preferences')

    if generate_pbs_commands:
        result = generate_pbs_commands(preferences)
    else:
        result = {'commands': [], 'formatted': '', 'stats': {}}

    return render_template("pbs_results.html",
                         commands=result.get('commands', []),
                         formatted=result.get('formatted', ''),
                         preferences=preferences)

# Import datetime at the top
from datetime import datetime
''')

    # 5. Create basic app.py
    create_file(
        "src/core/app.py", '''"""
Flask application factory for VectorBid
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

    # Try to register admin portal if it exists
    try:
        from admin_portal_complete import admin_portal
        app.register_blueprint(admin_portal)
        print("✅ Admin portal registered")
    except ImportError:
        print("⚠️ Admin portal not yet installed")

    return app
''')

    # 6. Create basic models
    create_file(
        "src/core/models.py", '''"""
Database models for VectorBid
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    name = db.Column(db.String(100))
    airline = db.Column(db.String(50))
    base = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime)

class BidPacket(db.Model):
    __tablename__ = 'bid_packets'

    id = db.Column(db.Integer, primary_key=True)
    month_tag = db.Column(db.String(6), unique=True)
    filename = db.Column(db.String(255))
    file_data = db.Column(db.LargeBinary)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

class BidAnalysis(db.Model):
    __tablename__ = 'bid_analyses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'))
    preferences = db.Column(db.Text)
    commands = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
''')

    # 7. Create extensions
    create_file(
        "src/core/extensions.py", '''"""
Flask extensions
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
''')

    # 8. Create main.py
    create_file(
        "main.py", '''"""
Main entry point for VectorBid
"""

from src.core.app import create_app
import os

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
''')

    # 9. Create basic templates
    create_file(
        "src/ui/templates/index.html", '''<!DOCTYPE html>
<html>
<head>
    <title>VectorBid - AI Pilot Bidding Assistant</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            <span class="navbar-brand">✈️ VectorBid</span>
        </div>
    </nav>

    <div class="container mt-5">
        <div class="row">
            <div class="col-md-8 offset-md-2">
                <h1>Welcome to VectorBid</h1>
                <p class="lead">Your AI-powered pilot schedule bidding assistant</p>

                <div class="card mt-4">
                    <div class="card-body">
                        <h5>Quick PBS Generation</h5>
                        <form action="/pbs-results" method="get">
                            <div class="mb-3">
                                <label class="form-label">Enter your preferences:</label>
                                <textarea name="preferences" class="form-control" rows="4" 
                                    placeholder="I want weekends off and prefer short trips..."></textarea>
                            </div>
                            <button type="submit" class="btn btn-primary">Generate PBS Commands</button>
                        </form>
                    </div>
                </div>

                <div class="mt-4">
                    <a href="/admin/" class="btn btn-secondary">Admin Portal</a>
                </div>
            </div>
        </div>
    </div>
</body>
</html>''')

    create_file(
        "src/ui/templates/pbs_results.html", '''<!DOCTYPE html>
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
        <h2>Your PBS Commands</h2>
        <p>Based on: {{ preferences }}</p>

        <div class="card mt-4">
            <div class="card-header">Generated Commands</div>
            <div class="card-body">
                <pre>{{ formatted }}</pre>

                {% if commands %}
                <h5 class="mt-4">Commands Breakdown:</h5>
                <ul>
                {% for cmd in commands %}
                    <li>
                        <strong>{{ cmd.command }}</strong><br>
                        <small class="text-muted">{{ cmd.explanation }}</small>
                    </li>
                {% endfor %}
                </ul>
                {% endif %}
            </div>
        </div>

        <a href="/" class="btn btn-secondary mt-3">Back to Home</a>
    </div>
</body>
</html>''')

    # 10. Create requirements.txt
    create_file(
        "requirements.txt", '''Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-Login==0.6.2
python-dotenv==1.0.0
gunicorn==21.2.0
''')

    print("\n" + "=" * 60)
    print("✅ SETUP COMPLETE!")
    print("=" * 60)

    print("\n📋 Next Steps:\n")
    print("1. Install dependencies:")
    print("   pip install -r requirements.txt\n")

    print("2. Run the application:")
    print("   python main.py\n")

    print("3. Access VectorBid:")
    print("   http://localhost:5000\n")

    print("4. Test PBS generation:")
    print("   Enter preferences and click 'Generate PBS Commands'\n")

    print("Note: This is a simplified version to get you started.")
    print("The full features (admin portal, analytics, etc.) can be")
    print("added incrementally as separate files.\n")


if __name__ == "__main__":
    main()
