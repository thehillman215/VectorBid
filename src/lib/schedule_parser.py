import csv
import os
import re
from io import StringIO
from typing import List, TypedDict

__all__ = ["parse_schedule"]


class Trip(TypedDict, total=False):
    """Dictionary representation of a single trip."""

    id: str
    days: int
    credit: float
    raw: str


def parse_schedule(data: bytes, filename: str) -> List[Trip]:
    """Parse schedule data from CSV or simple text format.

    Parameters
    ----------
    data:
        Raw file contents as bytes.
    filename:
        Name of the uploaded file used to determine the format.

    Returns
    -------
    list of Trip
        Parsed trip entries. Each entry contains at minimum an ``id`` key and
        may include ``days``, ``credit``, and ``raw`` fields.
    """
    text = data.decode("utf-8")
    ext = os.path.splitext(filename)[1].lower()
    trips: List[Trip] = []

    if ext == ".csv":
        reader = csv.DictReader(StringIO(text))
        for row in reader:
            trip_id = row.get("TripID") or row.get("id") or row.get("ID")
            days = row.get("Days") or row.get("days")
            credit = row.get("Credit") or row.get("credit")
            if trip_id:
                trip: Trip = {"id": str(trip_id)}
                if days:
                    try:
                        trip["days"] = int(days)
                    except ValueError:
                        pass
                if credit:
                    try:
                        trip["credit"] = float(credit)
                    except ValueError:
                        pass
                trips.append(trip)
        return trips

    pattern = re.compile(
        r"(?P<id>\d+)\s+(?P<days>\d+)-Day\s+Trip\s+Credit:\s*(?P<credit>[\d.]+)",
        re.IGNORECASE,
    )
    for line in text.splitlines():
        match = pattern.search(line)
        if match:
            trip = {
                "id": match.group("id"),
                "days": int(match.group("days")),
                "credit": float(match.group("credit")),
                "raw": line.strip(),
            }
            trips.append(trip)
    return trips
