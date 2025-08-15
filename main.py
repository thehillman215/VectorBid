
"""
Main entry point for VectorBid - FIXED VERSION
"""

from src.core.app import create_app
import os
import sys

def main():
    """Main function with error handling"""
    try:
        print("=" * 60)
        print("🚀 Starting VectorBid Application")
        print("=" * 60)
        
        # Create the Flask app
        app = create_app()
        
        # Get port from environment or use default
        port = int(os.environ.get("PORT", 5000))
        
        print(f"Starting server on http://0.0.0.0:{port}")
        print(f"Preview URL: https://{os.environ.get('REPLIT_DEV_DOMAIN', 'localhost')}")
        print("=" * 60)
        
        # Run the app
        app.run(
            host="0.0.0.0", 
            port=port, 
            debug=True,
            use_reloader=False,  # Disable reloader for stability
            threaded=True
        )
        
    except Exception as e:
        print(f"❌ Failed to start VectorBid: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
