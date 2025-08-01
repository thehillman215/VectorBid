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
    bid_packet = services.bids.save_bid_packet(month_tag, file.stream, file.filename or "upload.pdf")

    return jsonify({"status": "ok", "stored": month_tag})


@bp.route("/", methods=["GET"])
@require_bearer_token  
def admin_dashboard():
    """Admin dashboard for managing bid packets."""
    
    # Get list of existing bid packets
    bid_packets = services.bids.get_all_bid_packets()
    
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
    """Format bid packet list for display."""
    if not bid_packets:
        return '<p class="text-muted">No bid packages uploaded yet.</p>'
    
    html = '<div class="list-group list-group-flush">'
    for packet in bid_packets:
        # Format month tag for display
        month_tag = packet.get('month_tag', '')
        if len(month_tag) == 6:
            year = month_tag[:4]
            month = month_tag[4:]
            display_date = f"{month}/{year}"
        else:
            display_date = month_tag
            
        html += f'''
        <div class="list-group-item bg-dark border-secondary">
            <div class="d-flex w-100 justify-content-between">
                <h6 class="mb-1">{display_date}</h6>
                <small class="text-success">Active</small>
            </div>
            <p class="mb-1 small text-muted">{packet.get('filename', 'Unknown file')}</p>
        </div>
        '''
    html += '</div>'
    return html
