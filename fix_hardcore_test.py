#!/usr/bin/env python3
"""Fix the hardcore test script bug"""

# Read and fix the file
with open('hardcore_pilot_test.py') as f:
    content = f.read()

# Fix the test cases that are missing the 4th parameter
# The error is in CATEGORY 5: SPECIFIC DATES & TIMES

# Find and replace the problematic section
old_section = '''test_cases = [
    ("Birthday off",
     "Need March 15th off for my birthday every year",
     1),

    ("Anniversary planning",
     "Wedding anniversary June 20-22 need those days off",
     1),

    ("School schedule",
     "Kids spring break March 10-17 want to be off",
     1),

    ("Training month",
     "Have recurrent training this month need 3 days available",
     1, ["TRAINING"]),
]'''

new_section = '''test_cases = [
    ("Birthday off",
     "Need March 15th off for my birthday every year",
     1, []),

    ("Anniversary planning",
     "Wedding anniversary June 20-22 need those days off",
     1, []),

    ("School schedule",
     "Kids spring break March 10-17 want to be off",
     1, []),

    ("Training month",
     "Have recurrent training this month need 3 days available",
     1, ["TRAINING"]),
]'''

content = content.replace(old_section, new_section)

# Write back
with open('hardcore_pilot_test_fixed.py', 'w') as f:
    f.write(content)

print("✅ Created hardcore_pilot_test_fixed.py with the bug fix")
print("Run: python hardcore_pilot_test_fixed.py")
