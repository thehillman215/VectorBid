

# ============== FIXED PBS GENERATION ==============
def get_dashboard_stats():
    """Get statistics for dashboard display"""
    return {
        'trips_count': 142,  # TODO: Get from database
        'match_score': 85,
        'days_off': 12,
        'block_hours': 72.5,
        'trips_trend': {
            'direction': 'up',
            'value': 12
        }
    }


"""
Enhanced routes with conflict resolution
"""

from flask import (
    Blueprint,
    jsonify,
    redirect,
    render_template,
    render_template_string,
    request,
    session,
    url_for,
)

from src.lib.pbs_20_layer_system import generate_pbs_compliant_bid_layers
from src.lib.pbs_command_generator import generate_pbs_commands
from src.lib.personas import PILOT_PERSONAS
from src.lib.services.db import get_profile, save_profile
from src.lib.subscription_manager import SubscriptionManager

try:
    from src.lib.pbs_enhanced import generate_advanced_pbs_strategy
except ImportError:
    generate_advanced_pbs_strategy = None

from datetime import datetime

# Fixed PBS generation functions

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    """Main dashboard - redirect to enhanced dashboard or show basic version"""
    user_id = session.get('user_id', 'demo_pilot')
    profile = get_profile(user_id)

    # If user has completed profile, show enhanced dashboard
    if profile.get('onboard_complete') or profile.get('airline'):
        return redirect(url_for('main.enhanced_dashboard'))

    # Get subscription info
    manager = SubscriptionManager()
    subscription = manager.get_user_subscription(user_id)

    # Use the proper template file instead of inline HTML
    try:
        return render_template("index.html",
                               subscription=subscription,
                               user_id=user_id,
                               profile=profile)
    except:
        # Fallback to simple HTML if template not found
        return f"""
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
                        <span class="badge bg-success">{subscription.get('tier', 'Free') if subscription else 'Free'}</span>
                        <a href="/admin/" class="btn btn-outline-light btn-sm ms-2">Admin</a>
                    </div>
                </div>
            </nav>
            <div class="container mt-5">
                <div class="row">
                    <div class="col-md-8 offset-md-2">
                        <h1>Welcome to VectorBid</h1>
                        <p class="lead">Your AI-powered pilot schedule bidding assistant</p>
                        <div class="card mt-4">
                            <div class="card-body">
                                <h5>Generate PBS Commands</h5>
                                <form action="/process" method="post">
                                    <div class="mb-3">
                                        <label class="form-label">Enter your preferences:</label>
                                        <textarea name="preferences" class="form-control" rows="4" 
                                            placeholder="I want weekends off and prefer short trips..."></textarea>
                                    </div>
                                    <button type="submit" class="btn btn-primary">Generate PBS Commands</button>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """


@bp.route("/process", methods=["POST", "GET"])
def process():
    """Handle preference submission and redirect to appropriate page.

    When called via POST, the submitted preferences are appended to the
    query string and the user is redirected to the PBS results page. For
    any other request method, the user is sent back to the index page.
    """
    if request.method == "POST":
        preferences = request.form.get('preferences', '')
        return redirect(url_for('main.pbs_results', preferences=preferences))
    else:
        return redirect(url_for('main.index'))


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
        try:
            result = generate_pbs_commands(preferences)
            return render_template("pbs_results.html",
                                   commands=result.get('commands', []),
                                   formatted=result.get('formatted', ''),
                                   preferences=preferences)
        except Exception as e:
            # Fallback if PBS generator fails - show actual error for debugging
            return f"""
            <h1>PBS Results</h1>
            <p>Preferences: {preferences}</p>
            <div class="alert alert-warning">
                PBS command generation error: {str(e)}
            </div>
            <a href="/" class="btn btn-primary">Back to Dashboard</a>
            """


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
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

@bp.route('/admin')
def admin_redirect():
    """Redirect to admin dashboard"""
    return redirect('/admin/dashboard')

@bp.route('/onboarding')
def onboarding():
    """Pilot profile onboarding wizard"""
    return render_template('onboarding.html', step=1)

@bp.route('/onboarding/submit', methods=['POST'])
def onboarding_submit():
    """Handle onboarding form submission"""
    try:
        # Collect pilot profile data
        profile_data = {
            'airline': request.form.get('airline', ''),
            'base': request.form.get('base', ''),
            'seat': request.form.get('seat', ''),
            'fleet': request.form.get('fleet', '').split(',') if request.form.get('fleet') else [],
            'seniority': int(request.form.get('seniority', 5000)),
            'onboarded': True
        }

        # Save profile (using demo user ID for now)
        user_id = "demo_pilot"
        save_profile(user_id, profile_data)

        # Redirect to personas page
        return redirect(url_for('main.personas'))

    except Exception as e:
        return f"Error saving profile: {str(e)}", 400

@bp.route('/personas')
def personas():
    """Display available pilot personas after onboarding"""
    # Check if pilot has completed profile (simplified for demo)
    user_id = "demo_pilot"
    profile = get_profile(user_id)

    if not profile.get('onboarded'):
        return redirect(url_for('main.onboarding'))
    personas_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Pilot Personas - VectorBid</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="/static/css/vectorbid-modern.css" rel="stylesheet">
</head>
<body>
    <nav class="vb-nav">
        <div class="vb-nav-container">
            <a href="/" class="vb-logo">
                <div class="vb-logo-icon"><i class="fas fa-plane"></i></div>
                VectorBid
            </a>
            <div class="vb-nav-links">
                <a href="/" class="vb-nav-link">Home</a>
                <a href="/personas" class="vb-nav-link active">Personas</a>
                <a href="/admin" class="vb-nav-link">Admin</a>
            </div>
        </div>
    </nav>

    <div class="vb-container">
        <div class="vb-hero">
            <h1 class="vb-hero-title">Choose Your Flying Style</h1>
            <p class="vb-hero-subtitle">Pre-built personas for {{ profile.get('airline', 'Pilot') }} {{ profile.get('seat', 'pilot') }}</p>
        </div>

        <div class="row">
            {% for persona_id, persona in personas.items() %}
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="vb-card">
                    <div class="vb-card-header">
                        <h3 class="vb-card-title">
                            <i class="{{ persona.icon }}"></i>
                            {{ persona.name }}
                        </h3>
                        <p class="vb-card-subtitle">{{ persona.description }}</p>
                    </div>
                    <div class="card-body">
                        <p><strong>Preferences:</strong></p>
                        <p class="text-muted">{{ persona.preferences[:100] }}...</p>
                        <form action="/bid-layers/generate" method="POST" class="mt-3">
                            <input type="hidden" name="persona" value="{{ persona_id }}">
                            <button type="submit" class="vb-btn vb-btn-primary">
                                <i class="fas fa-magic"></i>
                                Use This Persona
                            </button>
                        </form>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
    """
    return render_template_string(personas_html, personas=PILOT_PERSONAS, profile=profile)

@bp.route('/bid-layers/generate', methods=['POST'])
def generate_bid_layers():
    """Generate 20-layer PBS bid strategy with pilot profile and persona"""
    preferences = request.form.get('preferences', '')
    persona_id = request.form.get('persona', '')

    # Get pilot profile
    user_id = "demo_pilot"
    profile = get_profile(user_id)

    # Use persona if selected
    persona = None
    if persona_id and persona_id in PILOT_PERSONAS:
        persona = PILOT_PERSONAS[persona_id]
        preferences = persona['preferences']

    # Generate full 20-layer PBS bid strategy
    bid_layers = generate_pbs_compliant_bid_layers(preferences, profile)

    results_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Persona PBS Results - VectorBid</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="/static/css/vectorbid-modern.css" rel="stylesheet">
</head>
<body>
    <nav class="vb-nav">
        <div class="vb-nav-container">
            <a href="/" class="vb-logo">
                <div class="vb-logo-icon"><i class="fas fa-plane"></i></div>
                VectorBid
            </a>
            <div class="vb-nav-links">
                <a href="/" class="vb-nav-link">Home</a>
                <a href="/personas" class="vb-nav-link">Personas</a>
                <a href="/admin" class="vb-nav-link">Admin</a>
            </div>
        </div>
    </nav>

    <div class="vb-container">
        {% if persona %}
        <div class="vb-hero">
            <h1 class="vb-hero-title">
                <i class="{{ persona.icon }}"></i>
                {{ persona.name }} Results
            </h1>
            <p class="vb-hero-subtitle">{{ persona.description }}</p>
        </div>
        {% endif %}

        <div class="vb-card">
            <div class="vb-card-header">
                <h2 class="vb-card-title">Your PBS Commands</h2>
                <p class="vb-card-subtitle">Based on: {{ preferences }}</p>
            </div>

            <div class="card-body">
                <div class="alert alert-info mb-4">
                    <h6><i class="fas fa-user-pilot"></i> Pilot Profile</h6>
                    <p><strong>{{ profile.airline }}</strong> {{ profile.seat }} | Base: {{ profile.base }} | Fleet: {{ profile.fleet|join(', ') }} | Seniority: {{ profile.seniority }}</p>
                </div>

                <h5 class="mt-4">20-Layer PBS Bid Strategy:</h5>
                <div class="accordion" id="layersAccordion">
                {% for layer in bid_layers %}
                    <div class="accordion-item">
                        <h2 class="accordion-header" id="heading{{ layer.layer }}">
                            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse{{ layer.layer }}">
                                <strong>Layer {{ layer.layer }}: {{ layer.description }}</strong>
                                <span class="badge bg-{{ 'success' if layer.category == 'IDEAL' else 'primary' if layer.category == 'GOOD' else 'warning' if layer.category == 'ACCEPTABLE' else 'secondary' }} ms-2">{{ layer.probability }}</span>
                            </button>
                        </h2>
                        <div id="collapse{{ layer.layer }}" class="accordion-collapse collapse" data-bs-parent="#layersAccordion">
                            <div class="accordion-body">
                                <p><strong>Strategy:</strong> {{ layer.strategy }}</p>
                                <p><strong>PBS Filters:</strong></p>
                                <ul>
                                {% for filter in layer.filters %}
                                    <li><code>{{ filter }}</code></li>
                                {% endfor %}
                                </ul>
                            </div>
                        </div>
                    </div>
                {% endfor %}
                </div>

                <h5 class="mt-4">Complete PBS Command Block:</h5>
                <pre class="bg-light p-3 rounded">{% for layer in bid_layers %}
# LAYER {{ layer.layer }}: {{ layer.description }} ({{ layer.probability }})
{% for filter in layer.filters %}{{ filter }}
{% endfor %}

{% endfor %}</pre>
            </div>

            <div class="mt-3">
                <a href="/personas" class="vb-btn vb-btn-secondary">Try Another Persona</a>
                <button class="vb-btn vb-btn-primary" onclick="copyCommands()">
                    <i class="fas fa-copy"></i>
                    Copy Commands
                </button>
            </div>
        </div>
    </div>

    <!-- Bootstrap JavaScript (must be loaded after DOM elements) -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    
    <script>
        function copyCommands() {
            const commands = document.querySelector('pre').textContent;
            navigator.clipboard.writeText(commands);
            alert('Commands copied to clipboard!');
        }
        
        // Initialize Bootstrap components after DOM is loaded
        document.addEventListener('DOMContentLoaded', function() {
            console.log('DOM loaded, initializing Bootstrap accordion...');
            // Ensure Bootstrap is available
            if (typeof bootstrap !== 'undefined') {
                console.log('Bootstrap is loaded');
            } else {
                console.error('Bootstrap is not loaded!');
            }
        });
    </script>
</body>
</html>
    """

    return render_template_string(results_html,
                                 preferences=preferences,
                                 bid_layers=bid_layers,
                                 profile=profile,
                                 persona=persona)


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


# Add missing routes for navigation
@bp.route("/preferences")
def preferences():
    return "Preferences page under development. <a href=\"/\">Back to Dashboard</a>"


@bp.route("/schedule")
def schedule():
    return "Schedule page under development. <a href=\"/\">Back to Dashboard</a>"


@bp.route("/history")
def history():
    return "History page under development. <a href=\"/\">Back to Dashboard</a>"


@bp.route("/profile")
def user_profile():
    """Enhanced user profile page"""
    user_id = session.get('user_id', 'demo_pilot')
    profile = get_profile(user_id)

    return render_template("user_profile.html",
                         profile=profile,
                         personas=PILOT_PERSONAS)


@bp.route("/dashboard")
def enhanced_dashboard():
    """Enhanced dashboard with metrics and personalized content"""
    user_id = session.get('user_id', 'demo_pilot')
    profile = get_profile(user_id)

    # Get dashboard statistics
    stats = get_dashboard_stats()

    # Get current month for bid period display
    from datetime import datetime
    current_month = datetime.now().strftime("%B %Y")

    # Add persona name to profile for display
    if profile.get('persona'):
        profile['persona_name'] = PILOT_PERSONAS.get(profile['persona'], {}).get('name', 'Custom')

    return render_template("enhanced_dashboard.html",
                         profile=profile,
                         stats=stats,
                         personas=PILOT_PERSONAS,
                         current_month=current_month)


@bp.route("/api/dashboard-stats")
def api_dashboard_stats():
    """API endpoint for dashboard statistics"""
    stats = get_dashboard_stats()
    return jsonify(stats)


@bp.route("/preferences/advanced")
def advanced_preferences():
    """Advanced preferences management page"""
    user_id = session.get('user_id', 'demo_pilot')

    # Import preferences manager
    from src.lib.preferences_manager import preferences_manager

    # Get user preferences and analysis
    profile = get_profile(user_id)
    report = preferences_manager.generate_preference_report(user_id)
    suggestions = preferences_manager.get_smart_suggestions(user_id)

    # Get current persona if selected
    current_persona = None
    if profile.get('persona'):
        current_persona = PILOT_PERSONAS.get(profile['persona'])

    return render_template("preferences_advanced.html",
                         profile=profile,
                         optimization_score=report['optimization_score'],
                         suggestions=suggestions,
                         learning_data=report.get('learning_data', {}),
                         current_persona=current_persona)


@bp.route("/api/preferences/advanced", methods=["POST"])
def api_save_advanced_preferences():
    """Save advanced preferences via API"""
    try:
        user_id = session.get('user_id', 'demo_pilot')
        data = request.get_json()

        # Import preferences manager
        from src.lib.preferences_manager import preferences_manager

        # Save preferences using preferences manager
        success = preferences_manager.update_preferences(user_id, data)

        if success:
            return jsonify({'success': True, 'message': 'Preferences saved successfully'})
        else:
            return jsonify({'success': False, 'message': 'Error saving preferences'}), 500

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
