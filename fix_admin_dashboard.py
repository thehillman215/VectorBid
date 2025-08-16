
# Read the file
with open('src/api/admin_unified.py') as f:
    content = f.read()

# Replace the problematic template lines
old_storage = '{{ "%.1f"|format(packets|sum(attribute=\'size_mb\', default=0)) }} MB'
new_storage = '{{ storage_mb }} MB'

old_airlines = '{{ packets|map(attribute=\'airline\')|unique|list|length }}'
new_airlines = '{{ unique_airlines }}'

content = content.replace(old_storage, new_storage)
content = content.replace(old_airlines, new_airlines)

# Now we need to add the calculations before the render_template_string call
# Find the line "return render_template_string(dashboard_html,"
import re

# Add calculations before the return statement
calculation_code = """
    # Calculate statistics
    storage_mb = sum(p.get('size_mb', 0) for p in packets) if packets else 0
    storage_mb = round(storage_mb, 1)
    
    airlines = set(p.get('airline', '') for p in packets if p.get('airline'))
    unique_airlines = len(airlines)
    
"""

# Find where to insert the calculations
pattern = r'(    return render_template_string\(dashboard_html,)'
replacement = calculation_code + r'\1'
content = re.sub(pattern, replacement, content)

# Update the render_template_string call to include new variables
old_render = 'return render_template_string(dashboard_html, packets=packets, contracts=contracts)'
new_render = 'return render_template_string(dashboard_html, packets=packets, contracts=contracts, storage_mb=storage_mb, unique_airlines=unique_airlines)'
content = content.replace(old_render, new_render)

# Write the fixed content
with open('src/api/admin_unified.py', 'w') as f:
    f.write(content)

print("Dashboard fixed!")
