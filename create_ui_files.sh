#!/bin/bash

echo "📝 Creating UI files..."

# Create the complete ui.py file
cat > app/routes/ui.py << 'EOFILE'
from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates
import httpx
import json
import os
from typing import Dict, Any, Optional
import csv
import io

router = APIRouter(tags=["UI"])
templates = Jinja2Templates(directory="app/templates")

# Backend URL from environment or default
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

async def get_http_client():
    """Dependency to get HTTP client"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main UI page"""
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/parse-preview", response_class=HTMLResponse)
async def parse_preview(
    request: Request, 
    preferences: str = Form(...), 
    persona: str = Form(...),
    client: httpx.AsyncClient = Depends(get_http_client)
):
    """Parse preferences and return preview chips"""
    try:
        # For now, do local parsing until backend endpoint is ready
        parsed_items = []
        
        # Simple keyword extraction
        keywords = {
            "weekends": "Weekends Off",
            "red-eye": "No Red-eyes", 
            "redeye": "No Red-eyes",
            "commute": "Commuter",
            "layover": "Layover Preference",
            "money": "High Pay",
            "senior": "Seniority"
        }
        
        pref_lower = preferences.lower()
        for key, label in keywords.items():
            if key in pref_lower:
                parsed_items.append(label)
        
        if persona:
            parsed_items.append(f"Persona: {persona.title()}")
            
        return templates.TemplateResponse(
            "partials/_parse_chips.html",
            {"request": request, "items": parsed_items}
        )
    except Exception as e:
        return templates.TemplateResponse(
            "partials/_alerts.html",
            {"request": request, "error": str(e), "type": "error"}
        )

@router.post("/run", response_class=HTMLResponse)
async def run_pipeline(
    request: Request,
    preferences: str = Form(...),
    persona: str = Form(...),
    airline: str = Form("UAL"),
    base: str = Form("EWR"),
    seat: str = Form("FO"),
    equipment: str = Form("73G"),
    client: httpx.AsyncClient = Depends(get_http_client)
):
    """Run full pipeline and return results"""
    try:
        # Build the full pipeline request
        pilot_context = {
            "pilot_id": "user1",
            "airline": airline,
            "base": base,
            "seat": seat,
            "equip": [equipment]
        }
        
        # For MVP, create mock PBS layers
        pbs_layers = [
            "AVOID PAIRINGS",
            "  IF REPORT < 0800",
            "  IF LAYOVER CITY = 'LAS'",
            "",
            "PREFER PAIRINGS", 
            "  IF LAYOVER CITY = 'SAN'",
            "  IF CREDIT > 5:00",
            "",
            "AWARD PAIRINGS",
            "  IF DOW = 'SAT,SUN' POINTS -100",
            "  IF REPORT > 0600 AND REPORT < 1000 POINTS +50"
        ]
        
        # Create results
        results = {
            "pbs_layers": pbs_layers,
            "stats": {
                "total_pairings": 127,
                "filtered": 45,
                "preferred": 12,
                "success_probability": "73%"
            },
            "warnings": [],
            "pilot_context": pilot_context
        }
        
        return templates.TemplateResponse(
            "partials/_results_table.html",
            {"request": request, "results": results}
        )
    except Exception as e:
        return templates.TemplateResponse(
            "partials/_alerts.html",
            {"request": request, "error": str(e), "type": "error"}
        )

@router.get("/download/csv")
async def download_csv(data: str = ""):
    """Download results as CSV"""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Layer", "Command"])
    # Add data rows here
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=vectorbid-results.csv"}
    )

@router.get("/health-check", response_class=JSONResponse)
async def health_check(client: httpx.AsyncClient = Depends(get_http_client)):
    """Check backend health"""
    try:
        response = await client.get(f"{BACKEND_URL}/health")
        return {"backend": "online", "status": response.json()}
    except:
        return {"backend": "offline", "status": None}
EOFILE

echo "✅ UI route file created"

# Create base template
cat > app/templates/base.html << 'EOFILE'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VectorBid - AI-Powered PBS Assistant</title>
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="/static/styles.css">
</head>
<body class="bg-gray-50">
    <nav class="bg-blue-900 text-white shadow-lg">
        <div class="container mx-auto px-4 py-3">
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                    <span class="text-2xl">✈️</span>
                    <h1 class="text-2xl font-bold">VectorBid</h1>
                    <span class="text-sm text-blue-200">AI-Powered PBS Assistant</span>
                </div>
                <div class="text-sm">
                    <span hx-get="/health-check" hx-trigger="load, every 30s" hx-target="#status"></span>
                    <span id="status" class="text-green-300">● Online</span>
                </div>
            </div>
        </div>
    </nav>
    <main>
        {% block content %}{% endblock %}
    </main>
</body>
</html>
EOFILE

echo "✅ Base template created"

# Create index template
cat > app/templates/index.html << 'EOFILE'
{% extends "base.html" %}

{% block content %}
<div class="container mx-auto px-4 py-8">
    <div class="max-w-5xl mx-auto">
        <!-- Main Form Card -->
        <div class="bg-white rounded-xl shadow-lg p-8 mb-8">
            <h2 class="text-3xl font-bold mb-2 text-gray-800">Generate Your Monthly Bid</h2>
            <p class="text-gray-600 mb-8">Tell us your preferences and we'll generate optimized PBS commands</p>
            
            <form hx-post="/run" hx-target="#results" hx-indicator="#spinner" class="space-y-6">
                <!-- Two Column Layout -->
                <div class="grid md:grid-cols-2 gap-6">
                    <!-- Left Column - Pilot Info -->
                    <div class="space-y-4">
                        <h3 class="font-semibold text-gray-700 border-b pb-2">Pilot Information</h3>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Airline</label>
                            <select name="airline" class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                                <option value="UAL">United Airlines</option>
                                <option value="DAL">Delta Air Lines</option>
                                <option value="AAL">American Airlines</option>
                                <option value="SWA">Southwest Airlines</option>
                            </select>
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Base</label>
                            <input type="text" name="base" value="EWR" placeholder="e.g., EWR, ORD, DEN" 
                                   class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Position</label>
                            <select name="seat" class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                                <option value="CPT">Captain</option>
                                <option value="FO" selected>First Officer</option>
                            </select>
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Equipment</label>
                            <select name="equipment" class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                                <option value="73G">737</option>
                                <option value="320">A320</option>
                                <option value="787">787</option>
                                <option value="777">777</option>
                            </select>
                        </div>
                    </div>
                    
                    <!-- Right Column - Preferences -->
                    <div class="space-y-4">
                        <h3 class="font-semibold text-gray-700 border-b pb-2">Bidding Preferences</h3>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Persona</label>
                            <select name="persona" class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                                <option value="commuter">🏠 Commuter</option>
                                <option value="family">👨‍👩‍👧‍👦 Family First</option>
                                <option value="money">💰 Money Maximizer</option>
                                <option value="seniority">📈 Seniority Builder</option>
                                <option value="custom">✏️ Custom</option>
                            </select>
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">
                                Your Preferences
                                <span class="text-xs text-gray-500">(Natural language)</span>
                            </label>
                            <textarea 
                                name="preferences" 
                                rows="6"
                                class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                                placeholder="Examples:&#10;• I want weekends off&#10;• Prefer SAN layovers&#10;• No red-eyes&#10;• Avoid trips longer than 3 days&#10;• Maximize credit hours"
                                hx-post="/parse-preview"
                                hx-trigger="keyup changed delay:1s"
                                hx-target="#parse-preview"
                            ></textarea>
                        </div>
                    </div>
                </div>
                
                <!-- Parse Preview -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Detected Preferences:</label>
                    <div id="parse-preview" class="min-h-[40px] p-3 bg-gray-50 rounded-lg">
                        <span class="text-gray-400 text-sm">Start typing to see detected preferences...</span>
                    </div>
                </div>
                
                <!-- Submit Button -->
                <div class="flex items-center justify-between pt-4 border-t">
                    <span id="spinner" class="htmx-indicator text-blue-600">
                        ⟲ Processing...
                    </span>
                    <button type="submit" 
                            class="bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors">
                        Generate PBS Commands
                    </button>
                </div>
            </form>
        </div>
        
        <!-- Results Area -->
        <div id="results">
            <!-- Results will be inserted here -->
        </div>
    </div>
</div>
{% endblock %}
EOFILE

echo "✅ Index template created"

# Create all partials - need to continue the script
cat > create_ui_files_part2.sh << 'INNEREOF'
#!/bin/bash

# Parse chips partial
cat > app/templates/partials/_parse_chips.html << 'EOFILE'
<div class="flex flex-wrap gap-2">
    {% if items %}
        {% for item in items %}
        <span class="inline-flex items-center px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
            <span class="mr-1">✓</span> {{ item }}
        </span>
        {% endfor %}
    {% else %}
        <span class="text-gray-400 text-sm">No preferences detected yet...</span>
    {% endif %}
</div>
EOFILE

# Results table partial
cat > app/templates/partials/_results_table.html << 'EOFILE'
<div class="bg-white rounded-xl shadow-lg p-8 animate-fade-in">
    <div class="flex items-center justify-between mb-6">
        <h3 class="text-2xl font-bold text-gray-800">Generated PBS Commands</h3>
        <span class="text-sm text-green-600 font-medium">
            ✓ {{ results.stats.success_probability }} Success Rate
        </span>
    </div>
    
    <!-- Stats Grid -->
    <div class="grid grid-cols-4 gap-4 mb-6">
        <div class="bg-gray-50 p-3 rounded-lg">
            <div class="text-2xl font-bold text-blue-600">{{ results.stats.total_pairings }}</div>
            <div class="text-xs text-gray-600">Total Pairings</div>
        </div>
        <div class="bg-gray-50 p-3 rounded-lg">
            <div class="text-2xl font-bold text-green-600">{{ results.stats.filtered }}</div>
            <div class="text-xs text-gray-600">Filtered</div>
        </div>
        <div class="bg-gray-50 p-3 rounded-lg">
            <div class="text-2xl font-bold text-purple-600">{{ results.stats.preferred }}</div>
            <div class="text-xs text-gray-600">Preferred</div>
        </div>
        <div class="bg-gray-50 p-3 rounded-lg">
            <div class="text-2xl font-bold text-orange-600">{{ results.stats.success_probability }}</div>
            <div class="text-xs text-gray-600">Success Rate</div>
        </div>
    </div>
    
    <!-- PBS Commands -->
    <div class="bg-gray-900 text-green-400 p-6 rounded-lg font-mono text-sm mb-6 overflow-x-auto">
        <pre id="pbs-output">{% for line in results.pbs_layers %}{{ line }}
{% endfor %}</pre>
    </div>
    
    <!-- Action Buttons -->
    <div class="flex flex-wrap gap-3">
        <button onclick="copyPBS()" 
                class="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors">
            📋 Copy PBS Commands
        </button>
        <button onclick="downloadPBS()" 
                class="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors">
            💾 Download PBS File
        </button>
        <button onclick="downloadJSON()" 
                class="bg-gray-600 text-white px-6 py-2 rounded-lg hover:bg-gray-700 transition-colors">
            📊 Download Analysis
        </button>
        <button hx-get="/" hx-target="body" 
                class="bg-white text-gray-700 px-6 py-2 rounded-lg border hover:bg-gray-50 transition-colors">
            🔄 New Bid
        </button>
    </div>
</div>

<script>
function copyPBS() {
    const text = document.getElementById('pbs-output').innerText;
    navigator.clipboard.writeText(text).then(() => {
        alert('✅ PBS commands copied to clipboard!');
    });
}

function downloadPBS() {
    const text = document.getElementById('pbs-output').innerText;
    const blob = new Blob([text], {type: 'text/plain'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'vectorbid-pbs-commands.txt';
    a.click();
    URL.revokeObjectURL(url);
}

function downloadJSON() {
    const results = {{ results | tojson }};
    const blob = new Blob([JSON.stringify(results, null, 2)], {type: 'application/json'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'vectorbid-analysis.json';
    a.click();
    URL.revokeObjectURL(url);
}
</script>
EOFILE

# Alerts partial
cat > app/templates/partials/_alerts.html << 'EOFILE'
<div class="rounded-lg p-4 mb-4 {% if type == 'error' %}bg-red-100 border border-red-400 text-red-700{% elif type == 'warning' %}bg-yellow-100 border border-yellow-400 text-yellow-700{% else %}bg-blue-100 border border-blue-400 text-blue-700{% endif %}">
    <div class="flex">
        <div class="flex-shrink-0">
            {% if type == 'error' %}❌{% elif type == 'warning' %}⚠️{% else %}ℹ️{% endif %}
        </div>
        <div class="ml-3">
            <p class="text-sm font-medium">
                {% if type == 'error' %}Error{% elif type == 'warning' %}Warning{% else %}Info{% endif %}
            </p>
            <p class="text-sm mt-1">{{ error if error else message }}</p>
        </div>
    </div>
</div>
EOFILE

# Create styles.css
cat > app/static/styles.css << 'EOFILE'
/* HTMX Loading States */
.htmx-indicator {
    display: none;
}

.htmx-request .htmx-indicator {
    display: inline-block;
    animation: spin 1s linear infinite;
}

/* Animations */
@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

@keyframes fade-in {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.animate-fade-in {
    animation: fade-in 0.3s ease-out;
}

/* Custom Scrollbar for Code Blocks */
pre::-webkit-scrollbar {
    height: 8px;
    width: 8px;
}

pre::-webkit-scrollbar-track {
    background: #1a1a1a;
}

pre::-webkit-scrollbar-thumb {
    background: #4a4a4a;
    border-radius: 4px;
}

pre::-webkit-scrollbar-thumb:hover {
    background: #5a5a5a;
}
EOFILE

echo "✅ All partials and styles created!"
INNEREOF

chmod +x create_ui_files_part2.sh
bash create_ui_files_part2.sh
rm create_ui_files_part2.sh

echo "✅ All UI files created successfully!"
