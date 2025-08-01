"""VectorBid Application Entry Point

This module serves as the entry point for the VectorBid Flask application.
It imports and creates the Flask app instance using the application factory pattern.
"""

from src.core.app import create_app

# Create the Flask application instance
app = create_app()

if __name__ == '__main__':
    # Run the application in development mode
    app.run(host='0.0.0.0', port=5000, debug=True)