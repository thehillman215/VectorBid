#!/usr/bin/env python3
"""
Clean up routes.py by removing the broken function
Since we have the working version in pbs_fixed.py, we just need to clean routes.py
Run: python clean_routes.py
"""

import os
import shutil
from datetime import datetime

print("=" * 60)
print("🧹 CLEANING ROUTES.PY")
print("=" * 60)
print()

routes_path = "src/api/routes.py"

# Backup first
if os.path.exists(routes_path):
    backup_path = f"{routes_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(routes_path, backup_path)
    print(f"✅ Backed up to: {backup_path}")

    # Read the file
    with open(routes_path, 'r') as f:
        lines = f.readlines()

    # Find and remove the broken function
    new_lines = []
    skip_mode = False
    skip_count = 0

    for i, line in enumerate(lines):
        # Check if this starts the broken function
        if 'def _fallback_pbs_generation' in line or 'def natural_language_to_pbs_filters' in line:
            skip_mode = True
            skip_count = 0
            print(f"  🔍 Found broken function at line {i+1}, removing...")
            continue

        # If we're in skip mode, keep skipping until we find the next function or reach enough lines
        if skip_mode:
            skip_count += 1
            # Stop skipping when we find the next function definition or class, or after 100 lines
            if (line.strip().startswith('def ') and skip_count > 2) or \
               line.strip().startswith('class ') or \
               line.strip().startswith('@') or \
               skip_count > 100:
                skip_mode = False
                # Don't skip this line - it's the start of the next function
                new_lines.append(line)
            # Skip this line if still in skip mode
            continue

        # Keep this line
        new_lines.append(line)

    # Make sure the import is there
    has_import = any('from src.lib.pbs_fixed import' in line
                     for line in new_lines)

    if not has_import:
        print("  📝 Adding import for fixed PBS functions...")
        # Find where to add the import (after other imports)
        import_index = 0
        for i, line in enumerate(new_lines):
            if line.startswith('import ') or line.startswith('from '):
                import_index = i + 1

        # Add the import
        new_lines.insert(import_index, '\n')
        new_lines.insert(import_index + 1,
                         '# Fixed PBS generation functions\n')
        new_lines.insert(
            import_index + 2,
            'from src.lib.pbs_fixed import natural_language_to_pbs_filters, _fallback_pbs_generation\n'
        )

    # Write the cleaned file
    with open(routes_path, 'w') as f:
        f.writelines(new_lines)

    print("  ✅ Cleaned routes.py")
    print("  ✅ Import for fixed functions confirmed")

print()
print("=" * 60)
print("✅ ROUTES.PY CLEANED!")
print("=" * 60)
print()
print("Now try: python main.py")
print()
print("If there are still issues, use the emergency fix:")
print("python emergency_routes_fix.py")
