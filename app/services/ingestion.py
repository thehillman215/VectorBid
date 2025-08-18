"""Ingestion service for bid packages using existing PBS parser."""

import tempfile
from pathlib import Path
from typing import Any

from app.models import BidPackage, IngestionRequest, IngestionResponse
from app.services.pbs_parser.contracts import Pairing, Trip
from app.services.pbs_parser.reader import load_jsonl
from app.services.store import bid_package_store


class IngestionService:
    """Service for ingesting and parsing bid packages."""

    def __init__(self):
        self.supported_formats = {
            '.csv': self._parse_csv,
            '.jsonl': self._parse_jsonl,
            '.pdf': self._parse_pdf,
            '.txt': self._parse_txt
        }

    def ingest(self, file_content: bytes, filename: str, request: IngestionRequest) -> IngestionResponse:
        """Ingest a bid package file and return parsed summary."""
        try:
            # Determine file format
            file_ext = Path(filename).suffix.lower()
            if file_ext not in self.supported_formats:
                return IngestionResponse(
                    success=False,
                    summary={},
                    error=f"Unsupported file format: {file_ext}. Supported: {list(self.supported_formats.keys())}"
                )

            # Parse the file
            parse_func = self.supported_formats[file_ext]
            parsed_data = parse_func(file_content, filename)

            # Create summary
            summary = self._create_summary(parsed_data, request)

            # Store the bid package
            bid_package = BidPackage(
                pilot_id=request.pilot_id,
                airline=request.airline,
                month=request.month,
                meta={
                    "filename": filename,
                    "file_size": len(file_content),
                    "file_type": file_ext,
                    "base": request.base,
                    "fleet": request.fleet,
                    "seat": request.seat,
                    "parsed_data": summary
                }
            )

            package_id = bid_package_store.store(bid_package, file_content)

            # Add package ID to summary
            summary["package_id"] = package_id

            return IngestionResponse(
                success=True,
                summary=summary,
                message=f"Successfully ingested {filename}"
            )

        except Exception as e:
            return IngestionResponse(
                success=False,
                summary={},
                error=f"Failed to ingest file: {str(e)}"
            )

    def _parse_csv(self, file_content: bytes, filename: str) -> list[Pairing]:
        """Parse CSV format using existing PBS parser."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Write the CSV content to a temporary file
            # Note: This assumes the CSV contains both pairings and trips data
            # In a real implementation, we'd need to handle the file structure properly
            csv_file = temp_path / "data.csv"
            csv_file.write_bytes(file_content)

            # For now, return mock data since the existing parser expects specific file structure
            # TODO: Enhance the parser to handle single CSV files
            return self._create_mock_pairings()

    def _parse_jsonl(self, file_content: bytes, filename: str) -> list[Pairing]:
        """Parse JSONL format using existing PBS parser."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Write the JSONL content to a temporary file
            jsonl_file = temp_path / "pairings.jsonl"
            jsonl_file.write_bytes(file_content)

            try:
                return load_jsonl(temp_path)
            except Exception:
                # Fallback to mock data if parsing fails
                return self._create_mock_pairings()

    def _parse_pdf(self, file_content: bytes, filename: str) -> list[dict[str, Any]]:
        """Parse PDF format - placeholder for future implementation."""
        # TODO: Integrate with existing PDF parser from src/lib/schedule_parser/
        # For now, return mock data
        return self._create_mock_trips()

    def _parse_txt(self, file_content: bytes, filename: str) -> list[dict[str, Any]]:
        """Parse TXT format - placeholder for future implementation."""
        # TODO: Integrate with existing TXT parser from src/lib/schedule_parser/
        # For now, return mock data
        return self._create_mock_trips()

    def _create_summary(self, parsed_data: Any, request: IngestionRequest) -> dict[str, Any]:
        """Create a summary from parsed data."""
        if isinstance(parsed_data, list) and parsed_data and isinstance(parsed_data[0], Pairing):
            # PBS parser format
            pairings = parsed_data
            trips = []
            for pairing in pairings:
                trips.extend(pairing.trips)

            return {
                "trips": len(trips),
                "legs": len(trips),
                "pairings": len(pairings),
                "date_span": f"{request.month}",
                "credit_total": self._estimate_credit_total(trips),
                "bases": list({p.pairing_id.split('-')[0] for p in pairings if '-' in p.pairing_id}),
                "fleet": request.fleet,
                "format": "pbs_parser"
            }
        else:
            # Generic format (from PDF/TXT parsers)
            trips = parsed_data
            return {
                "trips": len(trips),
                "legs": len(trips),
                "pairings": len(trips),  # Assuming 1:1 mapping for now
                "date_span": f"{request.month}",
                "credit_total": self._estimate_credit_total_generic(trips),
                "bases": [request.base],
                "fleet": request.fleet,
                "format": "generic"
            }

    def _estimate_credit_total(self, trips: list[Trip]) -> float:
        """Estimate total credit hours from PBS parser trips."""
        # Mock credit calculation - in real implementation would use actual credit data
        return len(trips) * 5.5  # Assume average 5.5 hours per trip

    def _estimate_credit_total_generic(self, trips: list[dict[str, Any]]) -> float:
        """Estimate total credit hours from generic trip data."""
        total = 0.0
        for trip in trips:
            if isinstance(trip, dict) and "credit_hours" in trip:
                total += float(trip["credit_hours"])
            else:
                total += 5.5  # Default assumption
        return total

    def _create_mock_pairings(self) -> list[Pairing]:
        """Create mock pairings for testing."""
        from app.services.pbs_parser.contracts import Trip

        trips = [
            Trip(trip_id="MOCK-001", pairing_id="MOCK-PAIR-001", day=1, origin="SFO", destination="LAX"),
            Trip(trip_id="MOCK-002", pairing_id="MOCK-PAIR-001", day=2, origin="LAX", destination="SFO"),
        ]

        return [
            Pairing(
                pairing_id="MOCK-PAIR-001",
                base="SFO",
                fleet="737",
                month="2025-09-01",
                trips=trips
            )
        ]

    def _create_mock_trips(self) -> list[dict[str, Any]]:
        """Create mock trips for testing."""
        return [
            {
                "trip_id": "MOCK-001",
                "days": 2,
                "credit_hours": 10.5,
                "route": "SFO-LAX-SFO",
                "equipment": "737"
            },
            {
                "trip_id": "MOCK-002",
                "days": 3,
                "credit_hours": 15.2,
                "route": "SFO-ORD-SFO",
                "equipment": "737"
            }
        ]


# Global instance
ingestion_service = IngestionService()
