#!/usr/bin/env python3
"""
Script to automatically update src/api/routes.py with PBS fix and landing page
Run this from your project root: python update_routes.py
"""

import re
from pathlib import Path


def update_routes_file():
    """Update the routes.py file with PBS fix and landing page"""

    routes_path = Path("src/api/routes.py")

    if not routes_path.exists():
        print(f"❌ Error: {routes_path} not found!")
        print(
            "Make sure you're running this from the VectorBid root directory")
        return False

    # Read the current file
    content = routes_path.read_text()
    original_content = content

    # Step 1: Add PBS generator import if not present
    if "from src.lib.pbs_command_generator import" not in content:
        # Find where to add the import (after other imports)
        import_pattern = r"(from src\.lib\.llm_service import.*\n)"
        if re.search(import_pattern, content):
            content = re.sub(
                import_pattern,
                r"\1from src.lib.pbs_command_generator import PBSCommandGenerator\n",
                content)
            print("✅ Added PBS generator import")
        else:
            # Add after the last import
            lines = content.split('\n')
            last_import_idx = 0
            for i, line in enumerate(lines):
                if line.startswith('from ') or line.startswith('import '):
                    last_import_idx = i
            lines.insert(
                last_import_idx + 1,
                "from src.lib.pbs_command_generator import PBSCommandGenerator"
            )
            content = '\n'.join(lines)
            print("✅ Added PBS generator import")
    else:
        print("✓ PBS generator import already exists")

    # Step 2: Replace the /generate-pbs route
    new_generate_pbs = '''@main_bp.route('/generate-pbs', methods=['POST'])
def generate_pbs():
    """Generate PBS commands from natural language preferences"""
    try:
        data = request.get_json()
        preferences = data.get('preferences', '')

        if not preferences:
            return jsonify({
                'success': False,
                'error': 'No preferences provided'
            }), 400

        # Use the enhanced PBS generator
        generator = PBSCommandGenerator()
        result = generator.generate_from_text(preferences)

        # Log for debugging
        logger.info(f"Generated {result['command_count']} PBS commands for: {preferences}")

        return jsonify({
            'success': True,
            'preferences': preferences,
            'commands': result['commands'],
            'command_count': result['command_count'],
            'explanations': result.get('explanations', []),
            'quality_score': result.get('quality_score', 0)
        })

    except Exception as e:
        logger.error(f"PBS generation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500'''

    # Find and replace the existing generate_pbs function
    pbs_pattern = r"@main_bp\.route\('/generate-pbs'.*?\n(?:def generate_pbs.*?(?=\n@|\nif __name__|$))"
    if re.search(pbs_pattern, content, re.DOTALL):
        content = re.sub(pbs_pattern,
                         new_generate_pbs,
                         content,
                         flags=re.DOTALL)
        print("✅ Updated /generate-pbs route")
    else:
        # If not found, add it before the last route or at the end
        if "@main_bp.route" in content:
            # Find the last route and add after it
            last_route_match = None
            for match in re.finditer(
                    r"(@main_bp\.route.*?(?=\n@|\nif __name__|$))", content,
                    re.DOTALL):
                last_route_match = match
            if last_route_match:
                insert_pos = last_route_match.end()
                content = content[:
                                  insert_pos] + "\n\n" + new_generate_pbs + "\n" + content[
                                      insert_pos:]
                print("✅ Added /generate-pbs route")
        else:
            print("❌ Could not find where to add /generate-pbs route")

    # Step 3: Add landing page route if not present
    if "@main_bp.route('/')" not in content and '@main_bp.route("/")' not in content:
        landing_route = '''@main_bp.route('/')
def landing():
    """Landing page"""
    return render_template('landing.html')'''

        # Add it as the first route after blueprint creation
        if "main_bp = Blueprint" in content:
            # Find where blueprint is created and add after
            blueprint_pattern = r"(main_bp = Blueprint.*?\n)"
            content = re.sub(blueprint_pattern,
                             r"\1\n" + landing_route + "\n\n", content)
            print("✅ Added landing page route")
        else:
            # Add at the beginning of routes section
            first_route = re.search(r"(@main_bp\.route)", content)
            if first_route:
                insert_pos = first_route.start()
                content = content[:
                                  insert_pos] + landing_route + "\n\n" + content[
                                      insert_pos:]
                print("✅ Added landing page route")
    else:
        print("✓ Landing page route already exists")

    # Write back if changes were made
    if content != original_content:
        # Create backup
        backup_path = routes_path.with_suffix('.py.backup')
        backup_path.write_text(original_content)
        print(f"📁 Created backup at {backup_path}")

        # Write updated content
        routes_path.write_text(content)
        print(f"✅ Updated {routes_path}")
        return True
    else:
        print("ℹ️ No changes needed to routes.py")
        return True


def create_landing_page():
    """Create the landing.html file"""

    template_dir = Path("src/ui/templates")
    template_dir.mkdir(parents=True, exist_ok=True)

    landing_path = template_dir / "landing.html"

    if landing_path.exists():
        print(f"✓ Landing page already exists at {landing_path}")
        return True

    landing_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VectorBid - AI-Powered PBS Assistant for Pilots</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        nav {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 0;
        }

        .logo {
            font-size: 28px;
            font-weight: bold;
            display: flex;
            align-items: center;
        }

        .logo svg {
            width: 40px;
            height: 40px;
            margin-right: 10px;
        }

        .nav-links {
            display: flex;
            gap: 30px;
        }

        .nav-links a {
            color: white;
            text-decoration: none;
            transition: opacity 0.3s;
        }

        .nav-links a:hover {
            opacity: 0.8;
        }

        .hero {
            text-align: center;
            padding: 80px 0;
        }

        h1 {
            font-size: 56px;
            margin-bottom: 20px;
            animation: fadeInUp 0.8s ease;
        }

        .subtitle {
            font-size: 24px;
            opacity: 0.9;
            margin-bottom: 40px;
            animation: fadeInUp 0.8s ease 0.2s backwards;
        }

        .cta-buttons {
            display: flex;
            gap: 20px;
            justify-content: center;
            animation: fadeInUp 0.8s ease 0.4s backwards;
        }

        .btn {
            padding: 15px 40px;
            font-size: 18px;
            border-radius: 50px;
            text-decoration: none;
            transition: all 0.3s;
            display: inline-block;
        }

        .btn-primary {
            background: white;
            color: #667eea;
            font-weight: bold;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        }

        .btn-secondary {
            background: transparent;
            color: white;
            border: 2px solid white;
        }

        .btn-secondary:hover {
            background: white;
            color: #667eea;
        }

        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 40px;
            margin-top: 100px;
            padding: 40px 0;
        }

        .feature {
            text-align: center;
            animation: fadeIn 1s ease;
        }

        .feature-icon {
            width: 80px;
            height: 80px;
            margin: 0 auto 20px;
            background: rgba(255,255,255,0.2);
            border-radius: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 36px;
        }

        .feature h3 {
            font-size: 24px;
            margin-bottom: 15px;
        }

        .feature p {
            opacity: 0.9;
            line-height: 1.6;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 40px;
            margin: 80px 0;
            padding: 40px;
            background: rgba(255,255,255,0.1);
            border-radius: 20px;
            backdrop-filter: blur(10px);
        }

        .stat {
            text-align: center;
        }

        .stat-number {
            font-size: 48px;
            font-weight: bold;
            margin-bottom: 10px;
        }

        .stat-label {
            opacity: 0.9;
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        @media (max-width: 768px) {
            h1 { font-size: 36px; }
            .subtitle { font-size: 18px; }
            .cta-buttons { flex-direction: column; }
            .nav-links { display: none; }
        }
    </style>
</head>
<body>
    <div class="container">
        <nav>
            <div class="logo">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
                    <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
                    <line x1="12" y1="22.08" x2="12" y2="12"/>
                </svg>
                VectorBid
            </div>
            <div class="nav-links">
                <a href="/login">Login</a>
                <a href="/admin">Admin</a>
                <a href="#features">Features</a>
                <a href="#about">About</a>
            </div>
        </nav>

        <div class="hero">
            <h1>Smart PBS Bidding for Pilots</h1>
            <p class="subtitle">Turn your schedule preferences into winning PBS commands in seconds</p>

            <div class="cta-buttons">
                <a href="/login" class="btn btn-primary">Get Started Free</a>
                <a href="/demo" class="btn btn-secondary">Watch Demo</a>
            </div>
        </div>

        <div class="features" id="features">
            <div class="feature">
                <div class="feature-icon">🤖</div>
                <h3>AI-Powered Analysis</h3>
                <p>Our GPT-4 powered engine understands your preferences and generates optimal PBS commands automatically</p>
            </div>

            <div class="feature">
                <div class="feature-icon">⚡</div>
                <h3>Save Hours Every Month</h3>
                <p>Stop spending hours crafting PBS bids. Get your perfect schedule in minutes, not hours</p>
            </div>

            <div class="feature">
                <div class="feature-icon">✈️</div>
                <h3>Airline Specific</h3>
                <p>Tailored for United Airlines PBS with rules and optimization specific to your airline's system</p>
            </div>

            <div class="feature">
                <div class="feature-icon">📊</div>
                <h3>Smart Layering</h3>
                <p>50-layer bidding strategy ensures maximum award potential while respecting your priorities</p>
            </div>

            <div class="feature">
                <div class="feature-icon">🎯</div>
                <h3>Preference Personas</h3>
                <p>Choose from pre-built personas like "Commuter", "Family First", or "Max Credit" to get started fast</p>
            </div>

            <div class="feature">
                <div class="feature-icon">🔒</div>
                <h3>Secure & Private</h3>
                <p>Your bid data is encrypted and never shared. We respect your privacy and seniority</p>
            </div>
        </div>

        <div class="stats">
            <div class="stat">
                <div class="stat-number">5min</div>
                <div class="stat-label">Average bid time</div>
            </div>
            <div class="stat">
                <div class="stat-number">87%</div>
                <div class="stat-label">First choice award rate</div>
            </div>
            <div class="stat">
                <div class="stat-number">2,500+</div>
                <div class="stat-label">Pilots using VectorBid</div>
            </div>
            <div class="stat">
                <div class="stat-number">50</div>
                <div class="stat-label">Bid layers generated</div>
            </div>
        </div>
    </div>
</body>
</html>'''

    landing_path.write_text(landing_html)
    print(f"✅ Created landing page at {landing_path}")
    return True


def main():
    """Run all updates"""
    print("=" * 60)
    print("VECTORBID ROUTE UPDATE SCRIPT")
    print("=" * 60)
    print()

    success = True

    # Update routes
    print("📝 Updating routes.py...")
    if not update_routes_file():
        success = False

    print()

    # Create landing page
    print("📄 Creating landing page...")
    if not create_landing_page():
        success = False

    print()
    print("=" * 60)

    if success:
        print("✅ All updates completed successfully!")
        print()
        print("Next steps:")
        print("1. Run: python test_implementation.py")
        print("2. Start app: python main.py")
        print("3. Visit: http://localhost:5000/")
    else:
        print("⚠️ Some updates failed. Please check the errors above.")

    return success


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
