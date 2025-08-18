"""Admin blueprint for bid packet management."""

import os
import secrets
from functools import wraps

from flask import Blueprint, abort, jsonify, request

import src.lib.services.bids as services_bids

# Create admin blueprint
bp = Blueprint("admin", __name__, url_prefix="/admin")


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
    from io import BytesIO

    file_data = file.stream.read()
    file_stream = BytesIO(file_data)
    services_bids.save_bid_packet(month_tag, file_stream, file.filename or "upload.pdf")

    return jsonify({"status": "ok", "stored": month_tag})


@bp.route("/validate-bid/<month_tag>", methods=["GET"])
@require_bearer_token
def validate_bid_package(month_tag):
    """One-click bid package validation preview."""
    try:
        # Get bid package info
        bid_info = services_bids.get_bid_packet_info(month_tag)
        if not bid_info:
            return jsonify({"error": "Bid package not found"}), 404

        # Get file path and attempt to parse
        file_path = services_bids.get_bid_packet_path(month_tag)
        if not file_path:
            return jsonify({"error": "Bid package file not found"}), 404

        # Import parsing service
        from src.lib.schedule_parser import parse_schedule

        # Attempt to parse the bid package
        with open(file_path, "rb") as f:
            try:
                parsed_trips = parse_schedule(f.read(), file_path.name)

                validation_result = {
                    "status": "success",
                    "month_tag": month_tag,
                    "filename": bid_info.get("filename", "Unknown"),
                    "file_size": bid_info.get("file_size", 0),
                    "total_trips": len(parsed_trips) if parsed_trips else 0,
                    "sample_trips": parsed_trips[:5] if parsed_trips else [],
                    "parsing_successful": True,
                    "errors": [],
                    "warnings": [],
                }

                # Add validation warnings/info
                if not parsed_trips:
                    validation_result["warnings"].append(
                        "No trips found in bid package"
                    )
                elif len(parsed_trips) < 10:
                    validation_result["warnings"].append(
                        f"Only {len(parsed_trips)} trips found - this seems low for a monthly bid package"
                    )

                return jsonify(validation_result)

            except Exception as parse_error:
                return jsonify(
                    {
                        "status": "error",
                        "month_tag": month_tag,
                        "filename": bid_info.get("filename", "Unknown"),
                        "file_size": bid_info.get("file_size", 0),
                        "total_trips": 0,
                        "parsing_successful": False,
                        "errors": [f"Failed to parse bid package: {str(parse_error)}"],
                        "warnings": [],
                    }
                )

    except Exception as e:
        return jsonify({"error": f"Validation failed: {str(e)}"}), 500


@bp.route("/preview-bid/<month_tag>", methods=["GET"])
@require_bearer_token
def preview_bid_package(month_tag):
    """Generate HTML preview of bid package validation."""
    try:
        # Get validation data
        bid_info = services_bids.get_bid_packet_info(month_tag)
        if not bid_info:
            return "<h3>Bid package not found</h3>", 404

        file_path = services_bids.get_bid_packet_path(month_tag)
        if not file_path:
            return "<h3>Bid package file not found</h3>", 404

        from src.lib.schedule_parser import parse_schedule

        # Parse trips for preview
        with open(file_path, "rb") as f:
            try:
                parsed_trips = parse_schedule(f.read(), file_path.name)

                preview_html = f"""
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-file-pdf me-2"></i>{
                    bid_info.get("filename", "Unknown")
                }</h5>
                    </div>
                    <div class="card-body">
                        <div class="row mb-3">
                            <div class="col-md-4">
                                <strong>Month:</strong> {month_tag[:4]}-{month_tag[4:]}
                            </div>
                            <div class="col-md-4">
                                <strong>File Size:</strong> {
                    bid_info.get("file_size", 0) / 1024:.1f} KB
                            </div>
                            <div class="col-md-4">
                                <strong>Total Trips:</strong> {
                    len(parsed_trips) if parsed_trips else 0
                }
                            </div>
                        </div>

                        {
                    '<div class="alert alert-success"><i class="fas fa-check me-2"></i>Parsing successful!</div>'
                    if parsed_trips
                    else '<div class="alert alert-warning"><i class="fas fa-exclamation-triangle me-2"></i>No trips found</div>'
                }

                        {
                    f'''
                        <h6>Sample Trips (First 5):</h6>
                        <div class="table-responsive">
                            <table class="table table-sm table-dark">
                                <thead>
                                    <tr>
                                        <th>Trip ID</th>
                                        <th>Days</th>
                                        <th>Credit Hours</th>
                                        <th>Routing</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {"".join([f"<tr><td>{trip.get('trip_id', 'N/A')}</td><td>{trip.get('days', 'N/A')}</td><td>{trip.get('credit_hours', 'N/A')}</td><td>{trip.get('routing', 'N/A')}</td></tr>" for trip in parsed_trips[:5]])}
                                </tbody>
                            </table>
                        </div>
                        '''
                    if parsed_trips
                    else ""
                }
                    </div>
                </div>
                """

                return preview_html

            except Exception as parse_error:
                return f"""
                <div class="card">
                    <div class="card-header">
                        <h5 class="text-danger"><i class="fas fa-exclamation-triangle me-2"></i>{bid_info.get("filename", "Unknown")}</h5>
                    </div>
                    <div class="card-body">
                        <div class="alert alert-danger">
                            <strong>Parsing Error:</strong> {str(parse_error)}
                        </div>
                        <p><strong>File Size:</strong> {bid_info.get("file_size", 0) / 1024:.1f} KB</p>
                        <p><strong>Month:</strong> {month_tag[:4]}-{month_tag[4:]}</p>
                    </div>
                </div>
                """

    except Exception as e:
        return f"<div class='alert alert-danger'>Preview failed: {str(e)}</div>", 500


@bp.route("/", methods=["GET"])
@require_bearer_token
def admin_dashboard():
    """Admin dashboard for managing bid packets."""

    # Get list of existing bid packets
    bid_packets = services_bids.get_all_bid_packets()

    dashboard_html = f"""
    <!DOCTYPE html>
    <html lang="en" data-bs-theme="dark">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>VectorBid Admin Dashboard</title>
        <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-dark bg-dark">
            <div class="container">
                <span class="navbar-brand">
                    <i class="fas fa-cog me-2"></i>VectorBid Admin Dashboard
                </span>
            </div>
        </nav>

        <div class="container my-4">
            <div class="row">
                <div class="col-lg-8">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="card-title mb-0">
                                <i class="fas fa-upload me-2"></i>Upload Bid Package
                            </h5>
                        </div>
                        <div class="card-body">
                            <form id="uploadForm" enctype="multipart/form-data">
                                <div class="mb-3">
                                    <label for="month_tag" class="form-label">Month Tag (YYYYMM format)</label>
                                    <input type="text" class="form-control" id="month_tag" name="month_tag"
                                           placeholder="202508" pattern="[0-9]{{6}}" required>
                                    <div class="form-text">Enter 6-digit format: Year + Month (e.g., 202508 for August 2025)</div>
                                </div>
                                <div class="mb-3">
                                    <label for="file" class="form-label">Bid Package PDF</label>
                                    <input type="file" class="form-control" id="file" name="file"
                                           accept=".pdf" required>
                                </div>
                                <button type="submit" class="btn btn-primary">
                                    <i class="fas fa-cloud-upload-alt me-2"></i>Upload Bid Package
                                </button>
                            </form>

                            <div id="uploadStatus" class="mt-3" style="display: none;"></div>
                        </div>
                    </div>
                </div>

                <div class="col-lg-4">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="card-title mb-0">
                                <i class="fas fa-list me-2"></i>Existing Bid Packages
                            </h5>
                        </div>
                        <div class="card-body">
                            {format_bid_packet_list(bid_packets)}
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            document.getElementById('uploadForm').addEventListener('submit', async function(e) {{
                e.preventDefault();

                const formData = new FormData(this);
                const statusDiv = document.getElementById('uploadStatus');

                statusDiv.style.display = 'block';
                statusDiv.innerHTML = '<div class="alert alert-info"><i class="fas fa-spinner fa-spin me-2"></i>Uploading...</div>';

                try {{
                    const response = await fetch('/admin/upload-bid', {{
                        method: 'POST',
                        body: formData,
                        headers: {{
                            'Authorization': 'Bearer {os.environ.get("ADMIN_BEARER_TOKEN", "")}'
                        }}
                    }});

                    if (response.ok) {{
                        const result = await response.json();
                        statusDiv.innerHTML = '<div class="alert alert-success"><i class="fas fa-check me-2"></i>Successfully uploaded bid package: ' + result.stored + '</div>';
                        this.reset();

                        // Refresh page after 2 seconds to show new bid package
                        setTimeout(() => location.reload(), 2000);
                    }} else {{
                        statusDiv.innerHTML = '<div class="alert alert-danger"><i class="fas fa-exclamation-triangle me-2"></i>Upload failed: ' + response.status + '</div>';
                    }}
                }} catch (error) {{
                    statusDiv.innerHTML = '<div class="alert alert-danger"><i class="fas fa-exclamation-triangle me-2"></i>Upload error: ' + error.message + '</div>';
                }}
            }});
        </script>
    </body>
    </html>
    """

    return dashboard_html


def format_bid_packet_list(bid_packets):
    """Format bid packet list for display with validation buttons."""
    if not bid_packets:
        return '<p class="text-muted">No bid packages uploaded yet.</p>'

    html = '<div class="list-group list-group-flush">'
    for packet in bid_packets:
        # Format month tag for display
        month_tag = packet.get("month_tag", "")
        if len(month_tag) == 6:
            year = month_tag[:4]
            month = month_tag[4:]
            display_date = f"{month}/{year}"
        else:
            display_date = month_tag

        html += f"""
        <div class="list-group-item bg-dark border-secondary">
            <div class="d-flex w-100 justify-content-between align-items-start">
                <div class="flex-grow-1">
                    <h6 class="mb-1">{display_date}</h6>
                    <p class="mb-1 small text-muted">{packet.get("filename", "Unknown file")}</p>
                    <p class="mb-0 small text-info">{packet.get("file_size", 0) / 1024:.1f} KB</p>
                </div>
                <div class="text-end">
                    <small class="text-success d-block">Active</small>
                    <button class="btn btn-outline-primary btn-sm mt-1"
                            onclick="validateBidPackage('{month_tag}')"
                            data-month="{month_tag}">
                        <i class="fas fa-search me-1"></i>Preview
                    </button>
                </div>
            </div>
        </div>
        """
    html += "</div>"

    # Add preview modal and JavaScript
    html += (
        """
    <div class="modal fade" id="validationModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content bg-dark">
                <div class="modal-header">
                    <h5 class="modal-title">Bid Package Validation</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body" id="validationContent">
                    <div class="text-center">
                        <i class="fas fa-spinner fa-spin fa-2x"></i>
                        <p class="mt-2">Loading validation preview...</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        async function validateBidPackage(monthTag) {
            const modal = new bootstrap.Modal(document.getElementById('validationModal'));
            const content = document.getElementById('validationContent');

            // Show loading
            content.innerHTML = `
                <div class="text-center">
                    <i class="fas fa-spinner fa-spin fa-2x"></i>
                    <p class="mt-2">Validating bid package...</p>
                </div>
            `;
            modal.show();

            try {
                const response = await fetch(`/admin/preview-bid/${monthTag}`, {
                    headers: {
                        'Authorization': 'Bearer """
        + os.environ.get("ADMIN_BEARER_TOKEN", "")
        + """\''
                    }
                });

                if (response.ok) {
                    const html = await response.text();
                    content.innerHTML = html;
                } else {
                    content.innerHTML = `
                        <div class="alert alert-danger">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            Failed to validate bid package: ${response.status}
                        </div>
                    `;
                }
            } catch (error) {
                content.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Error: ${error.message}
                    </div>
                `;
            }
        }
    </script>
    """
    )

    return html
