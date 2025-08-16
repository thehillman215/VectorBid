#!/bin/bash
echo "📝 Creating UI files..."

# Create UI route
cat > app/routes/ui.py << 'EOFILE'
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["UI"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/run", response_class=HTMLResponse)
async def run_pipeline(request: Request, preferences: str = Form(...)):
    pbs_layers = [
        "AVOID PAIRINGS",
        "  IF REPORT < 0800",
        "PREFER PAIRINGS", 
        "  IF LAYOVER CITY = 'SAN'"
    ]
    results = {"pbs_layers": pbs_layers}
    return templates.TemplateResponse("results.html", {"request": request, "results": results})
EOFILE

# Create templates
mkdir -p app/templates
cat > app/templates/index.html << 'EOFILE'
<!DOCTYPE html>
<html>
<head>
    <title>VectorBid</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 p-8">
    <div class="max-w-2xl mx-auto bg-white rounded-lg shadow p-6">
        <h1 class="text-2xl font-bold mb-4">✈️ VectorBid PBS Generator</h1>
        <form method="post" action="/run">
            <textarea name="preferences" rows="4" class="w-full p-2 border rounded" 
                placeholder="I want weekends off, prefer SAN layovers..."></textarea>
            <button type="submit" class="mt-4 bg-blue-600 text-white px-4 py-2 rounded">
                Generate PBS Commands
            </button>
        </form>
    </div>
</body>
</html>
EOFILE

cat > app/templates/results.html << 'EOFILE'
<!DOCTYPE html>
<html>
<head>
    <title>VectorBid Results</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 p-8">
    <div class="max-w-2xl mx-auto bg-white rounded-lg shadow p-6">
        <h2 class="text-xl font-bold mb-4">PBS Commands</h2>
        <pre class="bg-gray-900 text-green-400 p-4 rounded">{% for line in results.pbs_layers %}{{ line }}
{% endfor %}</pre>
        <button onclick="navigator.clipboard.writeText(document.querySelector('pre').innerText)" 
                class="mt-4 bg-green-600 text-white px-4 py-2 rounded">
            Copy PBS Commands
        </button>
        <a href="/" class="ml-2 bg-gray-600 text-white px-4 py-2 rounded inline-block">New Bid</a>
    </div>
</body>
</html>
EOFILE

echo "✅ UI files created!"
