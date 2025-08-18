import os

# Read the current ui.py
with open("app/routes/ui.py") as f:
    content = f.read()

# Fix the main index route to return smart_bid.html
content = content.replace(
    'return templates.TemplateResponse("monthly_bid.html"',
    'return templates.TemplateResponse("smart_bid.html"',
)

# Make sure we're returning smart_bid for logged in users
if "smart_bid.html" not in content:
    print("⚠️ smart_bid.html not found in routes, fixing...")
    # Find the index function and fix it

    pattern = (
        r'(def index.*?)(return templates\.TemplateResponse\(["\'])\w+\.html(["\'])'
    )

    def replace_template(match):
        if "return RedirectResponse" in match.group(0):
            return match.group(0)
        return match.group(1) + match.group(2) + "smart_bid.html" + match.group(3)

    # Fix the template reference
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if "def index" in line:
            # Look ahead for the return statement
            for j in range(i, min(i + 20, len(lines))):
                if (
                    "return templates.TemplateResponse" in lines[j]
                    and "onboarding" not in lines[j]
                ):
                    lines[j] = (
                        '    return templates.TemplateResponse("smart_bid.html", {'
                    )
                    print(f"✅ Fixed line {j}: {lines[j]}")
                    break
            break
    content = "\n".join(lines)

# Write it back
with open("app/routes/ui.py", "w") as f:
    f.write(content)

print("✅ Fixed UI route to use smart_bid.html")
print("🔍 Verifying...")
os.system("grep -n 'smart_bid.html' app/routes/ui.py")
