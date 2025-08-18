"""Lightweight storage service for bid packages."""

import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from app.models import BidPackage


class BidPackageStore:
    """File-backed storage for bid packages with SQLite metadata."""

    def __init__(self, storage_dir: str = "uploads", db_path: str = "bid_packages.db"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database with bid_packages table."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bid_packages (
                id TEXT PRIMARY KEY,
                pilot_id TEXT NOT NULL,
                airline TEXT NOT NULL,
                month TEXT NOT NULL,
                meta TEXT NOT NULL,
                created_at TEXT NOT NULL,
                hash TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    def store(self, bid_package: BidPackage, file_content: bytes) -> str:
        """Store a bid package and return the ID."""
        # Generate hash and ID
        file_hash = hashlib.sha256(file_content).hexdigest()
        package_id = f"{bid_package.pilot_id}_{bid_package.airline}_{bid_package.month}_{file_hash[:8]}"

        # Store file
        file_path = self.storage_dir / f"{package_id}.bin"
        file_path.write_bytes(file_content)

        # Store metadata in SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO bid_packages
            (id, pilot_id, airline, month, meta, created_at, hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                package_id,
                bid_package.pilot_id,
                bid_package.airline,
                bid_package.month,
                json.dumps(bid_package.meta),
                bid_package.created_at.isoformat(),
                file_hash,
            ),
        )

        conn.commit()
        conn.close()

        return package_id

    def get(self, package_id: str) -> BidPackage | None:
        """Retrieve a bid package by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, pilot_id, airline, month, meta, created_at, hash
            FROM bid_packages WHERE id = ?
        """,
            (package_id,),
        )

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return BidPackage(
            id=row[0],
            pilot_id=row[1],
            airline=row[2],
            month=row[3],
            meta=json.loads(row[4]),
            created_at=datetime.fromisoformat(row[5]),
            hash=row[6],
        )

    def list_by_pilot(self, pilot_id: str) -> list[BidPackage]:
        """List all bid packages for a pilot."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, pilot_id, airline, month, meta, created_at, hash
            FROM bid_packages WHERE pilot_id = ? ORDER BY created_at DESC
        """,
            (pilot_id,),
        )

        rows = cursor.fetchall()
        conn.close()

        return [
            BidPackage(
                id=row[0],
                pilot_id=row[1],
                airline=row[2],
                month=row[3],
                meta=json.loads(row[4]),
                created_at=datetime.fromisoformat(row[5]),
                hash=row[6],
            )
            for row in rows
        ]

    def delete(self, package_id: str) -> bool:
        """Delete a bid package."""
        # Get package info first
        package = self.get(package_id)
        if not package:
            return False

        # Delete file
        file_path = self.storage_dir / f"{package_id}.bin"
        if file_path.exists():
            file_path.unlink()

        # Delete from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM bid_packages WHERE id = ?", (package_id,))
        deleted = cursor.rowcount > 0

        conn.commit()
        conn.close()

        return deleted


# Global instance
bid_package_store = BidPackageStore()
