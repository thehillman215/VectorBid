"""Bid packet storage service."""

from extensions import db
from models import BidPacket


def save_bid_packet(
    month_tag: str, file_stream, filename: str | None = None
) -> BidPacket:
    """Save a bid packet PDF to PostgreSQL database.

    Args:
        month_tag: Six-digit YYYYMM format
        file_stream: File stream to save
        filename: Original filename (optional)

    Returns:
        BidPacket: The created database record

    Raises:
        ValueError: If month_tag already exists
    """
    # Read the PDF data from stream
    pdf_data = file_stream.read()
    file_size = len(pdf_data)

    # Use provided filename or generate default
    if not filename:
        filename = f"bid_{month_tag}.pdf"

    # Check if month_tag already exists
    existing = BidPacket.query.filter_by(month_tag=month_tag).first()
    if existing:
        # Update existing record
        existing.filename = filename
        existing.file_size = file_size
        existing.pdf_data = pdf_data
        db.session.commit()
        return existing

    # Create new bid packet record
    bid_packet = BidPacket()  # type: ignore
    bid_packet.month_tag = month_tag
    bid_packet.filename = filename
    bid_packet.file_size = file_size
    bid_packet.pdf_data = pdf_data

    # Save to database
    db.session.add(bid_packet)
    db.session.commit()

    return bid_packet


def get_bid_packet(month_tag: str) -> BidPacket | None:
    """Retrieve a bid packet by month tag.

    Args:
        month_tag: Six-digit YYYYMM format

    Returns:
        BidPacket: The database record or None if not found
    """
    return BidPacket.query.filter_by(month_tag=month_tag).first()


def list_bid_packets() -> list[BidPacket]:
    """List all bid packets ordered by month tag descending.

    Returns:
        List of BidPacket records
    """
    return BidPacket.query.order_by(BidPacket.month_tag.desc()).all()
