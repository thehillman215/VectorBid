"""Bid packet storage service."""
import os
from pathlib import Path


def save_bid_packet(month_tag: str, file_stream) -> None:
    """Save a bid packet PDF to storage.
    
    Args:
        month_tag: Six-digit YYYYMM format
        file_stream: File stream to save
    """
    # Create bids directory if it doesn't exist
    bids_dir = Path("bids")
    bids_dir.mkdir(exist_ok=True)
    
    # Save the file
    filename = f"bid_{month_tag}.pdf"
    filepath = bids_dir / filename
    
    with open(filepath, 'wb') as f:
        f.write(file_stream.read())