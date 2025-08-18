"""
Flask API Adapter for VectorBid
Provides Flask-API compatible interfaces for existing VectorBid functionality
"""

from typing import Any

from flask import Blueprint, jsonify, request
from flask.views import MethodView

from src.lib.bid_packet_manager import BidPacketManager

# Import core VectorBid functionality
from src.lib.pbs_command_generator import generate_pbs_commands
from src.lib.personas import PILOT_PERSONAS

# Create Flask API blueprint
api_v1 = Blueprint("api_v1", __name__, url_prefix="/api/v1")


class PBSGeneratorAPI(MethodView):
    """Flask API endpoint for PBS command generation"""

    def post(self) -> dict[str, Any]:
        """Generate PBS commands from pilot preferences"""
        try:
            data = request.get_json()
            if not data:
                return {"error": "No JSON data provided"}, 400

            preferences = data.get("preferences", "")
            pilot_profile = data.get("pilot_profile", {})

            if not preferences:
                return {"error": "Preferences text is required"}, 400

            # Generate PBS commands
            pbs_commands = generate_pbs_commands(preferences, pilot_profile)

            return {
                "success": True,
                "pbs_commands": pbs_commands,
                "preferences_processed": preferences,
                "pilot_profile": pilot_profile,
            }

        except Exception as e:
            return {"error": f"PBS generation failed: {str(e)}"}, 500


class PersonasAPI(MethodView):
    """Flask API endpoint for pilot personas"""

    def get(self) -> dict[str, Any]:
        """Get available pilot personas"""
        try:
            return {
                "success": True,
                "personas": PILOT_PERSONAS,
                "count": len(PILOT_PERSONAS),
            }
        except Exception as e:
            return {"error": f"Failed to retrieve personas: {str(e)}"}, 500


class BidPacketsAPI(MethodView):
    """Flask API endpoint for bid packet management"""

    def __init__(self):
        self.manager = BidPacketManager()

    def get(self) -> dict[str, Any]:
        """Get available bid packets"""
        try:
            airline = request.args.get("airline")
            packets = self.manager.get_available_bid_packets(airline)

            return {
                "success": True,
                "bid_packets": packets,
                "count": len(packets),
                "filter_airline": airline,
            }
        except Exception as e:
            return {"error": f"Failed to retrieve bid packets: {str(e)}"}, 500

    def post(self) -> dict[str, Any]:
        """Upload new bid packet"""
        try:
            if "file" not in request.files:
                return {"error": "No file provided"}, 400

            file = request.files["file"]
            airline = request.form.get("airline", "")
            month_tag = request.form.get("month_tag", "")

            if not airline or not month_tag:
                return {"error": "airline and month_tag are required"}, 400

            # Upload bid packet
            result = self.manager.upload_bid_packet(file, month_tag, airline)

            if result.get("success"):
                return result, 201
            else:
                return result, 400

        except Exception as e:
            return {"error": f"Upload failed: {str(e)}"}, 500


class HealthCheckAPI(MethodView):
    """Flask API health check endpoint"""

    def get(self) -> dict[str, Any]:
        """Health check for API"""
        return {
            "status": "healthy",
            "service": "VectorBid API",
            "version": "1.0.0",
            "api_version": "v1",
        }


# Register API endpoints
api_v1.add_url_rule("/pbs/generate", view_func=PBSGeneratorAPI.as_view("pbs_generate"))

api_v1.add_url_rule("/personas", view_func=PersonasAPI.as_view("personas"))

api_v1.add_url_rule("/bid-packets", view_func=BidPacketsAPI.as_view("bid_packets"))

api_v1.add_url_rule("/health", view_func=HealthCheckAPI.as_view("health"))


# Additional utility endpoints
@api_v1.route("/status")
def api_status():
    """Simple API status endpoint"""
    return jsonify(
        {
            "api_status": "active",
            "endpoints": [
                "/api/v1/pbs/generate",
                "/api/v1/personas",
                "/api/v1/bid-packets",
                "/api/v1/health",
                "/api/v1/status",
            ],
        }
    )


@api_v1.errorhandler(404)
def not_found(error):
    """Handle 404 errors in API"""
    return jsonify({"error": "Endpoint not found"}), 404


@api_v1.errorhandler(500)
def internal_error(error):
    """Handle 500 errors in API"""
    return jsonify({"error": "Internal server error"}), 500


# Export the blueprint for registration
__all__ = ["api_v1"]
