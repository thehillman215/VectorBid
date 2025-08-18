#!/usr/bin/env python3
"""Recreate bid_packets table with airline-based uniqueness.

This lightweight migration drops the existing ``bid_packets`` table and
recreates it using the current SQLAlchemy model definition, which now
includes an ``airline`` column and a composite unique constraint on
``(month_tag, airline)``.
"""

from src.core.app import create_app
from src.core.models import BidPacket, db


def migrate() -> None:
    """Drop and recreate the bid_packets table."""
    app = create_app()
    with app.app_context():
        # Remove old table if it exists
        BidPacket.__table__.drop(db.engine, checkfirst=True)
        # Create table with updated schema
        BidPacket.__table__.create(db.engine, checkfirst=True)
        print("bid_packets table recreated with airline column and composite uniqueness")


if __name__ == "__main__":  # pragma: no cover - script entry point
    migrate()
