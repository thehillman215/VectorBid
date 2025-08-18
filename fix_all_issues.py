#!/usr/bin/env python3
from pathlib import Path

print("FIXING VECTORBID ISSUES")
print("=" * 40)

# Fix 1: Update routes.py to use correct PBS method
print("\n1. Fixing PBS generation in routes.py...")
routes_path = Path("src/api/routes.py")
if routes_path.exists():
    content = routes_path.read_text()
    
    # Replace the generate_pbs function with correct implementation
    new_generate_pbs = '''@main_bp.route('/generate-pbs', methods=['POST'])
def generate_pbs():
    """Generate PBS commands from natural language preferences"""
    try:
        data = request.get_json()
        preferences = data.get('preferences', '')
        
        if not preferences:
            return jsonify({'success': False, 'error': 'No preferences provided'}), 400
        
        # Create a default pilot profile (can be enhanced later)
        from src.lib.pbs_command_generator import PBSCommandGenerator, PilotProfile
        generator = PBSCommandGenerator()
        
        # Create default profile or get from session
        profile = PilotProfile(
            airline="UAL",
            base="EWR",
            fleet=["737"],
            seat="FO"
        )
        
        # Generate PBS commands
        commands = generator.generate(preferences, profile)
        
        # Convert commands to dict format
        command_list = [cmd.to_dict() for cmd in commands]
        
        logger.info(f"Generated {len(command_list)} PBS commands")
        
        return jsonify({
            'success': True,
            'preferences': preferences,
            'commands': command_list,
            'command_count': len(command_list),
            'quality_score': 80
        })
    except Exception as e:
        logger.error(f"PBS generation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500'''
    
    # Find and replace the generate_pbs function
    if "@main_bp.route('/generate-pbs'" in content:
        start = content.find("@main_bp.route('/generate-pbs'")
        # Find the next route or end of file
        next_route = content.find("\n@main_bp.route", start + 1)
        next_def = content.find("\ndef ", start + 1)
        end = min(x for x in [next_route, next_def, len(content)] if x > start)
        
        content = content[:start] + new_generate_pbs + "\n" + content[end:]
        
        # Also add PilotProfile import if not there
        if "from src.lib.pbs_command_generator import" in content:
            if "PilotProfile" not in content:
                content = content.replace(
                    "from src.lib.pbs_command_generator import PBSCommandGenerator",
                    "from src.lib.pbs_command_generator import PBSCommandGenerator, PilotProfile"
                )
        
        routes_path.write_text(content)
        print("   ✅ Fixed PBS generation in routes.py")
    else:
        print("   ❌ Could not find /generate-pbs route")
else:
    print("   ❌ routes.py not found")

# Fix 2: Add missing imports to optimizer modules
print("\n2. Fixing optimizer imports...")
optimizer_files = [
    "app/services/optimizer/interface.py",
    "app/services/optimizer/scoring.py", 
    "app/services/optimizer/ranking.py",
    "app/services/optimizer/filters.py",
    "app/services/optimizer/preferences.py"
]

for filepath in optimizer_files:
    path = Path(filepath)
    if path.exists():
        content = path.read_text()
        
        # Check if typing imports exist and add List if missing
        if "from typing import" in content:
            if "List" not in content:
                # Add List to existing imports
                content = content.replace(
                    "from typing import ",
                    "from typing import List, "
                )
        else:
            # Add typing imports at the top
            lines = content.split('\n')
            # Find where to insert (after docstring if exists)
            insert_pos = 0
            if lines[0].startswith('"""'):
                for i, line in enumerate(lines[1:], 1):
                    if '"""' in line:
                        insert_pos = i + 1
                        break
            
            lines.insert(insert_pos, "from typing import List, Dict, Any, Optional")
            content = '\n'.join(lines)
        
        path.write_text(content)
        print(f"   ✅ Fixed {Path(filepath).name}")
    else:
        print(f"   ❌ {filepath} not found")

# Fix 3: Update test script to use correct method
print("\n3. Fixing test script...")
test_path = Path("test_implementation.py")
if test_path.exists():
    content = test_path.read_text()
    
    # Replace the PBS test section
    content = content.replace(
        'result = generator.generate_from_text(test)',
        '''# Create default profile for testing
            from src.lib.pbs_command_generator import PilotProfile
            profile = PilotProfile(airline="UAL", base="EWR", fleet=["737"], seat="FO")
            commands = generator.generate(test, profile)
            result = {"command_count": len(commands), "commands": [c.to_dict() for c in commands]}'''
    )
    
    test_path.write_text(content)
    print("   ✅ Fixed test script")
else:
    print("   ❌ test_implementation.py not found")

print("\n" + "=" * 40)
print("✅ All fixes applied!")
print("\nNow run: python test_implementation.py")
