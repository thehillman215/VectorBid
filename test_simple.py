#!/usr/bin/env python3
print("=" * 60)
print("SIMPLE VECTORBID TEST")
print("=" * 60)

# Test 1: PBS Generation
print("\n1. PBS Generation...")
try:
    from src.lib.pbs_wrapper import SimplePBSGenerator
    gen = SimplePBSGenerator()
    result = gen.generate_simple("weekends off and no early mornings")
    print(f"   ✅ Generated {result['command_count']} commands")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Landing Page
print("\n2. Landing Page...")
from pathlib import Path
if Path("src/ui/templates/landing.html").exists():
    print("   ✅ Landing page exists")
else:
    print("   ❌ Landing page missing")

# Test 3: Routes
print("\n3. Routes...")
content = Path("src/api/routes.py").read_text()
if "pbs" in content.lower():
    print("   ✅ PBS route exists")
if "route('/')" in content or 'route("/")' in content:
    print("   ✅ Landing route exists")

print("\n" + "=" * 60)
print("Now run: python main.py")
print("Visit: http://localhost:5000/")
