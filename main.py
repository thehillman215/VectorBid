"""
Main entry point for VectorBid
"""

import os
import socket

from src.core.app import create_app


def find_free_port(start_port=5000, max_attempts=10):
    """Find a free port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            # Test if port is available
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("0.0.0.0", port))
                print(f"✅ Found available port: {port}")
                return port
        except OSError:
            print(f"⚠️ Port {port} is in use, trying next...")
            continue

    # Fallback to default if no port found
    print("❌ No free ports found in range, using fallback port 8080")
    return 8080


# Create Flask app instance for gunicorn
app = create_app()

if __name__ == "__main__":
    # Try to find a free port starting from 5000
    available_port = find_free_port(5000)
    port = int(os.environ.get("PORT", available_port))

    print(f"🚀 Starting VectorBid on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
