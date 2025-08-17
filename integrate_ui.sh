#!/bin/bash

echo "🔧 Integrating UI with FastAPI app..."

# Check if app/main.py includes UI routes
if ! grep -q "app.routes.ui" app/main.py 2>/dev/null; then
    echo "Adding UI routes to app/main.py..."
    
    # Create a backup
    cp app/main.py app/main.py.backup 2>/dev/null || echo "⚠️  Could not backup main.py"
    
    # Add UI integration
    cat >> app/main.py << 'EOFILE'

# UI Routes Integration
try:
    from app.routes.ui import router as ui_router
    app.include_router(ui_router, prefix="", tags=["UI"])
    print("✅ UI routes registered")
except ImportError as e:
    print(f"⚠️  UI routes not available: {e}")

# Static files
try:
    from fastapi.staticfiles import StaticFiles
    import os
    if os.path.exists("app/static"):
        app.mount("/static", StaticFiles(directory="app/static"), name="static")
        print("✅ Static files mounted")
except Exception as e:
    print(f"⚠️  Static files not mounted: {e}")
EOFILE
else
    echo "✅ UI routes already integrated"
fi

echo "✅ Integration complete!"
echo ""
echo "🚀 To start the application:"
echo "   python -m uvicorn app.main:app --reload --port 8000"
echo ""
echo "🌐 Then visit: http://localhost:8000/"
