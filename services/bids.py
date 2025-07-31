"""
Bid-packet helper wrappers around the storage layer.
"""

from pathlib import Path
from datetime import datetime
from typing import BinaryIO

from storage import disk_storage


def _key(month_tag: str) -> str:
    """
    Map a yyyymm tag -> storage key.
    Example: "202508" -> "bid_packets/202508.pdf"
    """
    return f"bid_packets/{month_tag}.pdf"


def save_bid_packet(month_tag: str, fp: BinaryIO) -> None:
    """
    Persist the uploaded PDF so pilots can fetch it later.

    `month_tag` must be a six-digit string YYYYMM.
    """
    if not (len(month_tag) == 6 and month_tag.isdigit()):
        raise ValueError("month_tag must be YYYYMM (e.g. 202508)")

    disk_storage.save(_key(month_tag), fp)


def latest_tag() -> str | None:
    """
    Return the newest YYYYMM tag we have stored, or None.
    (LocalDisk backend has no listing API yet; stub for later.)
    """
    # TODO: implement once storage backend supports listing.
    return None


def exists(month_tag: str) -> bool:
    return disk_storage.exists(_key(month_tag))
