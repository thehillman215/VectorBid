#!/usr/bin/env python3
"""
Run VectorBid on port 8080 for multiple app development
"""
import os
import sys

# Set the port before importing the app
os.environ['PORT'] = '8080'

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.app import create_app

if __name__ == "__main__":
    app = create_app()
    print("🚀 Starting VectorBid on port 8080...")
    print("📱 You can now run multiple Replit apps in different Chrome windows!")
    print("🌐 Access at: http://localhost:8080")
    app.run(host="0.0.0.0", port=8080, debug=True)