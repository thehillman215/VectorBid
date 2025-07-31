"""Admin blueprint for bid packet management."""
from flask import Blueprint, request, abort, jsonify
import services.bids

# Create admin blueprint
bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/upload-bid", methods=["POST"])
def upload_bid():
    """Upload monthly bid packet PDF with token protection."""
    # Check token
    token = request.args.get("token")
    if token != "letmein":
        abort(403)
    
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
    services.bids.save_bid_packet(month_tag, file.stream)
    
    return jsonify({"status": "ok", "stored": month_tag})