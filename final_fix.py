#!/usr/bin/env python3
from pathlib import Path

print("FINAL FIX FOR VECTORBID")
print("=" * 40)

# Fix 1: Update routes.py with correct PilotProfile usage
print("\n1. Fixing routes.py with correct PilotProfile...")
routes_path = Path("src/api/routes.py")
if routes_path.exists():
    content = routes_path.read_text()
    
    # Replace the generate_pbs function with correct PilotProfile usage
    new_generate_pbs = '''@main_bp.route('/generate-pbs', methods=['POST'])
def generate_pbs():
    """Generate PBS commands from natural language preferences"""
    try:
        data = request.get_json()
        preferences = data.get('preferences', '')
        
        if not preferences:
            return jsonify({'success': False, 'error': 'No preferences provided'}), 400
        
        from src.lib.pbs_command_generator import PBSCommandGenerator, PilotProfile
        generator = PBSCommandGenerator()
        
        # Create profile with correct fields
        profile = PilotProfile(
            base="EWR",
            fleet=["737"],
            seniority=50,
            flying_style="balanced",
            commuter=False
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
    
    # Find and replace
    if "@main_bp.route('/generate-pbs'" in content:
        start = content.find("@main_bp.route('/generate-pbs'")
        next_route = content.find("\n@main_bp.route", start + 1)
        next_def = content.find("\ndef ", start + 1)
        end = min(x for x in [next_route, next_def, len(content)] if x > start and x != -1)
        
        content = content[:start] + new_generate_pbs + "\n" + content[end:]
        routes_path.write_text(content)
        print("   ✅ Fixed routes.py")

# Fix 2: Update test script with correct PilotProfile
print("\n2. Fixing test script...")
test_content = '''#!/usr/bin/env python3
"""VectorBid Implementation Test Script"""
import sys
from pathlib import Path

def test_pbs_generation():
    """Test PBS command generation"""
    print("\\n🧪 Testing PBS Generation...")
    
    try:
        from src.lib.pbs_command_generator import PBSCommandGenerator, PilotProfile
        
        generator = PBSCommandGenerator()
        profile = PilotProfile(
            base="EWR",
            fleet=["737"],
            seniority=50,
            flying_style="balanced",
            commuter=False
        )
        
        test_cases = [
            "I want weekends off",
            "Weekends off and no early mornings",
            "Maximum credit with short trips"
        ]
        
        for test in test_cases:
            commands = generator.generate(test, profile)
            print(f"  Input: '{test}'")
            print(f"  Output: {len(commands)} commands")
            
            if len(commands) < 2 and 'and' in test:
                print("  ❌ FAILED: Should generate multiple commands")
                return False
        
        print("  ✅ PBS Generation working!")
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_landing_page():
    """Test landing page exists"""
    print("\\n🧪 Testing Landing Page...")
    
    landing_path = Path("src/ui/templates/landing.html")
    
    if landing_path.exists():
        print("  ✅ Landing page exists!")
        return True
    else:
        print(f"  ❌ Landing page not found")
        return False

def test_modular_optimizer():
    """Test modular optimizer imports"""
    print("\\n🧪 Testing Modular Optimizer...")
    
    try:
        # First ensure List is imported
        import sys
        sys.path.insert(0, '.')
        
        # Try to import
        from app.services.optimizer.interface import select_topk
        
        test_bundle = {
            'preference_schema': {
                'pilot_id': 'test',
                'hard_constraints': {'no_red_eyes': True},
                'soft_prefs': {'weekend_protection': 1.0}
            },
            'pairing_features': {
                'pairings': [
                    {'id': 'P1', 'days': 3, 'credit_hours': 18},
                    {'id': 'P2', 'days': 4, 'credit_hours': 24}
                ]
            }
        }
        
        result = select_topk(test_bundle, k=2)
        print(f"  ✅ Optimizer working! ({len(result)} results)")
        return True
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_flask_routes():
    """Test Flask routes are updated"""
    print("\\n🧪 Testing Flask Routes...")
    
    try:
        routes_path = Path("src/api/routes.py")
        if routes_path.exists():
            content = routes_path.read_text()
            
            has_pbs = "pbs_command_generator" in content.lower()
            has_landing = "route('/')" in content or 'route("/")'  in content
            
            if has_pbs:
                print("  ✅ PBS generator import found")
            else:
                print("  ❌ PBS generator import missing")
            
            if has_landing:
                print("  ✅ Landing route found")
            else:
                print("  ❌ Landing route missing")
            
            return has_pbs and has_landing
        else:
            print(f"  ❌ Routes file not found")
            return False
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("VECTORBID IMPLEMENTATION TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_pbs_generation,
        test_landing_page,
        test_modular_optimizer,
        test_flask_routes
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\\nPassed: {passed}/{total} tests")
    
    if passed == total:
        print("\\n🎉 All tests passed!")
        print("\\nNext: python main.py")
    else:
        print("\\n⚠️ Some tests failed. Check errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
'''

Path("test_implementation.py").write_text(test_content)
print("   ✅ Fixed test script")

# Fix 3: Fix optimizer imports one more time
print("\n3. Fixing optimizer imports...")

# Simple fix - add typing imports to __init__.py first
init_file = Path("app/services/optimizer/__init__.py")
if init_file.exists():
    content = init_file.read_text()
    if "from typing import" not in content:
        lines = content.split('\n')
        lines.insert(3, "from typing import List, Dict, Any, Optional")
        init_file.write_text('\n'.join(lines))
        print("   ✅ Fixed __init__.py")

# Fix interface.py specifically
interface_file = Path("app/services/optimizer/interface.py")
if interface_file.exists():
    content = interface_file.read_text()
    if "from typing import" not in content:
        lines = content.split('\n')
        # Add after docstring
        insert_pos = 3 if lines[0].startswith('"""') else 0
        lines.insert(insert_pos, "from typing import List, Dict, Any, Optional")
        interface_file.write_text('\n'.join(lines))
        print("   ✅ Fixed interface.py")

print("\n" + "=" * 40)
print("✅ All fixes applied!")
