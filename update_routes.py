#!/usr/bin/env python3
"""
Script to automatically update src/api/routes.py with PBS fix and landing page
"""

import re
from pathlib import Path

def update_routes_file():
    routes_path = Path("src/api/routes.py")
    
    if not routes_path.exists():
        print(f"Error: {routes_path} not found!")
        return False
    
    content = routes_path.read_text()
    original_content = content
    
    # Add PBS generator import
    if "from src.lib.pbs_command_generator import" not in content:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if "from src.lib.llm_service import" in line:
                lines.insert(i + 1, "from src.lib.pbs_command_generator import PBSCommandGenerator")
                break
        content = '\n'.join(lines)
        print("Added PBS generator import")
    
    # Replace generate_pbs function
    new_pbs = '''@main_bp.route('/generate-pbs', methods=['POST'])
def generate_pbs():
    """Generate PBS commands from natural language preferences"""
    try:
        data = request.get_json()
        preferences = data.get('preferences', '')
        
        if not preferences:
            return jsonify({'success': False, 'error': 'No preferences provided'}), 400
        
        generator = PBSCommandGenerator()
        result = generator.generate_from_text(preferences)
        
        logger.info(f"Generated {result['command_count']} PBS commands")
        
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
        return jsonify({'success': False, 'error': str(e)}), 500'''
    
    # Find and replace existing generate_pbs
    if "@main_bp.route('/generate-pbs'" in content:
        start = content.find("@main_bp.route('/generate-pbs'")
        end = content.find("\n@main_bp.route", start + 1)
        if end == -1:
            end = len(content)
        content = content[:start] + new_pbs + content[end:]
        print("Updated /generate-pbs route")
    
    # Add landing route
    if "@main_bp.route('/')" not in content:
        landing = '''@main_bp.route('/')
def landing():
    """Landing page"""
    return render_template('landing.html')

'''
        # Add after blueprint creation
        bp_pos = content.find("main_bp = Blueprint")
        if bp_pos != -1:
            insert_pos = content.find('\n', bp_pos) + 1
            content = content[:insert_pos] + '\n' + landing + content[insert_pos:]
            print("Added landing page route")
    
    if content != original_content:
        routes_path.write_text(content)
        print(f"Updated {routes_path}")
        return True
    return True

def create_landing_page():
    template_dir = Path("src/ui/templates")
    template_dir.mkdir(parents=True, exist_ok=True)
    landing_path = template_dir / "landing.html"
    
    if landing_path.exists():
        print(f"Landing page already exists")
        return True
    
    landing_path.write_text('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VectorBid - AI-Powered PBS Assistant</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        nav { display: flex; justify-content: space-between; align-items: center; padding: 20px 0; }
        .logo { font-size: 28px; font-weight: bold; }
        .nav-links { display: flex; gap: 30px; }
        .nav-links a { color: white; text-decoration: none; }
        .hero { text-align: center; padding: 80px 0; }
        h1 { font-size: 56px; margin-bottom: 20px; }
        .subtitle { font-size: 24px; opacity: 0.9; margin-bottom: 40px; }
        .cta-buttons { display: flex; gap: 20px; justify-content: center; }
        .btn {
            padding: 15px 40px;
            font-size: 18px;
            border-radius: 50px;
            text-decoration: none;
            display: inline-block;
        }
        .btn-primary { background: white; color: #667eea; font-weight: bold; }
        .btn-secondary { background: transparent; color: white; border: 2px solid white; }
        .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 40px; margin-top: 100px; }
        .feature { text-align: center; }
        .feature-icon { font-size: 36px; margin-bottom: 20px; }
        .feature h3 { font-size: 24px; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <nav>
            <div class="logo">VectorBid</div>
            <div class="nav-links">
                <a href="/login">Login</a>
                <a href="/admin">Admin</a>
            </div>
        </nav>
        <div class="hero">
            <h1>Smart PBS Bidding for Pilots</h1>
            <p class="subtitle">Turn your schedule preferences into winning PBS commands in seconds</p>
            <div class="cta-buttons">
                <a href="/login" class="btn btn-primary">Get Started</a>
                <a href="/admin" class="btn btn-secondary">Admin Portal</a>
            </div>
        </div>
        <div class="features">
            <div class="feature">
                <div class="feature-icon">🤖</div>
                <h3>AI-Powered</h3>
                <p>GPT-4 analyzes your preferences and generates optimal PBS commands</p>
            </div>
            <div class="feature">
                <div class="feature-icon">⚡</div>
                <h3>Save Time</h3>
                <p>Get your perfect schedule in minutes, not hours</p>
            </div>
            <div class="feature">
                <div class="feature-icon">✈️</div>
                <h3>Airline Specific</h3>
                <p>Tailored for United Airlines PBS system</p>
            </div>
        </div>
    </div>
</body>
</html>''')
    print(f"Created landing page")
    return True

if __name__ == "__main__":
    print("VECTORBID UPDATE SCRIPT")
    print("=" * 40)
    update_routes_file()
    create_landing_page()
    print("=" * 40)
    print("Done! Run: python test_implementation.py")
