from __future__ import annotations

import csv
import io
import re
from typing import Dict, List


def parse_schedule(data: bytes, filename: str) -> List[Dict[str, str]]:
    """Parse schedule data from a CSV or simple text format.

    The parser supports two lightweight formats used in tests:
    - CSV files with columns like ``TripID``, ``Days`` and ``Credit``.
    - Plain text lines in the form ``"105 4-Day Trip Credit: 18.30"``.

    Parameters
    ----------
    data:
        Raw file contents.
    filename:
        Name of the file, used to detect the format.

    Returns
    -------
    list of dict
        Each dict contains at least the key ``id``. Additional keys such as
        ``days`` and ``credit`` are included when available.
    """
    text = data.decode("utf-8", errors="ignore")
    trips: List[Dict[str, str]] = []

    # CSV format
    if filename.lower().endswith(".csv"):
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            trip: Dict[str, str] = {
                "id": str(
                    row.get("TripID")
                    or row.get("Trip Id")
                    or row.get("trip_id")
                    or row.get("id")
                    or ""
                )
            }
            if "Days" in row:
                trip["days"] = row["Days"]
            elif "days" in row:
                trip["days"] = row["days"]
            if "Credit" in row:
                trip["credit"] = row["Credit"]
            elif "credit" in row:
                trip["credit"] = row["credit"]
            trips.append(trip)
        return trips

    # Plain text format
    pattern = re.compile(r"(\d+)\s+(\d+)-Day\s+Trip\s+Credit:\s*([\d.]+)")
    for line in text.splitlines():
        line = line.strip()
        match = pattern.match(line)
        if match:
            trip_id, days, credit = match.groups()
            trips.append({"id": trip_id, "days": days, "credit": credit, "raw": line})

    return trips
