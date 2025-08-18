"""
Main entry point for VectorBid - Flask with FastAPI-style routes
"""

import os
from flask import Flask, jsonify, request
from src.lib.pbs_command_generator import generate_pbs_commands
from src.lib.personas import PILOT_PERSONAS
from src.lib.bid_packet_manager import BidPacketManager

def create_app():
    """Create Flask app with FastAPI-style API routes"""
    app = Flask(__name__)
    
    # Root route for web interface
    @app.route("/")
    def index():
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>VectorBid - AI-Powered Pilot Scheduling</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
            <style>
                body { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); min-height: 100vh; color: white; }
                .hero { padding: 100px 0; }
                .api-card { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); }
                .btn-api { background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3); color: white; }
                .btn-api:hover { background: rgba(255,255,255,0.3); color: white; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="hero text-center">
                    <i class="fas fa-plane fa-4x mb-4"></i>
                    <h1 class="display-4 fw-bold">VectorBid</h1>
                    <p class="lead">AI-Powered Pilot Schedule Bidding Assistant</p>
                    <p class="fs-5">Modern API endpoints with FastAPI-style patterns</p>
                </div>
                
                <div class="row g-4 mb-5">
                    <div class="col-md-6">
                        <div class="card api-card h-100">
                            <div class="card-body">
                                <h5 class="card-title"><i class="fas fa-heartbeat me-2"></i>Health Check</h5>
                                <p class="card-text">Check API status and service health</p>
                                <a href="/health" class="btn btn-api">GET /health</a>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card api-card h-100">
                            <div class="card-body">
                                <h5 class="card-title"><i class="fas fa-info-circle me-2"></i>API Status</h5>
                                <p class="card-text">View available endpoints and API information</p>
                                <a href="/api/v1/status" class="btn btn-api">GET /api/v1/status</a>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card api-card h-100">
                            <div class="card-body">
                                <h5 class="card-title"><i class="fas fa-user-tie me-2"></i>Pilot Personas</h5>
                                <p class="card-text">Get available pilot personas for bidding strategies</p>
                                <a href="/api/v1/personas" class="btn btn-api">GET /api/v1/personas</a>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card api-card h-100">
                            <div class="card-body">
                                <h5 class="card-title"><i class="fas fa-cogs me-2"></i>PBS Generation</h5>
                                <p class="card-text">Generate PBS commands from pilot preferences</p>
                                <button class="btn btn-api" onclick="testPBS()">POST /api/v1/pbs/generate</button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="text-center">
                    <h3>API Documentation</h3>
                    <p>This application provides modern REST API endpoints with JSON request/response handling.</p>
                    <p><strong>Framework:</strong> Flask with FastAPI-style patterns | <strong>Deployment:</strong> WSGI compatible</p>
                </div>
            </div>
            
            <script>
                async function testPBS() {
                    try {
                        const response = await fetch('/api/v1/pbs/generate', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                preferences: 'I want weekends off and morning departures',
                                pilot_profile: { airline: 'UAL', base: 'SFO' }
                            })
                        });
                        const result = await response.json();
                        alert('PBS Generation successful! Check console for details.');
                        console.log('PBS Result:', result);
                    } catch (error) {
                        alert('Error: ' + error.message);
                    }
                }
            </script>
        </body>
        </html>
        """
    
    # Basic health check
    @app.route("/health")
    def health_check():
        return jsonify({
            "status": "healthy",
            "service": "VectorBid API",
            "version": "1.0.0"
        })
    
    # API status endpoint
    @app.route("/api/v1/status")
    def api_status():
        return jsonify({
            "api_status": "active",
            "framework": "Flask",
            "endpoints": [
                "/api/v1/pbs/generate",
                "/api/v1/personas",
                "/api/v1/bid-packets",
                "/api/v1/status"
            ]
        })
    
    # PBS generation endpoint
    @app.route("/api/v1/pbs/generate", methods=["POST"])
    def generate_pbs():
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "No JSON data provided"}), 400
            
            preferences = data.get('preferences', '')
            pilot_profile = data.get('pilot_profile', {})
            
            if not preferences:
                return jsonify({"error": "Preferences text is required"}), 400
            
            pbs_commands = generate_pbs_commands(preferences, pilot_profile)
            
            return jsonify({
                "success": True,
                "pbs_commands": pbs_commands,
                "preferences_processed": preferences,
                "pilot_profile": pilot_profile
            })
            
        except Exception as e:
            return jsonify({"error": f"PBS generation failed: {str(e)}"}), 500
    
    # Personas endpoint
    @app.route("/api/v1/personas")
    def get_personas():
        try:
            return jsonify({
                "success": True,
                "personas": PILOT_PERSONAS,
                "count": len(PILOT_PERSONAS)
            })
        except Exception as e:
            return jsonify({"error": f"Failed to retrieve personas: {str(e)}"}), 500
    
    # Bid packets endpoint
    @app.route("/api/v1/bid-packets")
    def get_bid_packets():
        try:
            airline = request.args.get('airline')
            manager = BidPacketManager()
            packets = manager.get_available_bid_packets(airline)
            
            return jsonify({
                "success": True,
                "bid_packets": packets,
                "count": len(packets),
                "filter_airline": airline
            })
        except Exception as e:
            return jsonify({"error": f"Failed to retrieve bid packets: {str(e)}"}), 500
    
    # Include existing FastAPI validation routes
    try:
        from app.compat.validate_router import compat_validate
        
        @app.route("/api/validate", methods=["POST"])
        def validate_wrapper():
            try:
                payload = request.get_json()
                result = compat_validate(payload)
                return jsonify(result)
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        print("✅ Validation endpoint registered!")
    except ImportError as e:
        print(f"⚠️ Validation endpoint not available: {e}")
    
    print("✅ VectorBid Flask API created successfully!")
    return app

# Create app instance for Gunicorn
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting VectorBid Flask API on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
