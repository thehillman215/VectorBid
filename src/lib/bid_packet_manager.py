"""
Bid Packet and Contract Management System
Handles upload, storage, and parsing of airline bid packets and contracts
"""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


class BidPacketManager:
    """Manages bid packets and pilot contracts"""

    def __init__(self):
        # Create storage directories
        self.storage_dir = Path("bids")
        self.contracts_dir = Path("contracts")
        self.metadata_dir = Path("data/metadata")

        for dir_path in [self.storage_dir, self.contracts_dir, self.metadata_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def upload_bid_packet(self, file_obj, month_tag: str, airline: str) -> dict:
        """
        Upload and store a bid packet

        Args:
            file_obj: File object from Flask request
            month_tag: YYYYMM format (e.g., '202502')
            airline: Airline code (e.g., 'UAL', 'AAL', 'DAL')

        Returns:
            Dict with upload status and metadata
        """
        try:
            # Validate month_tag
            if not self._validate_month_tag(month_tag):
                return {"success": False, "error": "Invalid month tag format"}

            # Generate filename
            filename = f"bid_packet_{airline}_{month_tag}.pdf"
            file_path = self.storage_dir / filename

            # Save file
            file_obj.save(str(file_path))

            # Generate metadata
            file_size = file_path.stat().st_size
            file_hash = self._calculate_file_hash(file_path)

            metadata = {
                "filename": filename,
                "month_tag": month_tag,
                "airline": airline,
                "upload_date": datetime.utcnow().isoformat(),
                "file_size": file_size,
                "file_hash": file_hash,
                "status": "uploaded",
                "parsed": False,
                "trips_count": 0,
                "bases": [],
                "equipment": [],
            }

            # Save metadata
            metadata_file = self.metadata_dir / f"{month_tag}_{airline}.json"
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)

            # TODO: Trigger parsing job here
            self._queue_for_parsing(file_path, metadata)

            return {
                "success": True,
                "message": f"Bid packet uploaded successfully for {airline} {month_tag}",
                "metadata": metadata,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def upload_pilot_contract(
        self, file_obj, airline: str, version: str = None
    ) -> dict:
        """
        Upload and store a pilot contract

        Args:
            file_obj: File object from Flask request
            airline: Airline code
            version: Contract version/date

        Returns:
            Dict with upload status
        """
        try:
            # Generate filename
            version = version or datetime.now().strftime("%Y%m")
            filename = f"contract_{airline}_{version}.pdf"
            file_path = self.contracts_dir / filename

            # Save file
            file_obj.save(str(file_path))

            # Generate metadata
            metadata = {
                "filename": filename,
                "airline": airline,
                "version": version,
                "upload_date": datetime.utcnow().isoformat(),
                "file_size": file_path.stat().st_size,
                "sections": [],
                "rules_extracted": False,
            }

            # Save metadata
            metadata_file = self.metadata_dir / f"contract_{airline}_{version}.json"
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)

            # TODO: Extract contract rules for PBS validation
            self._extract_contract_rules(file_path, metadata)

            return {
                "success": True,
                "message": f"Contract uploaded successfully for {airline}",
                "metadata": metadata,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_available_bid_packets(self, airline: str = None) -> list[dict]:
        """Get list of available bid packets"""
        packets = []

        # Read all metadata files
        for metadata_file in self.metadata_dir.glob("*.json"):
            if metadata_file.name.startswith("contract_"):
                continue

            with open(metadata_file) as f:
                metadata = json.load(f)

            if airline and metadata.get("airline") != airline:
                continue

            packets.append(metadata)

        # Sort by month_tag descending (newest first)
        packets.sort(key=lambda x: x.get("month_tag", ""), reverse=True)

        return packets

    def get_bid_packet_for_month(self, month_tag: str, airline: str) -> dict | None:
        """Get specific bid packet for a month"""
        metadata_file = self.metadata_dir / f"{month_tag}_{airline}.json"

        if metadata_file.exists():
            with open(metadata_file) as f:
                return json.load(f)

        return None

    def parse_bid_packet(self, file_path: Path, metadata: dict) -> dict:
        """
        Parse bid packet to extract trips
        This is a placeholder - implement actual parsing logic
        """
        # TODO: Implement actual PDF parsing
        # For now, return mock data
        trips = [
            {
                "trip_id": "UA1234",
                "days": 3,
                "credit_hours": 15.5,
                "route": "DEN-ORD-LAX-DEN",
                "equipment": "737",
                "layovers": ["ORD", "LAX"],
                "report_time": "06:00",
                "release_time": "18:30",
            },
            {
                "trip_id": "UA5678",
                "days": 2,
                "credit_hours": 10.2,
                "route": "DEN-SFO-DEN",
                "equipment": "787",
                "layovers": ["SFO"],
                "report_time": "10:00",
                "release_time": "20:15",
            },
        ]

        metadata["parsed"] = True
        metadata["trips_count"] = len(trips)
        metadata["bases"] = ["DEN"]
        metadata["equipment"] = ["737", "787"]

        return {"success": True, "trips": trips, "metadata": metadata}

    def _validate_month_tag(self, month_tag: str) -> bool:
        """Validate month tag format YYYYMM"""
        if not month_tag or len(month_tag) != 6:
            return False

        try:
            year = int(month_tag[:4])
            month = int(month_tag[4:])

            if year < 2020 or year > 2099:
                return False
            if month < 1 or month > 12:
                return False

            return True
        except ValueError:
            return False

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _queue_for_parsing(self, file_path: Path, metadata: dict):
        """Queue bid packet for parsing"""
        # TODO: Implement async parsing queue
        # For now, parse immediately
        self.parse_bid_packet(file_path, metadata)

    def _extract_contract_rules(self, file_path: Path, metadata: dict):
        """Extract rules from pilot contract"""
        # TODO: Implement contract parsing and rule extraction
        # This would extract things like:
        # - Rest requirements
        # - Maximum duty days
        # - Minimum days off
        # - Seniority rules
        # - Equipment qualifications
        pass

    def upload_bid_packet(self, file, month_tag: str, airline: str) -> dict[str, Any]:
        """Upload a bid packet file"""
        try:
            # Create filename
            filename = f"{airline}_{month_tag}.pdf"
            file_path = os.path.join(self.bid_storage_path, filename)

            # Save the file
            file.save(file_path)

            # Create metadata
            metadata = {
                "month_tag": month_tag,
                "airline": airline,
                "filename": filename,
                "upload_date": datetime.now().isoformat(),
                "file_size": os.path.getsize(file_path),
            }

            # Save metadata
            metadata_file = os.path.join(
                self.metadata_path, f"{month_tag}_{airline}.json"
            )
            with open(metadata_file, "w") as f:
                json.dump(metadata, f)

            return {
                "success": True,
                "message": f"Bid packet uploaded successfully: {filename}",
                "filename": filename,
            }

        except Exception as e:
            return {"success": False, "error": f"Upload failed: {str(e)}"}

    def delete_bid_packet(self, month_tag: str, airline: str) -> dict[str, Any]:
        """Delete a bid packet"""
        try:
            filename = f"{airline}_{month_tag}.pdf"
            file_path = os.path.join(self.bid_storage_path, filename)
            metadata_file = os.path.join(
                self.metadata_path, f"{month_tag}_{airline}.json"
            )

            # Remove files if they exist
            if os.path.exists(file_path):
                os.remove(file_path)

            if os.path.exists(metadata_file):
                os.remove(metadata_file)

            return {"success": True, "message": f"Bid packet deleted: {filename}"}

        except Exception as e:
            return {"success": False, "error": f"Delete failed: {str(e)}"}

    def get_bid_packet_file(
        self, month_tag: str, airline: str
    ) -> tuple[bytes, str] | None:
        """Get bid packet file data for download"""
        try:
            filename = f"{airline}_{month_tag}.pdf"
            file_path = os.path.join(self.bid_storage_path, filename)

            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    return f.read(), filename

            return None

        except Exception as e:
            print(f"Error retrieving file: {e}")
            return None

    def _extract_month_tag(self, filename: str) -> str:
        """Extract month tag from filename"""
        # Try to find 6-digit year/month pattern
        import re

        match = re.search(r"(\d{6})", filename)
        if match:
            return match.group(1)

        # Fallback to current date
        now = datetime.now()
        return f"{now.year}{now.month:02d}"

    def _extract_airline(self, filename: str) -> str:
        """Extract airline from filename"""
        filename_lower = filename.lower()

        if "united" in filename_lower or "ual" in filename_lower:
            return "United"
        elif "delta" in filename_lower:
            return "Delta"
        elif "american" in filename_lower:
            return "American"
        elif "southwest" in filename_lower:
            return "Southwest"
        elif "alaska" in filename_lower:
            return "Alaska"
        else:
            return "Unknown"
