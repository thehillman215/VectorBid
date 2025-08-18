# vectorbid_pbs_integration.py
"""
Integration layer for VectorBid to use Enhanced PBS Generation
This replaces the simple natural_language_to_pbs_filters with comprehensive system
"""

from typing import List, Dict, Any, Optional
from flask import (
    session,
    request,
    jsonify,
    make_response,
    flash,
    redirect,
    url_for,
    render_template,
)
from datetime import datetime
import logging

# Import our enhanced systems
from enhanced_pbs_generator import (
    EnhancedPBSGenerator,
    PBSCommand,
    CommandType,
    Priority,
)
from enhanced_bid_layers_system import Enhanced50LayerSystem

logger = logging.getLogger(__name__)


class VectorBidPBSService:
    """
    Service class that provides PBS functionality to VectorBid routes
    """

    def __init__(self):
        self.generator = EnhancedPBSGenerator()

    def process_pilot_preferences(
        self,
        preferences: str,
        user_id: str = None,
        pilot_profile: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Main entry point for processing pilot preferences
        Replaces the old natural_language_to_pbs_filters function
        """
        try:
            # Create 50-layer system for this user
            bid_system = Enhanced50LayerSystem(user_id=user_id)

            # Set pilot profile if available
            if pilot_profile:
                bid_system.set_pilot_profile(pilot_profile)
                logger.info(
                    f"Set pilot profile for user {user_id}: {pilot_profile.get('base', 'Unknown base')}"
                )

            # Generate layers from preferences
            num_layers = bid_system.generate_layers_from_preferences(preferences)
            logger.info(f"Generated {num_layers} layers for user {user_id}")

            # Generate comprehensive outputs
            pbs_output = bid_system.generate_final_pbs_output(include_explanations=True)
            simple_pbs_output = bid_system.generate_final_pbs_output(
                include_explanations=False
            )

            # Extract simple commands for backward compatibility
            simple_commands = []
            detailed_layers = []

            for layer in bid_system.get_active_layers():
                layer_info = {
                    "layer_number": layer.layer_number,
                    "name": layer.name,
                    "description": layer.description,
                    "priority": layer.priority.name,
                    "commands": [],
                }

                for cmd in layer.commands:
                    simple_commands.append(cmd.to_pbs_string())
                    layer_info["commands"].append(
                        {
                            "pbs_string": cmd.to_pbs_string(),
                            "explanation": cmd.explanation,
                            "command_type": cmd.command_type.value,
                        }
                    )

                detailed_layers.append(layer_info)

            # Get strategy statistics and validation
            stats = bid_system.get_layer_statistics()
            issues = bid_system.validate_strategy()

            # Store in session for later use
            session_data = {
                "layers": detailed_layers,
                "pbs_output_detailed": pbs_output,
                "pbs_output_clean": simple_pbs_output,
                "statistics": stats,
                "validation_issues": issues,
                "preferences": preferences,
                "generated_at": datetime.now().isoformat(),
            }

            return {
                "success": True,
                "layers": num_layers,
                "commands": simple_commands,  # For backward compatibility
                "pbs_output": simple_pbs_output,  # Clean version for copy-paste
                "pbs_output_detailed": pbs_output,  # Version with explanations
                "detailed_layers": detailed_layers,
                "statistics": stats,
                "validation_issues": issues,
                "session_data": session_data,
                "bid_system": bid_system,  # For advanced manipulation
            }

        except Exception as e:
            logger.error(f"Error processing preferences for user {user_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "commands": [],
                "pbs_output": f"Error generating PBS commands: {str(e)}",
            }

    def get_pilot_profile_from_session(self) -> Dict[str, Any]:
        """Extract pilot profile from current session/user data"""
        # This would integrate with your existing user profile system
        profile = {}

        # Try to get from session first
        if "user_profile" in session:
            profile = session["user_profile"]

        # Add any additional profile data from your user management system
        # This is where you'd integrate with get_profile() or similar functions

        return profile

    def create_pbs_download_file(
        self, pbs_output: str, filename_prefix: str = "vectorbid_pbs"
    ) -> str:
        """Create downloadable PBS file content"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        file_content = f"""VectorBid Generated PBS Commands
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
File: {filename_prefix}_{timestamp}.txt

{"=" * 60}

{pbs_output}

{"=" * 60}
VectorBid - AI-Powered Pilot Schedule Optimization
For questions or support, contact: support@vectorbid.com

DISCLAIMER: Always review generated commands against actual
bid packet data before submitting to your airline's PBS system.
VectorBid is not responsible for bid results.
"""
        return file_content


# Updated route functions for VectorBid


def enhanced_natural_language_to_pbs_filters(
    preferences_text: str, trip_data: Optional[List[Dict]] = None
) -> List[str]:
    """
    Enhanced replacement for the original natural_language_to_pbs_filters function
    Maintains backward compatibility while providing enhanced functionality
    """
    service = VectorBidPBSService()

    # Get pilot profile from session/user system
    pilot_profile = service.get_pilot_profile_from_session()

    # Process preferences
    result = service.process_pilot_preferences(
        preferences=preferences_text,
        user_id=session.get("user_id"),
        pilot_profile=pilot_profile,
    )

    if result["success"]:
        # Store enhanced data in session for results page
        session["enhanced_pbs_data"] = result["session_data"]
        return result["commands"]  # Return simple commands for backward compatibility
    else:
        logger.error(f"PBS generation failed: {result.get('error', 'Unknown error')}")
        return [f"# Error: {result.get('error', 'Failed to generate PBS commands')}"]


def enhanced_results_route():
    """
    Enhanced results route that shows PBS commands instead of trip rankings
    This replaces the current results() function
    """
    try:
        user_id = session.get("user_id", "44040350")  # Fallback for testing

        # Check if we have enhanced PBS data from recent analysis
        if "enhanced_pbs_data" in session:
            pbs_data = session["enhanced_pbs_data"]

            return render_template(
                "enhanced_pbs_results.html",
                pbs_output=pbs_data["pbs_output_clean"],
                pbs_output_detailed=pbs_data["pbs_output_detailed"],
                layers=pbs_data["layers"],
                statistics=pbs_data["statistics"],
                validation_issues=pbs_data["validation_issues"],
                preferences=pbs_data["preferences"],
                generated_at=pbs_data["generated_at"],
            )

        # Fallback: Check for trip analysis data and generate PBS
        elif "trip_analysis" in session and "ranked_trips" in session:
            trip_analysis = session["trip_analysis"]
            preferences = trip_analysis.get("preferences", "")

            # Generate PBS using enhanced system
            service = VectorBidPBSService()
            pilot_profile = service.get_pilot_profile_from_session()

            result = service.process_pilot_preferences(
                preferences=preferences, user_id=user_id, pilot_profile=pilot_profile
            )

            if result["success"]:
                # Store for download functionality
                session["enhanced_pbs_data"] = result["session_data"]

                return render_template(
                    "enhanced_pbs_results.html",
                    pbs_output=result["pbs_output"],
                    pbs_output_detailed=result["pbs_output_detailed"],
                    layers=result["detailed_layers"],
                    statistics=result["statistics"],
                    validation_issues=result["validation_issues"],
                    preferences=preferences,
                    generated_at=datetime.now().isoformat(),
                )
            else:
                flash(
                    f"Error generating PBS commands: {result.get('error', 'Unknown error')}",
                    "error",
                )

        # Final fallback: Show sample/demo data
        flash("No analysis data found. Showing sample PBS strategy.", "info")
        return render_template(
            "enhanced_pbs_results.html",
            pbs_output=_get_sample_pbs_output(),
            pbs_output_detailed=_get_sample_pbs_output(detailed=True),
            layers=_get_sample_layers(),
            statistics={"total_layers": 3, "total_commands": 8},
            validation_issues=[],
            preferences="Sample preferences for demonstration",
            generated_at=datetime.now().isoformat(),
        )

    except Exception as e:
        logger.error(f"Error in enhanced results route: {str(e)}")
        flash("Error displaying PBS results. Please try again.", "error")
        return redirect(url_for("main.index"))


def enhanced_download_pbs_filters():
    """
    Enhanced download function for PBS filters
    Replaces the current download_pbs_filters route
    """
    try:
        user_id = session.get("user_id")
        if not user_id:
            flash("Please log in to download filters", "error")
            return redirect(url_for("replit_auth.login"))

        # Get PBS data from session
        if "enhanced_pbs_data" not in session:
            flash("No PBS data found. Please run an analysis first.", "error")
            return redirect(url_for("main.index"))

        pbs_data = session["enhanced_pbs_data"]

        # Create downloadable file
        service = VectorBidPBSService()
        file_content = service.create_pbs_download_file(
            pbs_output=pbs_data["pbs_output_clean"],
            filename_prefix="vectorbid_50layer_strategy",
        )

        # Create download response
        response = make_response(file_content)
        response.headers["Content-Type"] = "text/plain; charset=utf-8"
        response.headers["Content-Disposition"] = (
            f"attachment; filename=vectorbid_50layer_pbs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )

        return response

    except Exception as e:
        logger.error(f"PBS filter download error: {e}")
        flash("Error generating PBS download file", "error")
        return redirect(url_for("main.index"))


def enhanced_preview_pbs_filters():
    """
    Enhanced PBS filter preview endpoint
    """
    try:
        data = request.get_json()
        preferences = data.get("preferences", "")

        if not preferences:
            return jsonify({"error": "No preferences provided"}), 400

        # Process preferences with enhanced system
        service = VectorBidPBSService()
        pilot_profile = service.get_pilot_profile_from_session()

        result = service.process_pilot_preferences(
            preferences=preferences,
            user_id=session.get("user_id"),
            pilot_profile=pilot_profile,
        )

        if result["success"]:
            return jsonify(
                {
                    "success": True,
                    "filters": result["commands"],
                    "layers": result["layers"],
                    "pbs_output": result["pbs_output"],
                    "statistics": result["statistics"],
                    "validation_issues": result["validation_issues"],
                    "preview": True,
                }
            )
        else:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": result.get("error", "Failed to generate preview"),
                        "filters": [],
                    }
                ),
                500,
            )

    except Exception as e:
        logger.error(f"PBS filter preview error: {e}")
        return jsonify({"error": "Failed to generate preview"}), 500


# Helper functions for fallback/demo data


def _get_sample_pbs_output(detailed: bool = False) -> str:
    """Generate sample PBS output for demo purposes"""
    sample = """VectorBid 50-Layer PBS Strategy
Generated: 2025-08-02 14:30:00
Active Layers: 3 of 3
==================================================

LAYER  1: Critical Constraints
  PREFER LINE OVER RESERVE

LAYER  2: Weekend Strategy  
  AVOID TRIPS IF DUTY_PERIOD OVERLAPS WEEKEND

LAYER  3: Timing Preferences
  AVOID TRIPS STARTING BEFORE 0800

==================================================
SUMMARY:
Total Commands: 3
Priority Breakdown:
  CRITICAL: 1 commands
  HIGH: 2 commands

USAGE INSTRUCTIONS:
1. Copy the commands above (Layer by Layer)
2. Log into your airline's PBS system
3. Enter commands in layer order (1, 2, 3...)
4. Review and adjust based on current bid packets
5. Submit your bid before deadline

⚠️  IMPORTANT: Always review commands against actual
   trip data before submitting your bid!"""

    if detailed:
        return (
            sample.replace(
                "PREFER LINE OVER RESERVE",
                "PREFER LINE OVER RESERVE\n    # Strongly prefers any line over reserve duty",
            )
            .replace(
                "AVOID TRIPS IF DUTY_PERIOD OVERLAPS WEEKEND",
                "AVOID TRIPS IF DUTY_PERIOD OVERLAPS WEEKEND\n    # Avoids working on weekends for better work-life balance",
            )
            .replace(
                "AVOID TRIPS STARTING BEFORE 0800",
                "AVOID TRIPS STARTING BEFORE 0800\n    # Avoids early morning departures",
            )
        )

    return sample


def _get_sample_layers() -> List[Dict[str, Any]]:
    """Generate sample layer data for demo"""
    return [
        {
            "layer_number": 1,
            "name": "Critical Constraints",
            "description": "Must-have requirements",
            "priority": "CRITICAL",
            "commands": [
                {
                    "pbs_string": "PREFER LINE OVER RESERVE",
                    "explanation": "Strongly prefers any line over reserve duty",
                    "command_type": "PREFER",
                }
            ],
        },
        {
            "layer_number": 2,
            "name": "Weekend Strategy",
            "description": "Weekend work preferences",
            "priority": "HIGH",
            "commands": [
                {
                    "pbs_string": "AVOID TRIPS IF DUTY_PERIOD OVERLAPS WEEKEND",
                    "explanation": "Avoids working on weekends for better work-life balance",
                    "command_type": "AVOID",
                }
            ],
        },
        {
            "layer_number": 3,
            "name": "Timing Preferences",
            "description": "Departure time preferences",
            "priority": "HIGH",
            "commands": [
                {
                    "pbs_string": "AVOID TRIPS STARTING BEFORE 0800",
                    "explanation": "Avoids early morning departures",
                    "command_type": "AVOID",
                }
            ],
        },
    ]


# Route registration helper


def register_enhanced_pbs_routes(app):
    """
    Register enhanced PBS routes with Flask app
    This shows how to integrate with existing VectorBid routing
    """

    # Replace existing routes with enhanced versions
    @app.route("/results")
    def results():
        return enhanced_results_route()

    @app.route("/download_pbs_filters")
    def download_pbs_filters():
        return enhanced_download_pbs_filters()

    @app.route("/preview_pbs_filters", methods=["POST"])
    def preview_pbs_filters():
        return enhanced_preview_pbs_filters()

    # New routes for 50-layer system management
    @app.route("/api/pbs/layers", methods=["GET"])
    def get_pbs_layers():
        """Get current layers for the user"""
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Not logged in"}), 401

        if "enhanced_pbs_data" in session:
            return jsonify(
                {"success": True, "layers": session["enhanced_pbs_data"]["layers"]}
            )
        else:
            return jsonify({"success": True, "layers": []})

    @app.route("/api/pbs/statistics", methods=["GET"])
    def get_pbs_statistics():
        """Get PBS strategy statistics"""
        if "enhanced_pbs_data" in session:
            return jsonify(
                {
                    "success": True,
                    "statistics": session["enhanced_pbs_data"]["statistics"],
                }
            )
        else:
            return jsonify({"success": False, "error": "No PBS data found"})

    @app.route("/bid-layers")
    def bid_layers_ui():
        """Enhanced bid layers management UI"""
        user_id = session.get("user_id")
        if not user_id:
            return redirect(url_for("replit_auth.login"))

        # Get current PBS data
        layers = []
        if "enhanced_pbs_data" in session:
            layers = session["enhanced_pbs_data"]["layers"]

        return render_template(
            "enhanced_bid_layers.html", layers=layers, user_id=user_id
        )


# Integration instructions for VectorBid


def integrate_enhanced_pbs_system():
    """
    Instructions for integrating this enhanced PBS system into VectorBid

    1. Add the enhanced modules to src/lib/:
       - enhanced_pbs_generator.py
       - enhanced_bid_layers_system.py
       - vectorbid_pbs_integration.py (this file)

    2. Update src/api/routes.py:
       - Replace natural_language_to_pbs_filters with enhanced_natural_language_to_pbs_filters
       - Replace results() function with enhanced_results_route()
       - Replace download_pbs_filters() with enhanced_download_pbs_filters()

    3. Create new template: src/ui/templates/enhanced_pbs_results.html
       - Shows PBS commands instead of trip rankings
       - Includes layer breakdown, statistics, validation issues
       - Copy-to-clipboard functionality
       - Download options

    4. Update existing templates:
       - Add PBS preview functionality to preference input forms
       - Add layer management UI

    5. Test the integration:
       - Verify PBS command generation works
       - Test all download/preview functionality
       - Ensure backward compatibility
    """
    pass


if __name__ == "__main__":
    # Test the enhanced system
    service = VectorBidPBSService()

    test_preferences = """
    I'm a commuter from Denver flying 737s out of IAH. 
    I need weekends off, no early departures, and I want to avoid reserve.
    I prefer short trips and need to be home for my anniversary on the 15th.
    """

    result = service.process_pilot_preferences(
        preferences=test_preferences,
        user_id="test_pilot",
        pilot_profile={
            "base": "IAH",
            "fleet": ["737"],
            "is_commuter": True,
            "home_airport": "DEN",
        },
    )

    if result["success"]:
        print("✅ Enhanced PBS Generation Successful!")
        print(f"Generated {result['layers']} layers")
        print(f"Total commands: {len(result['commands'])}")
        print("\nPBS Output Preview:")
        print("=" * 50)
        print(result["pbs_output"][:500] + "...")

        if result["validation_issues"]:
            print(f"\n⚠️  Validation Issues: {len(result['validation_issues'])}")
            for issue in result["validation_issues"]:
                print(f"  - {issue}")
    else:
        print("❌ PBS Generation Failed:")
        print(result.get("error", "Unknown error"))
