#!/bin/bash

echo "🚀 Setting up VectorBid UI Layer"
echo "================================"

# Step 1: Create all directories
echo "📁 Creating directory structure..."
mkdir -p app/routes
mkdir -p app/templates/partials
mkdir -p app/static
mkdir -p app/auth
mkdir -p app/client
mkdir -p contracts

# Step 2: Check if backend is running
echo "🔍 Checking backend status..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    BACKEND_URL="http://localhost:8000"
    echo "✅ Backend found at http://localhost:8000"
elif curl -s http://localhost:8050/health > /dev/null 2>&1; then
    BACKEND_URL="http://localhost:8050"
    echo "✅ Backend found at http://localhost:8050"
else
    echo "⚠️  Backend not running. Starting it now..."
    python -m uvicorn app.main:app --reload --port 8000 &
    sleep 3
    BACKEND_URL="http://localhost:8000"
fi

# Step 3: Download OpenAPI spec
echo "📥 Fetching OpenAPI spec..."
curl -sS ${BACKEND_URL}/openapi.json > contracts/openapi.json
echo "✅ OpenAPI spec saved to contracts/openapi.json"

# Step 4: Install dependencies
echo "📦 Installing dependencies..."
pip install httpx jinja2 openapi-python-client fastapi

# Step 5: Generate typed client
echo "🔧 Generating typed client..."
if command -v openapi-python-client &> /dev/null; then
    openapi-python-client generate --path contracts/openapi.json --output-path app/client --overwrite
    echo "✅ Typed client generated"
else
    echo "⚠️  openapi-python-client not found, using httpx directly"
fi

echo ""
echo "✨ Setup complete!"
echo "📝 Next steps:"
echo "   1. Run: bash create_ui_files.sh"
echo "   2. Visit: ${BACKEND_URL}/"
echo "   3. Test the UI flow"
