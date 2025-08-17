"""Enhanced TXT parser with United Airlines support."""

import re
import io
import logging

logger = logging.getLogger(__name__)

# Enhanced patterns for United Airlines
_PATTERNS = [
    # United table format: UA123  3DAY  DEN-LAX-DEN     18:30   15FEB-17FEB
    {
        'name': 'united_table',
        'pattern': re.compile(
            r'(?P<trip_id>UA\d+)\s+(?P<days>\d+)DAY\s+(?P<routing>[A-Z]{3}(?:-[A-Z]{3})+)\s+(?P<credit>\d+[:\.]?\d+)\s+(?P<dates>\S+)',
            re.IGNORECASE
        ),
        'confidence': 0.95
    },

    # Numeric with routing: 202 1DAY DEN-ORD-DEN 06:45 10MAR-10MAR
    {
        'name': 'numeric_routing',
        'pattern': re.compile(
            r'(?P<trip_id>\d+)\s+(?P<days>\d+)DAY\s+(?P<routing>[A-Z]{3}(?:-[A-Z]{3})+)\s+(?P<credit>\d+[:\.]?\d+)\s+(?P<dates>\S+)',
            re.IGNORECASE
        ),
        'confidence': 0.85
    },

    # Your existing format: "105 4-Day Trip Credit: 18.30"
    {
        'name': 'existing_format',
        'pattern': re.compile(
            r'^(?P<trip_id>\d{3,4})\s+(?P<days>\d+)-Day\s+Trip\s+Credit:\s*(?P<credit>\d{1,2}\.\d{2})',
            re.IGNORECASE
        ),
        'confidence': 0.8
    },

    # Simple format: "105 3-Day Credit: 15.30"
    {
        'name': 'simple_format',
        'pattern': re.compile(
            r'^(?P<trip_id>\d{3,4})\s+(?P<days>\d)-Day.*?(?P<credit>\d+\.\d{2})'
        ),
        'confidence': 0.7
    }
]

def parse_txt(blob: bytes) -> list[dict]:
    """Parse TXT files with United Airlines support."""
    trips = []
    text = blob.decode("utf-8", "ignore")
    lines = text.split('\n')

    # Try each pattern
    for pattern_info in _PATTERNS:
        pattern = pattern_info['pattern']
        pattern_name = pattern_info['name']
        confidence = pattern_info['confidence']

        found_trips = []

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or len(line) < 8:
                continue

            # Skip headers
            if _is_header_line(line):
                continue

            match = pattern.search(line)
            if match:
                try:
                    trip = _extract_trip(match, line, confidence, pattern_name)
                    if trip:
                        found_trips.append(trip)
                except (ValueError, KeyError):
                    continue

        # Use first successful pattern
        if found_trips:
            trips = found_trips
            break

    if not trips:
        raise RuntimeError("TXT parse produced zero trips")

    return trips

def _is_header_line(line: str) -> bool:
    """Check if line is a header."""
    line_upper = line.upper()
    headers = ['UNITED AIRLINES', 'PILOT BID', 'BASE:', 'TRIP   DAYS', 'EQUIPMENT:']
    return any(header in line_upper for header in headers)

def _extract_trip(match, line, confidence, pattern_name):
    """Extract trip from match."""
    groups = match.groupdict()

    trip_id = groups['trip_id'].strip()
    if not trip_id.startswith('UA') and trip_id.isdigit():
        trip_id = f"UA{trip_id}"

    days = int(groups['days'])
    credit_str = groups['credit'].replace(':', '.')
    credit_hours = float(credit_str)

    routing = groups.get('routing', '').strip()
    dates = groups.get('dates', '').strip()

    return {
        "trip_id": trip_id,
        "id": trip_id,  # Compatibility
        "days": days,
        "credit_hours": credit_hours,
        "credit": credit_hours,  # Compatibility
        "routing": routing,
        "dates": dates,
        "includes_weekend": _detect_weekend(line),
        "raw": line,
        "confidence": confidence
    }

def _detect_weekend(line: str) -> bool:
    """Detect weekend in line."""
    line_upper = line.upper()
    return any(indicator in line_upper for indicator in ['SAT', 'SUN', 'WEEKEND'])