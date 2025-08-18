# Update the index route to show navigation menu
with open("app/routes/ui.py") as f:
    content = f.read()

# Add a simple navigation index
nav_route = '''
@router.get("/", response_class=HTMLResponse)
async def index(request: Request, pilot_id: Optional[str] = Cookie(None)):
    """Main page with navigation"""
    profile = get_pilot_profile(pilot_id, request) if TEST_MODE else get_pilot_profile(pilot_id)

    # Show navigation menu
    return templates.TemplateResponse("index_nav.html", {
        "request": request,
        "profile": profile
    })

@router.get("/bid", response_class=HTMLResponse)
async def bid_page(request: Request, pilot_id: Optional[str] = Cookie(None)):
    """Actual bidding page"""
    profile = get_pilot_profile(pilot_id, request) if TEST_MODE else get_pilot_profile(pilot_id)

    if not profile:
        return RedirectResponse(url="/onboarding", status_code=302)
    history = get_pilot_history(pilot_id)
    saved_prefs = SAVED_PREFERENCES.get(pilot_id, [])
    return templates.TemplateResponse("smart_bid.html", {
        "request": request,
        "profile": profile,
        "personas": PERSONAS,
        "current_month": "January 2025",
        "history": history,
        "saved_preferences": saved_prefs
    })
'''

# Find and replace the index function

lines = content.split("\n")
in_index = False
start_line = -1

for i, line in enumerate(lines):
    if '@router.get("/", response_class=HTMLResponse)' in line:
        start_line = i
        in_index = True
    elif in_index and "def " in lines[i + 1] if i + 1 < len(lines) else False:
        # Find the end of this function
        for j in range(i + 2, len(lines)):
            if lines[j] and not lines[j].startswith(" ") and not lines[j].startswith("\t"):
                # Replace this section
                lines = lines[:start_line] + nav_route.split("\n") + lines[j:]
                break
        break

content = "\n".join(lines)

with open("app/routes/ui.py", "w") as f:
    f.write(content)

print("✅ Updated routes with navigation")
