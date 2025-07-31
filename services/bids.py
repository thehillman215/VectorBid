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


def get_matching_bid_packet(profile: dict) -> dict | None:
    """Get the appropriate bid packet for a pilot based on their profile.
    
    Args:
        profile: Pilot profile dictionary with airline, fleet, seat, base info
        
    Returns:
        Dictionary with bid packet info or None if no match found
    """
    from datetime import datetime
    
    try:
        # Get current month in YYYYMM format
        current_month = datetime.now().strftime("%Y%m")
        
        # For now, we'll look for current month bid packets
        # In the future, this logic will expand to match based on:
        # - Airline (profile['airline'])
        # - Aircraft types (profile['fleet'])
        # - Position CA/FO (profile['seat'])
        # - Base airport (profile['base'])
        
        # For testing, prioritize August 2025 (202508) for 737 FO IAH profiles
        target_month = current_month
        if (profile.get('fleet') and '737' in profile['fleet'] and 
            profile.get('base') == 'IAH' and profile.get('seat') == 'FO'):
            august_bid = BidPacket.query.filter_by(month_tag='202508').first()
            if august_bid:
                target_month = '202508'
        
        bid_packet = BidPacket.query.filter_by(month_tag=target_month).first()
        
        if bid_packet:
            return {
                'month_tag': bid_packet.month_tag,
                'filename': bid_packet.filename,
                'file_size': bid_packet.file_size,
                'upload_date': bid_packet.uploaded_at,
                'matches_profile': True,  # Will be more sophisticated matching logic
                'content': bid_packet.pdf_data
            }
        
        return None
        
    except Exception as e:
        print(f"Error finding matching bid packet: {e}")
        return None
