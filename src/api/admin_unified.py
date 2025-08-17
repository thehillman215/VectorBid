"""
Admin portal blueprint with templates, user management, and audit logging.
"""

import io
import io
import logging
import os
import re
import secrets
from collections import defaultdict
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional

from flask import current_app

from flask import (
    Blueprint,
<<<<<<< HEAD
    current_app,
||||||| 9ab61b0
=======
    abort,
>>>>>>> pr-18
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

from src.core.models import db, User, BidPacket, AdminActionLog


class AdminConfig:
    """Configuration for admin portal"""

    BEARER_TOKEN = os.environ.get("ADMIN_BEARER_TOKEN", "vb-admin-2025-secure-token")
    SESSION_LIFETIME_MINUTES = 60
    MAX_FILE_SIZE = 50 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"pdf", "PDF"}
    MAX_UPLOADS_PER_HOUR = 20


# Simple in-memory rate limiting store
upload_counters: defaultdict[str, list[datetime]] = defaultdict(list)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
logger = logging.getLogger(__name__)


def require_bearer_token(f):
    """Decorator for Bearer token authentication with session lifetime"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        session_token = session.get("admin_token")
        token = None

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
        elif session_token:
            token = session_token

        api_like = request.path.startswith("/admin/api/") or request.path.startswith("/admin/upload-bid")
        valid_tokens = get_valid_tokens()

        if not token:
            if api_like:
                return jsonify({"error": "No authorization token provided"}), 401
            return redirect(url_for("admin.login"))

        if not any(secrets.compare_digest(token, t) for t in valid_tokens):
            if api_like:
                return jsonify({"error": "Invalid token"}), 401
            session.pop("admin_token", None)
            return redirect(url_for("admin.login"))

        login_time = session.get("admin_login_time")
        if login_time:
            try:
                login_dt = datetime.fromisoformat(login_time)
                if datetime.utcnow() - login_dt > timedelta(minutes=AdminConfig.SESSION_LIFETIME_MINUTES):
                    session.pop("admin_token", None)
                    session.pop("admin_login_time", None)
                    if request.path.startswith("/admin/api/"):
                        return jsonify({"error": "Session expired"}), 401
                    return redirect(url_for("admin.login"))
            except Exception:
                pass

        return f(*args, **kwargs)

    return decorated_function


<<<<<<< HEAD
# ============================================
# RATE LIMITING UTILITIES
# ============================================

upload_counters = {}


def check_rate_limit():
    """Simple in-memory rate limiter for upload endpoints."""
    # During tests we don't want rate limits to interfere with results.
    if current_app.config.get('TESTING'):
        upload_counters.clear()
        return True

    client_ip = request.remote_addr or 'global'
    now = datetime.utcnow()
    hour_key = now.strftime('%Y%m%d%H')

    client_counts = upload_counters.setdefault(client_ip, {})
    count = client_counts.get(hour_key, 0)

    if count >= AdminConfig.MAX_UPLOADS_PER_HOUR:
        return False

    client_counts[hour_key] = count + 1

    # Remove counters for previous hours to prevent growth
    for key in list(client_counts.keys()):
        if key != hour_key:
            del client_counts[key]

    return True


# ============================================
# WEB UI ROUTES
# ============================================
||||||| 9ab61b0
# ============================================
# WEB UI ROUTES
# ============================================
=======
def log_action(action: str, target: str = "", admin_id: Optional[str] = None) -> None:
    try:
        entry = AdminActionLog(admin_id=admin_id, action=action, target=target)
        db.session.add(entry)
        db.session.commit()
    except Exception as exc:
        logger.error(f"Failed to log admin action: {exc}")
>>>>>>> pr-18


def validate_month_tag(month_tag: str) -> bool:
    if not re.fullmatch(r"\d{6}", month_tag or ""):
        return False
    year = int(month_tag[:4])
    month = int(month_tag[4:])
    return 2000 <= year <= 2099 and 1 <= month <= 12


def check_rate_limit(token: str) -> bool:
    now = datetime.utcnow()
    times = upload_counters[token]
    upload_counters[token] = [t for t in times if (now - t).total_seconds() < 3600]
    if len(upload_counters[token]) >= AdminConfig.MAX_UPLOADS_PER_HOUR:
        return False
    upload_counters[token].append(now)
    return True


def contracts_dir() -> str:
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    return os.path.join(project_root, "contracts")


def get_contracts() -> list[dict]:
    dir_path = contracts_dir()
    items: list[dict] = []
    if os.path.isdir(dir_path):
        for fname in os.listdir(dir_path):
            if fname.lower().endswith(".pdf"):
                path = os.path.join(dir_path, fname)
                stat = os.stat(path)
                items.append(
                    {
                        "filename": fname,
                        "size_mb": round(stat.st_size / 1024 / 1024, 2),
                        "upload_date": datetime.utcfromtimestamp(stat.st_mtime).isoformat(),
                    }
                )
    return items


def get_valid_tokens() -> set[str]:
    tokens = {current_app.config.get("ADMIN_BEARER_TOKEN", AdminConfig.BEARER_TOKEN)}
    env_token = os.environ.get("ADMIN_BEARER_TOKEN", "test-token")
    tokens.add(env_token)
    extra = current_app.config.get("ADMIN_BEARER_TOKENS") or os.environ.get("ADMIN_BEARER_TOKENS")
    if extra:
        tokens.update(t.strip() for t in extra.split(",") if t.strip())
    return tokens


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        data = request.get_json() if request.is_json else request.form
        token = data.get("token") if data else None
        valid_tokens = get_valid_tokens()
        if token and any(secrets.compare_digest(token, t) for t in valid_tokens):
            session["admin_token"] = token
            session["admin_login_time"] = datetime.utcnow().isoformat()
            log_action("login", admin_id=token)
            if request.is_json:
                return jsonify({"success": True, "redirect": url_for("admin.dashboard")})
            return redirect(url_for("admin.dashboard"))
        error = "Invalid token"
        if request.is_json:
            return jsonify({"success": False, "error": error}), 401
    return render_template("admin/login.html", error=error)


@admin_bp.route("/logout")
def logout():
    log_action("logout", admin_id=session.get("admin_token"))
    session.pop("admin_token", None)
    session.pop("admin_login_time", None)
    return redirect(url_for("admin.login"))


@admin_bp.route("/")
@admin_bp.route("/dashboard")
@require_bearer_token
def dashboard():
    packets = [
        {
            "airline": p.airline,
            "month_tag": p.month_tag,
            "filename": p.filename,
            "size_mb": round((p.file_size or 0) / 1024 / 1024, 2),
            "upload_date": p.upload_date.strftime("%Y-%m-%d"),
        }
        for p in BidPacket.query.order_by(BidPacket.upload_date.desc()).all()
    ]
    contracts = get_contracts()
    storage_mb = round(sum(p["size_mb"] for p in packets), 1)
    unique_airlines = len({p["airline"] for p in packets if p["airline"]})

    uploads_count = AdminActionLog.query.filter_by(action="upload_bid").count()
    deletes_count = AdminActionLog.query.filter_by(action="delete_bid").count()

    return render_template(
        "admin/dashboard.html",
        packets=packets,
        contracts=contracts,
        storage_mb=storage_mb,
        unique_airlines=unique_airlines,
        metrics={"uploads": uploads_count, "deletes": deletes_count},
        allowed_extensions=list(AdminConfig.ALLOWED_EXTENSIONS),
    )


@admin_bp.route("/users")
@require_bearer_token
def manage_users():
    users = User.query.order_by(User.email).all()
    return render_template("admin/users.html", users=users)


@admin_bp.route("/api/update-user/<user_id>", methods=["POST"])
@require_bearer_token
def api_update_user(user_id: str):
    user = User.query.get_or_404(user_id)
    role = request.form.get("role")
    active = request.form.get("is_active")
    if role:
        user.role = role
    if active is not None:
        user.is_active = active.lower() in {"true", "1", "yes", "on"}
    db.session.commit()
    log_action("update_user", user_id, session.get("admin_token"))
    return jsonify({"success": True})


@admin_bp.route("/logs")
@require_bearer_token
def view_logs():
    logs = (
        AdminActionLog.query.order_by(AdminActionLog.timestamp.desc())
        .limit(100)
        .all()
    )
    return render_template("admin/logs.html", logs=logs)


@admin_bp.route("/api/upload-bid-packet", methods=["POST"])
@require_bearer_token
def api_upload_bid_packet():
    token = session.get("admin_token") or request.headers.get("Authorization", "")[7:]
    if not check_rate_limit(token):
        return jsonify({"success": False, "error": "Rate limit exceeded"}), 429

    file = request.files.get("file")
    month_tag = request.form.get("month_tag")
    airline = request.form.get("airline")

    if not file:
        return jsonify({"success": False, "error": "No file provided"}), 400
    if not month_tag or not validate_month_tag(month_tag):
        return jsonify({"success": False, "error": "Invalid month_tag"}), 400
    if not airline:
        airline = ""

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in AdminConfig.ALLOWED_EXTENSIONS:
        return jsonify({"success": False, "error": "Invalid file type"}), 400

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > AdminConfig.MAX_FILE_SIZE:
        return jsonify({"success": False, "error": "File too large"}), 400

<<<<<<< HEAD
        if not month_tag:
            return jsonify({
                'success': False,
                'error': 'Month tag is required'
            }), 400

        if not airline:
            return jsonify({
                'success': False,
                'error': 'Airline is required'
            }), 400

        if not check_rate_limit():
            return jsonify({
                'success': False,
                'error': 'Rate limit exceeded'
            }), 429

        result = manager.upload_bid_packet(file, month_tag, airline)

        if result['success']:
            logger.info(f"Bid packet uploaded: {airline} {month_tag}")
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
||||||| 9ab61b0
        if not month_tag:
            return jsonify({
                'success': False,
                'error': 'Month tag is required'
            }), 400

        if not airline:
            return jsonify({
                'success': False,
                'error': 'Airline is required'
            }), 400

        result = manager.upload_bid_packet(file, month_tag, airline)

        if result['success']:
            logger.info(f"Bid packet uploaded: {airline} {month_tag}")
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
=======
    data = file.read()
    packet = BidPacket(
        month_tag=month_tag,
        filename=file.filename,
        airline=airline,
        pdf_data=data,
        file_size=size,
    )
    db.session.add(packet)
    db.session.commit()
    log_action("upload_bid", f"{airline}-{month_tag}", token)
    return jsonify({"success": True, "stored": month_tag})
>>>>>>> pr-18


<<<<<<< HEAD
@admin_bp.route('/api/upload-contract', methods=['POST'])
@require_bearer_token
def api_upload_contract():
    """API endpoint for contract upload"""

    if not BidPacketManager:
        return jsonify({
            'success': False,
            'error': 'BidPacketManager not available'
        }), 500

    try:
        manager = BidPacketManager()

        file = request.files.get('file')
        airline = request.form.get('airline')
        version = request.form.get('version')

        if not file:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400

        if not airline:
            return jsonify({
                'success': False,
                'error': 'Airline is required'
            }), 400

        if not check_rate_limit():
            return jsonify({
                'success': False,
                'error': 'Rate limit exceeded'
            }), 429

        result = manager.upload_contract(file, airline, version)

        if result['success']:
            logger.info(f"Contract uploaded: {airline}")
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Contract upload error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/delete-bid-packet/<month_tag>/<airline>',
                methods=['DELETE'])
@require_bearer_token
def api_delete_bid_packet(month_tag: str, airline: str):
    """API endpoint to delete bid packet"""

    if not BidPacketManager:
        return jsonify({
            'success': False,
            'error': 'BidPacketManager not available'
        }), 500

    try:
        manager = BidPacketManager()
        result = manager.delete_bid_packet(month_tag, airline)

        if result['success']:
            logger.info(f"Bid packet deleted: {airline} {month_tag}")
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Delete error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/download-bid-packet/<month_tag>/<airline>')
@require_bearer_token
def api_download_bid_packet(month_tag: str, airline: str):
    """API endpoint to download bid packet"""

    if not BidPacketManager:
        return jsonify({
            'success': False,
            'error': 'BidPacketManager not available'
        }), 500

    try:
        manager = BidPacketManager()
        file_data = manager.get_bid_packet_file(month_tag, airline)

        if file_data:
            from flask import Response
            data, filename = file_data
            return Response(data,
                            mimetype='application/pdf',
                            headers={
                                'Content-Disposition':
                                f'attachment; filename={filename}'
                            })
        else:
            return jsonify({'error': 'File not found'}), 404

    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/list-bid-packets')
@require_bearer_token
def api_list_bid_packets():
    """API endpoint to list all bid packets"""

    if not BidPacketManager:
        return jsonify({
            'success': False,
            'error': 'BidPacketManager not available'
        }), 500

    try:
        manager = BidPacketManager()
        packets = manager.get_available_bid_packets()
        return jsonify({
            'success': True,
            'packets': packets,
            'count': len(packets)
        }), 200

    except Exception as e:
        logger.error(f"List error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# LEGACY COMPATIBILITY
# ============================================


@admin_bp.route('/upload-bid', methods=['POST'])
||||||| 9ab61b0
@admin_bp.route('/api/upload-contract', methods=['POST'])
@require_bearer_token
def api_upload_contract():
    """API endpoint for contract upload"""

    if not BidPacketManager:
        return jsonify({
            'success': False,
            'error': 'BidPacketManager not available'
        }), 500

    try:
        manager = BidPacketManager()

        file = request.files.get('file')
        airline = request.form.get('airline')
        version = request.form.get('version')

        if not file:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400

        if not airline:
            return jsonify({
                'success': False,
                'error': 'Airline is required'
            }), 400

        result = manager.upload_contract(file, airline, version)

        if result['success']:
            logger.info(f"Contract uploaded: {airline}")
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Contract upload error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/delete-bid-packet/<month_tag>/<airline>',
                methods=['DELETE'])
@require_bearer_token
def api_delete_bid_packet(month_tag: str, airline: str):
    """API endpoint to delete bid packet"""

    if not BidPacketManager:
        return jsonify({
            'success': False,
            'error': 'BidPacketManager not available'
        }), 500

    try:
        manager = BidPacketManager()
        result = manager.delete_bid_packet(month_tag, airline)

        if result['success']:
            logger.info(f"Bid packet deleted: {airline} {month_tag}")
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Delete error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/download-bid-packet/<month_tag>/<airline>')
@require_bearer_token
def api_download_bid_packet(month_tag: str, airline: str):
    """API endpoint to download bid packet"""

    if not BidPacketManager:
        return jsonify({
            'success': False,
            'error': 'BidPacketManager not available'
        }), 500

    try:
        manager = BidPacketManager()
        file_data = manager.get_bid_packet_file(month_tag, airline)

        if file_data:
            from flask import Response
            data, filename = file_data
            return Response(data,
                            mimetype='application/pdf',
                            headers={
                                'Content-Disposition':
                                f'attachment; filename={filename}'
                            })
        else:
            return jsonify({'error': 'File not found'}), 404

    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/list-bid-packets')
@require_bearer_token
def api_list_bid_packets():
    """API endpoint to list all bid packets"""

    if not BidPacketManager:
        return jsonify({
            'success': False,
            'error': 'BidPacketManager not available'
        }), 500

    try:
        manager = BidPacketManager()
        packets = manager.get_available_bid_packets()
        return jsonify({
            'success': True,
            'packets': packets,
            'count': len(packets)
        }), 200

    except Exception as e:
        logger.error(f"List error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# LEGACY COMPATIBILITY
# ============================================


@admin_bp.route('/upload-bid', methods=['POST'])
=======
@admin_bp.route("/upload-bid", methods=["POST"])
>>>>>>> pr-18
@require_bearer_token
def legacy_upload_bid():
    resp = api_upload_bid_packet()
    status = resp[1] if isinstance(resp, tuple) else resp.status_code
    if status == 200:
        data = resp[0].get_json() if isinstance(resp, tuple) else resp.get_json()
        return jsonify({"status": "ok", "stored": data.get("stored")}), 200
    return resp


@admin_bp.route(
    "/api/delete-bid-packet/<month_tag>/<airline>", methods=["DELETE"]
)
@require_bearer_token
def api_delete_bid_packet(month_tag: str, airline: str):
    packet = BidPacket.query.filter_by(month_tag=month_tag, airline=airline).first()
    if not packet:
        return jsonify({"success": False, "error": "Packet not found"}), 404
    db.session.delete(packet)
    db.session.commit()
    log_action("delete_bid", f"{airline}-{month_tag}", session.get("admin_token"))
    return jsonify({"success": True})


@admin_bp.route(
    "/api/download-bid-packet/<month_tag>/<airline>", methods=["GET"]
)
@require_bearer_token
def api_download_bid_packet(month_tag: str, airline: str):
    packet = BidPacket.query.filter_by(month_tag=month_tag, airline=airline).first()
    if not packet:
        abort(404)
    return send_file(
        io.BytesIO(packet.pdf_data),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=packet.filename,
    )


@admin_bp.route("/api/upload-contract", methods=["POST"])
@require_bearer_token
def api_upload_contract():
    token = session.get("admin_token") or request.headers.get("Authorization", "")[7:]
    if not check_rate_limit(token):
        return jsonify({"success": False, "error": "Rate limit exceeded"}), 429

    file = request.files.get("file")
    airline = request.form.get("airline")
    version = request.form.get("version") or datetime.utcnow().strftime("%Y%m%d")

    if not file:
        return jsonify({"success": False, "error": "No file provided"}), 400
    if not airline:
        return jsonify({"success": False, "error": "Airline is required"}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in AdminConfig.ALLOWED_EXTENSIONS:
        return jsonify({"success": False, "error": "Invalid file type"}), 400

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > AdminConfig.MAX_FILE_SIZE:
        return jsonify({"success": False, "error": "File too large"}), 400

    os.makedirs(contracts_dir(), exist_ok=True)
    filename = f"contract_{airline}_{version}.pdf"
    file.save(os.path.join(contracts_dir(), filename))
    log_action("upload_contract", f"{airline}-{version}", token)
    return jsonify({"success": True})


@admin_bp.route("/api/list-contracts")
@require_bearer_token
def api_list_contracts():
    return jsonify({"success": True, "contracts": get_contracts()})


@admin_bp.route("/api/download-contract/<filename>")
@require_bearer_token
def api_download_contract(filename: str):
    path = os.path.join(contracts_dir(), filename)
    if not os.path.exists(path):
        abort(404)
    return send_file(path, as_attachment=True)


@admin_bp.route("/api/delete-contract/<filename>", methods=["DELETE"])
@require_bearer_token
def api_delete_contract(filename: str):
    path = os.path.join(contracts_dir(), filename)
    if not os.path.exists(path):
        return jsonify({"success": False, "error": "Not found"}), 404
    os.remove(path)
    log_action("delete_contract", filename, session.get("admin_token"))
    return jsonify({"success": True})


# Export blueprint
unified_admin = admin_bp
