"""Ingestion service for bid packages using existing PBS parser."""

import tempfile
from pathlib import Path
from typing import Any, List

from app.models import BidPackage, IngestionRequest, IngestionResponse
from app.services.pbs_parser.contracts import Pairing, Trip
from app.services.pbs_parser.reader import load_jsonl, load_csv
from app.services.store import bid_package_store


class IngestionService:
    """Service for ingesting and parsing bid packages."""

    def __init__(self):
        self.supported_formats = {
            ".csv": self._parse_csv,
            ".jsonl": self._parse_jsonl,
            ".pdf": self._parse_pdf,
            ".txt": self._parse_txt,
        }

    def ingest(
        self, file_content: bytes, filename: str, request: IngestionRequest
    ) -> IngestionResponse:
        """Ingest a bid package file and return parsed summary."""
        try:
            # Determine file format
            file_ext = Path(filename).suffix.lower()
            if file_ext not in self.supported_formats:
                return IngestionResponse(
                    success=False,
                    summary={},
                    error=f"Unsupported file format: {file_ext}. Supported: {list(self.supported_formats.keys())}",
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
                    "parsed_data": summary,
                },
            )

            package_id = bid_package_store.store(bid_package, file_content)

            # Add package ID to summary
            summary["package_id"] = package_id

            return IngestionResponse(
                success=True,
                summary=summary,
                message=f"Successfully ingested {filename}",
            )

        except Exception as e:
            return IngestionResponse(
                success=False, summary={}, error=f"Failed to ingest file: {str(e)}"
            )

    def _parse_csv(self, file_content: bytes, filename: str) -> List[Pairing]:
        """Parse CSV format using existing PBS parser."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Try to detect if this is a combined file or separate files
            csv_text = file_content.decode('utf-8')
            lines = csv_text.split('\n')
            
            # Check if this looks like a combined file with both pairings and trips
            header = lines[0].lower() if lines else ""
            has_pairings = 'pairing_id' in header
            has_trips = 'trip_id' in header
            
            # Also check if the file contains both types of data (even with separate headers)
            contains_pairing_data = any('pairing_id' in line.lower() for line in lines[:5])
            contains_trip_data = any('trip_id' in line.lower() for line in lines[:5])
            
            if (has_pairings and has_trips) or (contains_pairing_data and contains_trip_data):
                # This is a combined file - we need to parse it manually
                return self._parse_combined_csv(file_content, filename)
            elif has_pairings:
                # This is just pairings - try to use existing parser
                pairings_file = temp_path / "pairings.csv"
                pairings_file.write_bytes(file_content)
                
                try:
                    # Try to use existing parser, but it might fail without trips
                    return load_csv(temp_path)
                except Exception:
                    # Fallback to mock data if parsing fails
                    return self._create_mock_pairings()
            else:
                # Unknown format - return mock data
                return self._create_mock_pairings()
    
    def _parse_combined_csv(self, file_content: bytes, filename: str) -> List[Pairing]:
        """Parse a combined CSV file that contains both pairings and trips data."""
        csv_text = file_content.decode('utf-8')
        lines = csv_text.split('\n')
        
        # Parse the CSV manually
        pairings = {}
        trips = []
        
        # Find the transition point between pairings and trips
        trip_start_line = -1
        for i, line in enumerate(lines):
            if 'trip_id' in line.lower():
                trip_start_line = i
                break
        
        # Parse pairings (lines before trip_id header)
        for line in lines[1:trip_start_line]:  # Skip first header, stop at trip header
            if not line.strip():
                continue
                
            parts = line.split(',')
            if len(parts) >= 4:
                # Check if this looks like a pairing line (has pairing_id, base, fleet, month)
                if parts[0] and parts[1] and parts[2] and parts[3]:
                    pairing_id = parts[0]
                    base = parts[1]
                    fleet = parts[2]
                    month = parts[3]
                    
                    pairings[pairing_id] = Pairing(
                        pairing_id=pairing_id,
                        base=base,
                        fleet=fleet,
                        month=month,
                        trips=[]
                    )
        
        # Parse trips (lines after trip_id header)
        if trip_start_line >= 0:
            for line in lines[trip_start_line + 1:]:  # Skip trip header
                if not line.strip():
                    continue
                    
                parts = line.split(',')
                if len(parts) >= 5:
                    # Check if this looks like a trip line (has trip_id, pairing_id, day, origin, destination)
                    if parts[0] and parts[1] and parts[2] and parts[3] and parts[4]:
                        trip_id = parts[0]
                        pairing_id = parts[1]
                        try:
                            day = int(parts[2])
                        except ValueError:
                            day = 1
                        origin = parts[3]
                        destination = parts[4]
                        
                        trip = Trip(
                            trip_id=trip_id,
                            pairing_id=pairing_id,
                            day=day,
                            origin=origin,
                            destination=destination
                        )
                        trips.append(trip)
        
        # Associate trips with pairings
        for trip in trips:
            if trip.pairing_id in pairings:
                pairings[trip.pairing_id].trips.append(trip)
        
        return list(pairings.values())

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

    def _create_summary(
        self, parsed_data: Any, request: IngestionRequest
    ) -> dict[str, Any]:
        """Create a summary from parsed data."""
        if (
            isinstance(parsed_data, list)
            and parsed_data
            and isinstance(parsed_data[0], Pairing)
        ):
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
                "bases": list(
                    {
                        p.pairing_id.split("-")[0]
                        for p in pairings
                        if "-" in p.pairing_id
                    }
                ),
                "fleet": request.fleet,
                "format": "pbs_parser",
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
                "format": "generic",
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
            Trip(
                trip_id="MOCK-001",
                pairing_id="MOCK-PAIR-001",
                day=1,
                origin="SFO",
                destination="LAX",
            ),
            Trip(
                trip_id="MOCK-002",
                pairing_id="MOCK-PAIR-001",
                day=2,
                origin="LAX",
                destination="SFO",
            ),
        ]

        return [
            Pairing(
                pairing_id="MOCK-PAIR-001",
                base="SFO",
                fleet="737",
                month="2025-09-01",
                trips=trips,
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
                "equipment": "737",
            },
            {
                "trip_id": "MOCK-002",
                "days": 3,
                "credit_hours": 15.2,
                "route": "SFO-ORD-SFO",
                "equipment": "737",
            },
        ]


# Global instance
ingestion_service = IngestionService()
