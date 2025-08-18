#!/bin/bash

# VectorBid Development Startup Script
# Starts FastAPI backend + serves frontend

echo "🚀 Starting VectorBid Development Environment"
echo "=============================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found"
    exit 1
fi

# Check if required packages are installed
echo "📦 Checking dependencies..."
python3 -c "import fastapi, uvicorn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Installing required packages..."
    pip install fastapi uvicorn
fi

# Create static directory if it doesn't exist
mkdir -p app/static

echo "🔧 Starting FastAPI server..."
echo "📍 Backend: http://localhost:8000"
echo "🌐 Frontend: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start the FastAPI server with hot reload
export PYTHONPATH=/home/runner/workspace:$PYTHONPATH
python3 -m uvicorn app.fastapi_main:app --host 0.0.0.0 --port 8000 --reload