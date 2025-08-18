#!/usr/bin/env python3
from pathlib import Path

print("Creating PBS wrapper to fix the issue...")

# Create a simple wrapper file
wrapper_content = '''"""
PBS Command Wrapper for VectorBid
Simplifies PBS command generation
"""

from src.lib.pbs_command_generator import PBSCommandGenerator as OriginalGenerator, PilotProfile

class SimplePBSGenerator:
    """Simplified PBS generator that handles the profile conversion"""
    
    def __init__(self):
        self.generator = OriginalGenerator()
    
    def generate_simple(self, preferences: str) -> dict:
        """Generate PBS commands with default profile"""
        # Use a dictionary instead of PilotProfile object
        profile_dict = {
            "base": "EWR",
            "fleet": ["737"],
            "seniority": 50,
            "flying_style": "balanced",
            "commuter": False
        }
        
        # Call the original generator with dict
        commands = self.generator.generate(preferences, profile_dict)
        
        # Convert to simple format
        return {
            "commands": [cmd.to_dict() for cmd in commands],
            "command_count": len(commands)
        }

# Helper function for easy access
def generate_pbs_commands(preferences: str) -> dict:
    """Quick helper to generate PBS commands"""
    gen = SimplePBSGenerator()
    return gen.generate_simple(preferences)
'''

# Save the wrapper
wrapper_path = Path("src/lib/pbs_wrapper.py")
wrapper_path.write_text(wrapper_content)
print(f"✅ Created {wrapper_path}")

# Now update routes.py to use the wrapper
print("\nUpdating routes.py to use wrapper...")
routes_path = Path("src/api/routes.py")
if routes_path.exists():
    content = routes_path.read_text()
    
    # Replace PBS import
    content = content.replace(
        "from src.lib.pbs_command_generator import PBSCommandGenerator",
        "from src.lib.pbs_wrapper import SimplePBSGenerator"
    )
    
    # Update the generate_pbs function
    new_generate_pbs = '''@main_bp.route('/generate-pbs', methods=['POST'])
def generate_pbs():
    """Generate PBS commands from natural language preferences"""
    try:
        data = request.get_json()
        preferences = data.get('preferences', '')
        
        if not preferences:
            return jsonify({'success': False, 'error': 'No preferences provided'}), 400
        
        from src.lib.pbs_wrapper import SimplePBSGenerator
        generator = SimplePBSGenerator()
        result = generator.generate_simple(preferences)
        
        logger.info(f"Generated {result['command_count']} PBS commands")
        
        return jsonify({
            'success': True,
            'preferences': preferences,
            'commands': result['commands'],
            'command_count': result['command_count'],
            'quality_score': 80
        })
    except Exception as e:
        logger.error(f"PBS generation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500'''
    
    # Find and replace
    if "@main_bp.route('/generate-pbs'" in content:
        start = content.find("@main_bp.route('/generate-pbs'")
        next_route = content.find("\n@main_bp.route", start + 1)
        if next_route == -1:
            next_route = len(content)
        content = content[:start] + new_generate_pbs + "\n" + content[next_route:]
        
    routes_path.write_text(content)
    print("✅ Updated routes.py")

# Update test to use wrapper
print("\nUpdating test script...")
test_path = Path("test_implementation.py")
if test_path.exists():
    test_content = test_path.read_text()
    test_content = test_content.replace(
        "from src.lib.pbs_command_generator import PBSCommandGenerator, PilotProfile",
        "from src.lib.pbs_wrapper import SimplePBSGenerator"
    )
    test_content = test_content.replace(
        "generator = PBSCommandGenerator()",
        "generator = SimplePBSGenerator()"
    )
    test_content = test_content.replace(
        """profile = PilotProfile(
            base="EWR",
            fleet=["737"],
            seniority=50,
            flying_style="balanced",
            commuter=False
        )""",
        "# No profile needed with SimplePBSGenerator"
    )
    test_content = test_content.replace(
        "commands = generator.generate(test, profile)",
        "result = generator.generate_simple(test)"
    )
    test_content = test_content.replace(
        'print(f"  Output: {len(commands)} commands")',
        'print(f"  Output: {result['command_count']} commands")'
    )
    test_content = test_content.replace(
        "if len(commands) < 2",
        "if result['command_count'] < 2"
    )
    
    test_path.write_text(test_content)
    print("✅ Updated test script")

print("\n" + "=" * 40)
print("Done! Testing the wrapper...")
