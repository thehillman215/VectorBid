"""
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
