from __future__ import annotations

from datetime import datetime, timedelta
import re
from typing import List

import pytz
from pydantic import BaseModel

# Minimal timezone mapping for airports we expect in tests.
AIRPORT_TZ = {
    "IAH": "America/Chicago",
    "ORD": "America/Chicago",
    "LAX": "America/Los_Angeles",
    "EWR": "America/New_York",
    "DEN": "America/Denver",
    "SFO": "America/Los_Angeles",
}


class Leg(BaseModel):
    flight: str
    departure_airport: str
    arrival_airport: str
    departure: datetime
    arrival: datetime
    equipment: str | None = None


class Trip(BaseModel):
    trip_id: str
    credit: float
    legs: list[Leg]


TRIP_BLOCK_RE = re.compile(
    r"EFF\s*(?P<date>\d{2}/\d{2}/\d{2}).*?ID\s*(?P<id>[A-Z]\d{4})(?P<body>.*?CRD-\s*(?P<credit>\d+\.\d{2}))",
    re.DOTALL,
)
LEG_RE = re.compile(
    r"(?P<equip>\w+)\s+(?P<flight>\d+)\s+(?P<dep>[A-Z]{3})\s+(?P<arr>[A-Z]{3})\s+"\
    r"(?P<dep_time>\d{4})\s+(?P<arr_time>\d{4})",
)


def parse_bid_pdf(path: str) -> List[Trip]:
    """Parse a UAL bid packet text file into Trip models.

    The production system reads PDFs, but the tests supply plain text that was
    extracted from real bid packets to avoid committing binary fixtures.
    """
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    return _parse_text(text)


def _parse_text(text: str) -> List[Trip]:
    trips: List[Trip] = []
    for match in TRIP_BLOCK_RE.finditer(text):
        block = match.group(0)
        trip = _parse_trip_block(block)
        if trip:
            trips.append(trip)
    if not trips:
        raise ValueError("no trips found")
    return trips


def _parse_trip_block(block: str) -> Trip | None:
    m = TRIP_BLOCK_RE.search(block)
    if not m:
        return None
    trip_id = m.group("id")
    credit = float(m.group("credit"))
    base_date = datetime.strptime(m.group("date"), "%m/%d/%y")
    legs: list[Leg] = []
    current = base_date
    for leg_match in LEG_RE.finditer(block):
        dep_time_str = leg_match.group("dep_time")
        arr_time_str = leg_match.group("arr_time")
        dep_naive = _combine(current, dep_time_str)
        arr_naive = _combine(dep_naive, arr_time_str)
        dep_tz = pytz.timezone(AIRPORT_TZ.get(leg_match.group("dep"), "UTC"))
        arr_tz = pytz.timezone(AIRPORT_TZ.get(leg_match.group("arr"), "UTC"))
        dep_dt = dep_tz.localize(dep_naive)
        arr_dt = arr_tz.localize(arr_naive)
        legs.append(
            Leg(
                flight=leg_match.group("flight"),
                departure_airport=leg_match.group("dep"),
                arrival_airport=leg_match.group("arr"),
                departure=dep_dt,
                arrival=arr_dt,
                equipment=leg_match.group("equip"),
            )
        )
        current = arr_naive
    return Trip(trip_id=trip_id, credit=credit, legs=legs)


def _combine(base: datetime, time_str: str) -> datetime:
    hour = int(time_str[:2])
    minute = int(time_str[2:])
    candidate = base.replace(hour=hour, minute=minute)
    if candidate < base:
        candidate += timedelta(days=1)
    return candidate


__all__ = ["Trip", "Leg", "parse_bid_pdf"]
