#!/usr/bin/env python3
from pathlib import Path

# Fix the List import in all optimizer files
files_to_fix = [
    "app/services/optimizer/interface.py",
    "app/services/optimizer/scoring.py",
    "app/services/optimizer/ranking.py",
    "app/services/optimizer/filters.py",
    "app/services/optimizer/preferences.py"
]

for filepath in files_to_fix:
    path = Path(filepath)
    if path.exists():
        content = path.read_text()
        if "from typing import" in content and "List" not in content:
            content = content.replace(
                "from typing import",
                "from typing import List, "
            )
        elif "from typing" not in content:
            lines = content.split('\n')
            lines.insert(0, "from typing import List, Dict, Any, Optional")
            content = '\n'.join(lines)
        
        path.write_text(content)
        print(f"✅ Fixed {filepath}")
    else:
        print(f"❌ {filepath} not found")

print("\nNow checking PBS generator methods...")
pbs_path = Path("src/lib/pbs_command_generator.py")
if pbs_path.exists():
    content = pbs_path.read_text()
    if "def generate_from_text" not in content:
        print("PBS uses different method. Checking for correct method...")
        if "def generate(" in content:
            print("Found: generate() method")
            print("\nUpdating routes.py to use correct method...")
            
            routes = Path("src/api/routes.py")
            routes_content = routes.read_text()
            routes_content = routes_content.replace(
                "result = generator.generate_from_text(preferences)",
                "result = generator.generate(preferences)"
            )
            routes.write_text(routes_content)
            print("✅ Updated routes.py")
