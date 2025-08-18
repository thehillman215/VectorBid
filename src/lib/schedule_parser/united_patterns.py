# =========================================
# File: schedule_parser/united_patterns.py
# Create this new file in your schedule_parser/ directory
# =========================================

"""
United Airlines specific parsing patterns.
Built for scalability - easy to add other airlines later.
"""

import logging
import re

logger = logging.getLogger(__name__)


class UnitedPatterns:
    """United Airlines bid packet patterns - comprehensive set."""

    @staticmethod
    def get_patterns():
        """Get all United Airlines patterns ordered by confidence."""
        return [
            # Pattern 1: Standard United format (highest confidence)
            {
                "name": "ua_standard",
                "pattern": re.compile(
                    r"(?P<trip_id>UA\d+)\s+"
                    r"(?P<days>\d+)[-\s]?DAY\s+"
                    r"(?P<dates>\d{1,2}[A-Z]{3}[-\s]\d{1,2}[A-Z]{3})\s+"
                    r"(?P<routing>[A-Z]{3}(?:[-\s][A-Z]{3})+)\s+"
                    r"(?P<credit>\d+[:\.]?\d+)",
                    re.IGNORECASE,
                ),
                "confidence": 0.95,
                "description": "Standard UA format: UA123 3DAY 15JAN-17JAN DEN-LAX-DEN 18:30",
            },
            # Pattern 2: Detailed format with aircraft
            {
                "name": "ua_detailed",
                "pattern": re.compile(
                    r"(?P<trip_id>UA\d+)\s+"
                    r"(?P<aircraft>[A-Z0-9]+)?\s*"
                    r"(?P<days>\d+)[-\s]?DAY\s+"
                    r"(?P<routing>[A-Z]{3}(?:\s*[-/]\s*[A-Z]{3})+)\s+"
                    r"Credit[:\s]*(?P<credit>\d+[:\.]?\d+)",
                    re.IGNORECASE,
                ),
                "confidence": 0.9,
                "description": "UA format with aircraft: UA123 737 3DAY DEN-LAX-DEN Credit: 18:30",
            },
            # Pattern 3: Simple numeric format (common in some UA packets)
            {
                "name": "ua_numeric",
                "pattern": re.compile(
                    r"(?P<trip_id>\d+)\s+"
                    r"(?P<days>\d+)[-\s]?Day\s+Trip\s+"
                    r"Credit[:\s]*(?P<credit>\d+[:\.]?\d+)",
                    re.IGNORECASE,
                ),
                "confidence": 0.8,
                "description": "Numeric format: 123 3-Day Trip Credit: 18.30",
            },
            # Pattern 4: Table format (lowest confidence, most generic)
            {
                "name": "ua_table",
                "pattern": re.compile(
                    r"(?P<trip_id>[A-Z]{0,3}\d+)\s+"
                    r"(?P<days>\d+)\s+"
                    r"(?P<credit>\d+\.\d+)\s+"
                    r"(?P<routing>[A-Z]{3}.*[A-Z]{3})",
                    re.IGNORECASE,
                ),
                "confidence": 0.7,
                "description": "Table format: UA123 3 18.30 DEN-LAX-DEN",
            },
        ]


def parse_united_content(text_content: str, filename: str = "") -> list[dict]:
    """
    Parse United Airlines bid packet content.

    Args:
        text_content: Raw text from PDF/TXT/CSV
        filename: Original filename for logging

    Returns:
        List of parsed trip dictionaries
    """
    patterns = UnitedPatterns.get_patterns()
    trips = []
    lines = text_content.split("\n")

    logger.info(f"Parsing {len(lines)} lines with {len(patterns)} United patterns")

    for line_num, line in enumerate(lines):
        line = line.strip()

        # Skip empty or too-short lines
        if not line or len(line) < 10:
            continue

        # Skip header lines
        if any(
            header in line.upper() for header in ["TRIP", "PAIRING", "CREDIT", "ROUTING", "DAYS"]
        ):
            if not any(char.isdigit() for char in line):  # Headers usually don't have numbers
                continue

        # Try each pattern in order of confidence
        parsed_trip = None
        for pattern_info in patterns:
            pattern = pattern_info["pattern"]
            confidence = pattern_info["confidence"]
            pattern_name = pattern_info["name"]

            match = pattern.search(line)
            if match:
                parsed_trip = _extract_united_trip(
                    match, line, confidence, pattern_name, line_num + 1
                )
                if parsed_trip:
                    logger.debug(
                        f"Line {line_num + 1}: Matched {pattern_name} - {parsed_trip['trip_id']}"
                    )
                    break

        if parsed_trip:
            trips.append(parsed_trip)

    logger.info(f"Successfully parsed {len(trips)} trips from {filename}")
    return trips


def _extract_united_trip(
    match: re.Match, line: str, confidence: float, pattern_name: str, line_num: int
) -> dict | None:
    """Extract United trip data from regex match."""
    try:
        groups = match.groupdict()

        # Extract trip ID
        trip_id = groups.get("trip_id", "").strip()
        if not trip_id:
            return None

        # Ensure UA prefix for consistency
        if not trip_id.startswith("UA") and trip_id.isdigit():
            trip_id = f"UA{trip_id}"

        # Parse days
        days = 1
        if "days" in groups and groups["days"]:
            try:
                days = int(groups["days"])
            except ValueError:
                days = 1

        # Parse credit hours (handle various formats)
        credit_hours = 0.0
        if "credit" in groups and groups["credit"]:
            credit_str = (
                groups["credit"].replace(":", ".").replace("H", "").replace("CR", "").strip()
            )
            try:
                credit_hours = float(credit_str)
            except ValueError:
                logger.warning(f"Could not parse credit hours: {groups['credit']}")

        # Clean routing
        routing = groups.get("routing", "").strip()
        if routing:
            # Normalize routing format: DEN-LAX-DEN
            routing = re.sub(r"[\s/]+", "-", routing)
            routing = re.sub(r"-+", "-", routing)  # Remove multiple dashes

        # Extract dates
        dates = groups.get("dates", "").strip()

        # Enhanced weekend detection
        includes_weekend = _detect_united_weekend(line, dates, routing)

        # Extract aircraft (if present)
        aircraft = groups.get("aircraft", "").strip() or None

        # Calculate efficiency
        efficiency = credit_hours / max(days, 1) if credit_hours > 0 else 0.0

        # Build trip dictionary
        trip = {
            "trip_id": trip_id,
            "id": trip_id,  # Compatibility with existing code
            "days": days,
            "credit_hours": credit_hours,
            "credit": credit_hours,  # Compatibility
            "routing": routing,
            "dates": dates,
            "includes_weekend": includes_weekend,
            "aircraft": aircraft,
            "raw": line,
            "confidence": confidence,
            "efficiency": efficiency,
            "pattern_used": pattern_name,
            "line_number": line_num,
        }

        return trip

    except Exception as e:
        logger.warning(
            f"Failed to extract United trip from line {line_num}: {line[:50]}... Error: {e}"
        )
        return None


def _detect_united_weekend(line: str, dates: str = "", routing: str = "") -> bool:
    """
    Enhanced weekend detection for United trips.
    Looks for various weekend indicators.
    """
    content_to_check = f"{line} {dates} {routing}".upper()

    # Direct weekend indicators
    weekend_patterns = [
        r"\bSAT\b",
        r"\bSUN\b",  # SAT, SUN
        r"\bSATURDAY\b",
        r"\bSUNDAY\b",  # Full day names
        r"\bWEEKEND\b",  # Direct mention
        r"\bSA\b",
        r"\bSU\b",  # Two-letter abbreviations
        r"SAT[A-Z]",
        r"SUN[A-Z]",  # SAT/SUN followed by letter (like SATA, SUNB)
    ]

    for pattern in weekend_patterns:
        if re.search(pattern, content_to_check):
            return True

    # Date-based detection (if dates are in format like 15JAN-17JAN)
    if dates:
        # This is a simplified check - you could enhance with actual date parsing
        # For now, assume if the trip is 3+ days and spans Friday-Sunday pattern
        if len(dates) > 10 and any(day in dates.upper() for day in ["FRI", "SAT", "SUN"]):
            return True

    return False


# =========================================
# Scalable Architecture Interface
# =========================================


class AirlineParserRegistry:
    """Registry for airline-specific parsers. Easy to extend."""

    _parsers = {
        "united": parse_united_content,
        # Future: 'delta': parse_delta_content,
        # Future: 'american': parse_american_content,
    }

    @classmethod
    def parse(cls, text_content: str, airline: str, filename: str = "") -> list[dict]:
        """Parse content using airline-specific parser."""
        parser = cls._parsers.get(airline.lower())
        if parser:
            return parser(text_content, filename)
        else:
            # Fallback to United parser for now
            logger.warning(f"No parser for airline '{airline}', using United parser")
            return parse_united_content(text_content, filename)

    @classmethod
    def detect_airline(cls, text_content: str, filename: str = "") -> str:
        """Detect airline from content and filename."""
        content_lower = text_content.lower()
        filename_lower = filename.lower()

        # Check filename first
        if any(x in filename_lower for x in ["united", "ua"]):
            return "united"

        # Check content patterns
        if "united" in content_lower or re.search(r"UA\d+", text_content):
            return "united"

        # Default to United for now
        return "united"

    @classmethod
    def get_supported_airlines(cls) -> list[str]:
        """Get list of supported airlines."""
        return list(cls._parsers.keys())


# =========================================
# Integration function for existing code
# =========================================


def parse_with_united_patterns(text_content: str, filename: str = "") -> list[dict]:
    """
    Main integration function for existing VectorBid code.
    Drop-in replacement that focuses on United Airlines.
    """
    # Detect airline (will be 'united' for now)
    airline = AirlineParserRegistry.detect_airline(text_content, filename)

    # Parse with detected airline parser
    trips = AirlineParserRegistry.parse(text_content, airline, filename)

    # Log results
    if trips:
        logger.info(
            f"Parsed {len(trips)} {airline} trips with avg confidence {sum(t.get('confidence', 0) for t in trips) / len(trips):.2f}"
        )
    else:
        logger.warning(f"No trips parsed from {filename}")

    return trips
