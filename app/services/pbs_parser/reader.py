"""Load synthetic datasets into parser contracts."""

from __future__ import annotations

import csv
from pathlib import Path

from .contracts import Pairing, Trip
from .errors import FileMissingError


def load(path: Path) -> list[Pairing]:
    """Load dataset from *path* detecting format automatically."""

    if (path / "pairings.csv").exists():
        return load_csv(path)
    if (path / "pairings.jsonl").exists():
        return load_jsonl(path)
    raise FileMissingError(path)


def load_csv(path: Path) -> list[Pairing]:
    pairings_file = path / "pairings.csv"
    trips_file = path / "trips.csv"
    if not pairings_file.exists():
        raise FileMissingError(pairings_file)
    if not trips_file.exists():
        raise FileMissingError(trips_file)

    pairings: dict[str, Pairing] = {}
    with pairings_file.open() as pf:
        reader = csv.DictReader(pf)
        for row in reader:
            pairings[row["pairing_id"]] = Pairing(
                pairing_id=row["pairing_id"],
                base=row["base"],
                fleet=row["fleet"],
                month=row["month"],
                trips=[],
            )
    with trips_file.open() as tf:
        reader = csv.DictReader(tf)
        for row in reader:
            trip = Trip(
                trip_id=row["trip_id"],
                pairing_id=row["pairing_id"],
                day=int(row["day"]),
                origin=row["origin"],
                destination=row["destination"],
            )
            pairings[row["pairing_id"]].trips.append(trip)
    return list(pairings.values())


def load_jsonl(path: Path) -> list[Pairing]:
    pairings_file = path / "pairings.jsonl"
    if not pairings_file.exists():
        raise FileMissingError(pairings_file)

    pairings: list[Pairing] = []
    with pairings_file.open() as pf:
        for line in pf:
            pairings.append(Pairing.model_validate_json(line))
    return pairings


__all__ = ["load", "load_csv", "load_jsonl"]
