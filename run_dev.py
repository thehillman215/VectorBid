#!/usr/bin/env python3
"""
Development server for VectorBid with proper preview support
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.app import create_app

if __name__ == "__main__":
    app = create_app()
    
    # Use port 5000 for Replit compatibility
    port = 5000
    
    print(f"Starting VectorBid on http://0.0.0.0:{port}")
    print("Preview should be available in Replit webview")
    
    app.run(
        host="0.0.0.0", 
        port=port, 
        debug=True,
        use_reloader=False,  # Disable reloader for preview stability
        threaded=True
    )