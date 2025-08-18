#!/usr/bin/env python3
"""Direct fix for the test file - replaces the broken section"""

# Read the broken test file
with open("hardcore_pilot_test_fixed.py") as f:
    lines = f.readlines()

# Find line 165 area and fix it
new_lines = []
skip_next = 0

for i, line in enumerate(lines):
    if skip_next > 0:
        skip_next -= 1
        continue

    # Fix the specific dates section
    if (
        i >= 160
        and i <= 180
        and "for desc, input_text, min_cmd, must_have in test_cases:" in line
    ):
        # Replace with a working loop
        new_lines.append("    for test in test_cases:\n")
        new_lines.append("        if len(test) == 4:\n")
        new_lines.append("            desc, input_text, min_cmd, must_have = test\n")
        new_lines.append("        else:\n")
        new_lines.append("            desc, input_text, min_cmd = test\n")
        new_lines.append("            must_have = []\n")
        skip_next = 0
    else:
        new_lines.append(line)

# Write the fixed version
with open("hardcore_pilot_test_working.py", "w") as f:
    f.writelines(new_lines)

print("✅ Created hardcore_pilot_test_working.py")
print("Run: python hardcore_pilot_test_working.py")
