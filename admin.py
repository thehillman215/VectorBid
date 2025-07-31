"""Admin blueprint for bid packet management."""
from flask import Blueprint, request, abort, jsonify
from functools import wraps
import secrets
import os
import services.bids

# Create admin blueprint
bp = Blueprint("admin", __name__, url_prefix="/admin")


def require_bearer_token(f):
    """Decorator to require valid Bearer token authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            abort(401)
        
        # Check for Bearer token format
        if not auth_header.startswith('Bearer '):
            abort(401)
        
        # Extract token
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        # Get expected token from environment
        expected_token = os.environ.get('ADMIN_BEARER_TOKEN')
        if not expected_token:
            abort(401)
        
        # Use secure comparison to prevent timing attacks
        if not secrets.compare_digest(token, expected_token):
            abort(401)
        
        return f(*args, **kwargs)
    return decorated_function


@bp.route("/upload-bid", methods=["POST"])
@require_bearer_token
def upload_bid():
    """Upload monthly bid packet PDF with Bearer token protection."""
    
    # Validate form data
    month_tag = request.form.get("month_tag")
    file = request.files.get("file")
    
    if not month_tag or not file:
        abort(400)
    
    # Validate month_tag format (6 digits YYYYMM with valid month)
    if not (month_tag.isdigit() and len(month_tag) == 6):
        abort(400)
    
    # Validate year and month ranges
    year = int(month_tag[:4])
    month = int(month_tag[4:])
    if year < 2000 or year > 2099 or month < 1 or month > 12:
        abort(400)
    
    # Save the bid packet
    bid_packet = services.bids.save_bid_packet(month_tag, file.stream, file.filename)
    
    return jsonify({"status": "ok", "stored": month_tag})