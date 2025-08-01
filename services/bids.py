"""Enhanced bid packet storage service with metadata support."""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any, BinaryIO

logger = logging.getLogger(__name__)

# Storage directories
BIDS_DIR = Path("bids")
METADATA_DIR = BIDS_DIR / "metadata"

# Ensure directories exist
BIDS_DIR.mkdir(exist_ok=True)
METADATA_DIR.mkdir(exist_ok=True)


def save_bid_packet(month_tag: str,
                    file_stream: BinaryIO,
                    filename: Optional[str] = None,
                    metadata: Optional[Dict] = None) -> Dict:
    """Save a bid packet file with metadata.

    Args:
        month_tag: Six-digit YYYYMM format
        file_stream: File stream to save
        filename: Original filename
        metadata: Additional metadata to store

    Returns:
        Dict with save information
    """
    try:
        # Validate month_tag
        if not (len(month_tag) == 6 and month_tag.isdigit()):
            raise ValueError("month_tag must be YYYYMM format")

        # Determine file extension
        if filename:
            ext = Path(filename).suffix.lower()
        else:
            ext = ".pdf"  # Default

        # Create file path
        file_path = BIDS_DIR / f"{month_tag}{ext}"
        metadata_path = METADATA_DIR / f"{month_tag}.json"

        # Save the file
        with open(file_path, 'wb') as f:
            file_stream.seek(0)
            f.write(file_stream.read())

        # Prepare metadata
        file_metadata = {
            "month_tag": month_tag,
            "filename": filename or f"{month_tag}{ext}",
            "file_path": str(file_path),
            "file_size": file_path.stat().st_size,
            "created_at": datetime.utcnow().isoformat(),
            "file_type": ext,
            **(metadata or {})
        }

        # Save metadata
        with open(metadata_path, 'w') as f:
            json.dump(file_metadata, f, indent=2)

        logger.info(f"Saved bid packet {month_tag} to {file_path}")
        return file_metadata

    except Exception as e:
        logger.error(f"Failed to save bid packet {month_tag}: {e}")
        raise


def get_bid_packet_path(month_tag: str) -> Optional[Path]:
    """Get the file path for a bid packet.

    Args:
        month_tag: Six-digit YYYYMM format

    Returns:
        Path to the file if it exists, None otherwise
    """
    for ext in ['.pdf', '.csv', '.txt']:
        file_path = BIDS_DIR / f"{month_tag}{ext}"
        if file_path.exists():
            return file_path
    return None


def get_bid_packet_info(month_tag: str) -> Optional[Dict]:
    """Get metadata for a bid packet.

    Args:
        month_tag: Six-digit YYYYMM format

    Returns:
        Metadata dict if found, None otherwise
    """
    metadata_path = METADATA_DIR / f"{month_tag}.json"

    if not metadata_path.exists():
        return None

    try:
        with open(metadata_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to read metadata for {month_tag}: {e}")
        return None


def list_bid_packages() -> List[Dict]:
    """List all available bid packages with metadata.

    Returns:
        List of metadata dicts
    """
    packages = []

    for metadata_file in METADATA_DIR.glob("*.json"):
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                packages.append(metadata)
        except Exception as e:
            logger.error(f"Failed to read metadata from {metadata_file}: {e}")
            continue

    # Sort by month_tag (newest first)
    packages.sort(key=lambda x: x.get('month_tag', ''), reverse=True)
    return packages


def get_all_bid_packets() -> List[Dict]:
    """Alias for list_bid_packages for backward compatibility."""
    return list_bid_packages()


def delete_bid_package(month_tag: str) -> bool:
    """Delete a bid package and its metadata.

    Args:
        month_tag: Six-digit YYYYMM format

    Returns:
        True if deleted, False if not found
    """
    try:
        # Find and delete the file
        file_path = get_bid_packet_path(month_tag)
        if file_path and file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted bid packet file: {file_path}")

        # Delete metadata
        metadata_path = METADATA_DIR / f"{month_tag}.json"
        if metadata_path.exists():
            metadata_path.unlink()
            logger.info(f"Deleted metadata: {metadata_path}")

        return True

    except Exception as e:
        logger.error(f"Failed to delete bid packet {month_tag}: {e}")
        return False


def get_matching_bid_packet(profile: Dict) -> Optional[Dict]:
    """Find the best matching bid packet for a pilot's profile.

    Args:
        profile: Pilot profile with airline, base, fleet, etc.

    Returns:
        Matching bid packet metadata or None
    """
    packages = list_bid_packages()

    # Get current month as fallback
    current_month = datetime.now().strftime("%Y%m")

    # Filter and score packages
    scored_packages = []

    for package in packages:
        score = 0

        # Prefer current month
        if package.get('month_tag') == current_month:
            score += 100

        # Match airline
        if package.get('airline') == profile.get('airline'):
            score += 50

        # Match base (if specified in package)
        package_base = package.get('base', '').upper()
        profile_base = profile.get('base', '').upper()
        if package_base and package_base == profile_base:
            score += 30
        elif not package_base:  # Package applies to all bases
            score += 10

        # Match fleet (if specified in package)
        package_fleet = package.get('fleet', '')
        profile_fleet = profile.get('fleet', [])
        if package_fleet and package_fleet in profile_fleet:
            score += 20
        elif not package_fleet:  # Package applies to all fleets
            score += 5

        if score > 0:
            scored_packages.append((score, package))

    # Return highest scoring package
    if scored_packages:
        scored_packages.sort(key=lambda x: x[0], reverse=True)
        return scored_packages[0][1]

    return None


def get_admin_stats() -> Dict:
    """Get statistics for the admin dashboard.

    Returns:
        Dict with various statistics
    """
    try:
        packages = list_bid_packages()
        current_month = datetime.now().strftime("%Y%m")

        # Calculate stats
        total_packages = len(packages)
        active_packages = len(
            [p for p in packages if p.get('month_tag') >= current_month])
        total_trips = sum(p.get('trip_count', 0) for p in packages)

        # File size stats
        total_size = sum(p.get('file_size', 0) for p in packages)

        # Recent activity (packages uploaded in last 30 days)
        cutoff_date = datetime.now().timestamp() - (30 * 24 * 60 * 60)
        recent_packages = [
            p for p in packages if datetime.fromisoformat(
                p.get('created_at', '1970-01-01')).timestamp() > cutoff_date
        ]

        return {
            "total_packages": total_packages,
            "active_packages": active_packages,
            "total_trips": total_trips,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "recent_uploads": len(recent_packages),
            "airlines":
            list(set(p.get('airline', 'Unknown') for p in packages)),
            "latest_month": packages[0].get('month_tag') if packages else None,
            "active_pilots": 0,  # This would come from user database
        }

    except Exception as e:
        logger.error(f"Failed to get admin stats: {e}")
        return {
            "total_packages": 0,
            "active_packages": 0,
            "total_trips": 0,
            "total_size_mb": 0,
            "recent_uploads": 0,
            "airlines": [],
            "latest_month": None,
            "active_pilots": 0,
        }


def cleanup_old_packages(days_old: int = 365) -> int:
    """Clean up bid packages older than specified days.

    Args:
        days_old: Number of days to keep packages

    Returns:
        Number of packages deleted
    """
    try:
        cutoff_date = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
        packages = list_bid_packages()
        deleted_count = 0

        for package in packages:
            created_at = package.get('created_at', '1970-01-01')
            if datetime.fromisoformat(created_at).timestamp() < cutoff_date:
                if delete_bid_package(package['month_tag']):
                    deleted_count += 1
                    logger.info(
                        f"Cleaned up old package: {package['month_tag']}")

        return deleted_count

    except Exception as e:
        logger.error(f"Failed to cleanup old packages: {e}")
        return 0


def export_package_manifest() -> Dict:
    """Export a manifest of all bid packages.

    Returns:
        Dict with package manifest data
    """
    packages = list_bid_packages()

    return {
        "export_date": datetime.utcnow().isoformat(),
        "total_packages": len(packages),
        "packages": packages,
        "statistics": get_admin_stats()
    }
