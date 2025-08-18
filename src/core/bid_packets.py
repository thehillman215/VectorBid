from __future__ import annotations

"""Utility helpers for managing bid packet files and metadata."""

import json
from datetime import datetime
from pathlib import Path

# Directories for storing bid packets and metadata
BIDS_DIR = Path("bids")
METADATA_DIR = BIDS_DIR / "metadata"


def get_bid_packet_info(month_tag: str) -> dict | None:
    """Return metadata for the given month tag if it exists."""
    meta_file = METADATA_DIR / f"{month_tag}.json"
    if meta_file.exists():
        with open(meta_file, encoding="utf-8") as f:
            return json.load(f)
    return None


def save_bid_packet(file_storage, month_tag: str) -> dict:
    """Persist an uploaded PDF bid packet and its metadata.

    Args:
        file_storage: Werkzeug ``FileStorage`` instance representing the
            uploaded file.
        month_tag: Tag in ``YYYYMM`` format.

    Returns:
        Dict of stored metadata for the packet.
    """
    # Ensure directories exist
    BIDS_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    filename = file_storage.filename or f"{month_tag}.pdf"
    if not filename.lower().endswith(".pdf"):
        raise ValueError("Only PDF files are allowed")

    file_path = BIDS_DIR / f"{month_tag}.pdf"
    file_storage.save(file_path)

    metadata = {
        "month_tag": month_tag,
        "filename": filename,
        "file_path": str(file_path),
        "file_size": file_path.stat().st_size,
        "created_at": datetime.utcnow().isoformat(),
        "file_type": ".pdf",
    }

    meta_file = METADATA_DIR / f"{month_tag}.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return metadata
