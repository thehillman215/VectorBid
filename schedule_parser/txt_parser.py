import re, io

# Multiple regex patterns for different airline formats
_PATTERNS = [
    # Standard format: "105 3-Day Credit: 15.30"
    re.compile(r"^(?P<id>\d{3,4})\s+(?P<days>\d)-Day.*?(?P<credit>\d+\.\d{2})"
               ),

    # With "Trip" prefix: "Trip 105 3-Day Credit: 15.30"
    re.compile(
        r"^Trip\s+(?P<id>\d{3,4})\s+(?P<days>\d)-Day.*?(?P<credit>\d+\.\d{2})"
    ),

    # United format: "105 4-Day Trip Credit: 18.30"
    re.compile(
        r"^(?P<id>\d{3,4})\s+(?P<days>\d+)-Day\s+Trip\s+Credit:\s*(?P<credit>\d{1,2}\.\d{2})"
    ),

    # More flexible format: "105: 3 days, 15.30 credit"
    re.compile(
        r"^(?P<id>\d{3,4}).*?(?P<days>\d+).*?day.*?(?P<credit>\d+\.\d{2})"),

    # Generic format: any line with trip ID, days, and credit
    re.compile(r"(?P<id>\d{3,4}).*?(?P<days>\d+).*?(?P<credit>\d{1,2}\.\d{2})",
               re.IGNORECASE)
]


def parse_txt(blob: bytes) -> list[dict]:
    trips = []
    text = blob.decode("utf-8", "ignore")

    # Try each pattern
    for pattern in _PATTERNS:
        found_trips = []

        for line in io.StringIO(text):
            line = line.strip()
            if not line:
                continue

            m = pattern.match(line)
            if m:
                try:
                    trip = {
                        "trip_id":
                        m["id"],  # Changed from "id" to "trip_id" for consistency
                        "days": int(m["days"]),
                        "credit_hours":
                        float(m["credit"]
                              ),  # Changed from "credit" to "credit_hours"
                        "includes_weekend": _detect_weekend(line),
                        "routing": _extract_routing(line),
                        "raw": line,
                    }
                    found_trips.append(trip)
                except (ValueError, KeyError):
                    continue

        # If we found trips with this pattern, use them
        if found_trips:
            trips = found_trips
            break

    if not trips:
        raise RuntimeError("TXT parse produced zero trips")

    return trips


def _detect_weekend(line: str) -> bool:
    """Detect if trip includes weekend based on line content."""
    line_lower = line.lower()
    weekend_indicators = [
        'sat', 'sun', 'saturday', 'sunday', 'weekend', 'wknd'
    ]
    return any(indicator in line_lower for indicator in weekend_indicators)


def _extract_routing(line: str) -> str:
    """Extract routing information from line."""
    # Look for airport codes (3-letter combinations)
    airport_pattern = re.compile(r'\b([A-Z]{3})\b')
    airports = airport_pattern.findall(line)

    if len(airports) >= 2:
        return '-'.join(airports[:4])  # Limit to first 4 airports

    return ''
