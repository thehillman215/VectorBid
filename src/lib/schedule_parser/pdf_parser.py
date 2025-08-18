import re

# Enhanced patterns for United Airlines 737 bid packets
_UNITED_PATTERNS = [
    # United trip pattern: "ID H5001  - BASIC" followed by flight data and "DAYS- 1 CRD- 5.38*"
    re.compile(
        r"ID\s+(?P<id>H\d{4})\s*-\s*\w+.*?"
        r"DAYS-\s*(?P<days>\d+)\s+CRD-\s*(?P<credit>\d{1,2}\.\d{2})",
        re.DOTALL | re.MULTILINE,
    ),
    # Alternative pattern in case structure varies
    re.compile(
        r"(?P<id>H\d{4}).*?"
        r"DAYS-\s*(?P<days>\d+).*?"
        r"CRD-\s*(?P<credit>\d{1,2}\.\d{2})",
        re.DOTALL,
    ),
    # Fallback for any H-prefixed 4-digit IDs with credit hours
    re.compile(r"(?P<id>H\d{4}).*?" r"(?P<credit>\d{1,2}\.\d{2})", re.DOTALL),
]

# Standard patterns for other airlines (fallback)
_STANDARD_PATTERNS = [
    re.compile(
        r"(?P<id>\d{3,4})\s+"
        r"(?P<days>\d)-Day.*?"
        r"(?P<credit>\d{1,2}\.\d{2})\s+Cred",
        re.S,
    ),
    re.compile(
        r"(?P<id>\d{3,4})\s+"
        r"(?P<days>\d+)-Day\s+Trip\s+"
        r"Credit:\s*(?P<credit>\d{1,2}\.\d{2})",
        re.IGNORECASE,
    ),
]


def parse_pdf(blob: bytes) -> list[dict]:
    """Enhanced PDF parser for United and other airlines."""
    try:
        import fitz  # PyMuPDF imported only when needed
    except ImportError:
        raise RuntimeError("PyMuPDF not available - PDF parsing disabled") from None

    trips: list[dict] = []

    with fitz.open(stream=blob, filetype="pdf") as pdf:
        # Extract text from all pages
        full_text = ""
        for page in pdf:
            page_text = page.get_text()
            full_text += page_text + "\n"

        if not full_text.strip():
            raise RuntimeError("No text could be extracted from PDF")

        # Try United patterns first
        trips = _parse_united_format(full_text)

        # If no United trips found, try standard patterns
        if not trips:
            trips = _parse_standard_format(full_text)

    if not trips:
        raise RuntimeError("No trips parsed from PDF")

    return _deduplicate_and_enhance_trips(trips, full_text)


def _parse_united_format(text: str) -> list[dict]:
    """Parse United Airlines 737 bid packet format."""
    trips = []

    for pattern in _UNITED_PATTERNS:
        matches = list(pattern.finditer(text))

        if matches:
            print(f"Using United pattern, found {len(matches)} matches")

            for match in matches:
                try:
                    trip_id = match.group("id")

                    # Extract days (default to 1 if not found)
                    try:
                        days = int(match.group("days"))
                    except (IndexError, ValueError):
                        days = 1  # Most United day trips are 1 day

                    # Extract credit hours
                    credit = float(match.group("credit"))

                    # Get the full context around this match for route extraction
                    start, end = match.span()
                    context_start = max(0, start - 500)
                    context_end = min(len(text), end + 500)
                    context = text[context_start:context_end]

                    # Build the trip object
                    trip = {
                        "trip_id": trip_id,
                        "days": days,
                        "credit_hours": credit,
                        "includes_weekend": _detect_united_weekend(context),
                        "routing": _extract_united_routing(context),
                        "equipment": _extract_equipment(context),
                        "report_time": _extract_report_time(context),
                        "release_time": _extract_release_time(context),
                        "flight_time": _extract_flight_time(context),
                        "raw": match.group(0).strip(),
                    }

                    trips.append(trip)

                except (ValueError, AttributeError) as e:
                    print(f"Error parsing United trip: {e}")
                    continue

            # If we found trips with United patterns, use them
            if trips:
                break

    return trips


def _parse_standard_format(text: str) -> list[dict]:
    """Parse standard airline formats (fallback)."""
    trips = []

    for pattern in _STANDARD_PATTERNS:
        matches = list(pattern.finditer(text))

        if matches:
            for match in matches:
                try:
                    trip = {
                        "trip_id": match.group("id"),
                        "days": int(match.group("days")),
                        "credit_hours": float(match.group("credit")),
                        "includes_weekend": False,
                        "routing": "",
                        "raw": match.group(0).strip(),
                    }
                    trips.append(trip)
                except (ValueError, AttributeError):
                    continue

            if trips:
                break

    return trips


def _extract_united_routing(context: str) -> str:
    """Extract routing information from United trip context."""
    # United uses 3-letter airport codes like: IAH ORD, IAH LGA, etc.
    # Look for patterns like "IAH ORD 0630 0912" or "IAH LAS 0730 0900"

    # Common United hubs and airports
    airports = {
            "IAH",
            "DEN",
            "EWR",
            "SFO",
            "LAX",
            "ORD",
            "LAS",
            "LGA",
            "BNA",
            "FLL",
            "CUN",
            "DFW",
            "ATL",
            "PHX",
            "SEA",
            "BOS",
        }

    # Find airport code patterns
    airport_pattern = re.compile(r"\b([A-Z]{3})\b")
    found_airports = airport_pattern.findall(context)

    # Filter to valid airports and create routing
    route_airports = []
    for airport in found_airports:
        if airport in airports and airport not in route_airports:
            route_airports.append(airport)

    # For United day trips, usually it's OUT-BACK format
    if len(route_airports) >= 2:
        return "-".join(route_airports[:4])  # Limit to 4 airports max

    return ""


def _extract_equipment(context: str) -> str:
    """Extract aircraft equipment from context."""
    # Look for equipment codes like 37X, 73Y, 73C, 37E
    equipment_pattern = re.compile(r"\b(37[XYCE]|73[YXCE])\b")
    match = equipment_pattern.search(context)

    if match:
        return match.group(1)

    return "737"  # Default for 737 bid packet


def _extract_report_time(context: str) -> str:
    """Extract report time from context."""
    # Look for "RPT: 0530" pattern
    rpt_pattern = re.compile(r"RPT:\s*(\d{4})")
    match = rpt_pattern.search(context)

    if match:
        time_str = match.group(1)
        # Convert to HH:MM format
        return f"{time_str[:2]}:{time_str[2:]}"

    return ""


def _extract_release_time(context: str) -> str:
    """Extract release time from context."""
    # Look for "RLS: 1351" pattern
    rls_pattern = re.compile(r"RLS:\s*(\d{4})")
    match = rls_pattern.search(context)

    if match:
        time_str = match.group(1)
        return f"{time_str[:2]}:{time_str[2:]}"

    return ""


def _extract_flight_time(context: str) -> str:
    """Extract flight time from context."""
    # Look for "FTM- 5.38" pattern
    ftm_pattern = re.compile(r"FTM-\s*(\d{1,2}\.\d{2})")
    match = ftm_pattern.search(context)

    if match:
        return match.group(1)

    return ""


def _detect_united_weekend(context: str) -> bool:
    """Detect weekend flying from United context."""
    # Look at the calendar grid at the end: SU|MO TU WE TH FR|SA
    # Numbers in SA or SU columns indicate weekend flying

    # Look for patterns like "22|23 24 25 26 27|28" where 22,28 would be weekend
    re.compile(r"(\d{1,2})\|.*?\|(\d{1,2})")

    # Also check for explicit weekend indicators
    weekend_indicators = ["saturday", "sunday", "sat", "sun", "weekend"]
    context_lower = context.lower()

    return any(indicator in context_lower for indicator in weekend_indicators)


def _deduplicate_and_enhance_trips(trips: list[dict], full_text: str) -> list[dict]:
    """Remove duplicates and enhance trip data."""
    seen_ids = set()
    unique_trips = []

    for trip in trips:
        trip_id = trip["trip_id"]

        if trip_id not in seen_ids:
            seen_ids.add(trip_id)

            # Add calculated fields
            trip["efficiency"] = trip["credit_hours"] / max(trip["days"], 1)

            # Add trip type classification
            if trip["days"] == 1:
                trip["trip_type"] = "Day Trip"
            elif trip["days"] <= 3:
                trip["trip_type"] = "Short Trip"
            else:
                trip["trip_type"] = "Long Trip"

            unique_trips.append(trip)

    print(f"Found {len(unique_trips)} unique trips")
    return unique_trips
