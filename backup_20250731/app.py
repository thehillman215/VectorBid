"""Enhanced admin blueprint with dashboard and improved bid package management."""

from flask import Blueprint, request, abort, jsonify, render_template, redirect, url_for
from functools import wraps
import secrets
import os
import logging
from datetime import datetime
from pathlib import Path

# Import our services
import services.bids
from schedule_parser import parse_schedule

# Create admin blueprint
bp = Blueprint("admin", __name__, url_prefix="/admin")

logger = logging.getLogger(__name__)


def require_bearer_token(f):
    """Decorator to require valid Bearer token authentication."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            abort(401)

        # Check for Bearer token format
        if not auth_header.startswith("Bearer "):
            abort(401)

        # Extract token
        token = auth_header[7:]  # Remove 'Bearer ' prefix

        # Get expected token from environment
        expected_token = os.environ.get("ADMIN_BEARER_TOKEN")
        if not expected_token:
            abort(401)

        # Use secure comparison to prevent timing attacks
        if not secrets.compare_digest(token, expected_token):
            abort(401)

        return f(*args, **kwargs)

    return decorated_function


def require_web_auth(f):
    """Decorator for web-based admin authentication (simpler for dashboard)."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # For demo purposes, check for admin token in session or query param
        admin_token = request.args.get('token') or request.form.get('token')
        expected_token = os.environ.get("ADMIN_BEARER_TOKEN", "letmein")

        if admin_token != expected_token:
            return render_template("admin_login.html"), 401

        return f(*args, **kwargs)

    return decorated_function


@bp.route("/")
@require_web_auth
def dashboard():
    """Admin dashboard for bid package management."""
    return render_template("admin_dashboard.html")


@bp.route("/login")
def login():
    """Simple admin login page."""
    return render_template("admin_login.html")


@bp.route("/upload-bid", methods=["POST"])
@require_bearer_token
def upload_bid():
    """Upload monthly bid packet PDF/CSV/TXT with Bearer token protection."""

    try:
        # Validate form data
        month_tag = request.form.get("month_tag")
        file = request.files.get("file")
        airline = request.form.get("airline", "Unknown")
        base = request.form.get("base", "")
        fleet = request.form.get("fleet", "")

        if not month_tag or not file:
            logger.warning("Upload attempt with missing month_tag or file")
            abort(400)

        # Validate month_tag format (6 digits YYYYMM with valid month)
        if not (month_tag.isdigit() and len(month_tag) == 6):
            logger.warning(f"Invalid month_tag format: {month_tag}")
            abort(400)

        # Validate year and month ranges
        year = int(month_tag[:4])
        month = int(month_tag[4:])
        if year < 2000 or year > 2099 or month < 1 or month > 12:
            logger.warning(f"Invalid year/month range: {year}/{month}")
            abort(400)

        # Validate file type
        filename = file.filename or "unknown"
        ext = Path(filename).suffix.lower()
        if ext not in {".pdf", ".csv", ".txt"}:
            logger.warning(f"Unsupported file type: {ext}")
            return jsonify({"error": f"Unsupported file type: {ext}"}), 400

        # Log upload attempt
        logger.info(
            f"Processing upload: {filename} for {month_tag} ({airline})")

        # Parse the schedule to validate and extract trip data
        file_bytes = file.read()
        file.seek(0)  # Reset file pointer for storage

        try:
            trips = parse_schedule(file_bytes, filename)
            trip_count = len(trips)
            logger.info(
                f"Successfully parsed {trip_count} trips from {filename}")
        except Exception as parse_error:
            logger.error(f"Failed to parse {filename}: {parse_error}")
            return jsonify({
                "error":
                f"Failed to parse schedule file: {str(parse_error)}"
            }), 400

        # Save the bid packet with metadata
        bid_packet_info = services.bids.save_bid_packet(
            month_tag=month_tag,
            file_stream=file.stream,
            filename=filename,
            metadata={
                "airline": airline,
                "base": base,
                "fleet": fleet,
                "trip_count": trip_count,
                "uploaded_at": datetime.utcnow().isoformat(),
                "file_size": len(file_bytes),
                "file_type": ext
            })

        logger.info(f"Successfully stored bid packet {month_tag}")

        return jsonify({
            "status": "ok",
            "stored": month_tag,
            "trip_count": trip_count,
            "airline": airline,
            "file_type": ext,
            "file_size": len(file_bytes)
        })

    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route("/packages", methods=["GET"])
@require_bearer_token
def list_packages():
    """List all uploaded bid packages with metadata."""

    try:
        packages = services.bids.list_bid_packages()
        return jsonify({"packages": packages, "total": len(packages)})
    except Exception as e:
        logger.error(f"Error listing packages: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route("/packages/<month_tag>", methods=["GET"])
@require_bearer_token
def get_package_details(month_tag):
    """Get detailed information about a specific bid package."""

    try:
        package_info = services.bids.get_bid_package_info(month_tag)
        if not package_info:
            abort(404)

        return jsonify(package_info)
    except Exception as e:
        logger.error(f"Error getting package {month_tag}: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route("/packages/<month_tag>", methods=["DELETE"])
@require_bearer_token
def delete_package(month_tag):
    """Delete a bid package."""

    try:
        success = services.bids.delete_bid_package(month_tag)
        if not success:
            abort(404)

        logger.info(f"Deleted bid package {month_tag}")
        return jsonify({"status": "deleted", "month_tag": month_tag})
    except Exception as e:
        logger.error(f"Error deleting package {month_tag}: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route("/stats", methods=["GET"])
@require_bearer_token
def get_stats():
    """Get admin dashboard statistics."""

    try:
        stats = services.bids.get_admin_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route("/test-parser", methods=["POST"])
@require_bearer_token
def test_parser():
    """Test the schedule parser with a sample file."""

    try:
        file = request.files.get("file")
        if not file:
            abort(400)

        filename = file.filename or "test.txt"
        file_bytes = file.read()

        # Test parsing
        trips = parse_schedule(file_bytes, filename)

        # Return first few trips as sample
        sample_trips = trips[:5] if len(trips) > 5 else trips

        return jsonify({
            "status": "success",
            "total_trips": len(trips),
            "sample_trips": sample_trips,
            "parser_type": Path(filename).suffix.lower()
        })

    except Exception as e:
        logger.error(f"Parser test error: {e}")
        return jsonify({"status": "error", "error": str(e)}), 400


@bp.route("/logs", methods=["GET"])
@require_bearer_token
def get_logs():
    """Get recent system logs."""

    try:
        # This would read from actual log files in production
        # For now, return sample log data
        logs = [{
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO",
            "message": "System running normally",
            "module": "admin"
        }]

        return jsonify({"logs": logs})
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        return jsonify({"error": str(e)}), 500


# Error handlers for admin blueprint
@bp.errorhandler(401)
def unauthorized(error):
    """Handle unauthorized access."""
    if request.headers.get('Content-Type') == 'application/json':
        return jsonify({"error": "Unauthorized"}), 401
    return render_template("admin_login.html"), 401


@bp.errorhandler(404)
def not_found(error):
    """Handle not found errors."""
    return jsonify({"error": "Not found"}), 404


@bp.errorhandler(500)
def internal_error(error):
    """Handle internal server errors."""
    logger.error(f"Internal error: {error}")
    return jsonify({"error": "Internal server error"}), 500
