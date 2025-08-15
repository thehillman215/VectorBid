
"""
Main entry point for VectorBid
"""

from src.core.app import create_app
import os

# Create Flask app instance for gunicorn
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
