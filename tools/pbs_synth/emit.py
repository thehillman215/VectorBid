"""Writers for synthetic dataset outputs."""

from __future__ import annotations

import csv
from collections.abc import Sequence
from pathlib import Path

from .schema import Pairing


def write_csv(pairings: Sequence[Pairing], out_dir: Path) -> None:
    """Write pairings and trips to CSV files."""

    out_dir.mkdir(parents=True, exist_ok=True)
    pairings_path = out_dir / "pairings.csv"
    trips_path = out_dir / "trips.csv"
    with pairings_path.open("w", newline="") as pf:
        writer = csv.writer(pf)
        writer.writerow(["pairing_id", "base", "fleet", "month"])
        for pairing in pairings:
            writer.writerow(
                [
                    pairing.pairing_id,
                    pairing.base,
                    pairing.fleet,
                    pairing.month.isoformat(),
                ]
            )
    with trips_path.open("w", newline="") as tf:
        writer = csv.writer(tf)
        writer.writerow(["trip_id", "pairing_id", "day", "origin", "destination"])
        for pairing in pairings:
            for trip in pairing.trips:
                writer.writerow(
                    [
                        trip.trip_id,
                        trip.pairing_id,
                        trip.day,
                        trip.origin,
                        trip.destination,
                    ]
                )


def write_jsonl(pairings: Sequence[Pairing], out_dir: Path) -> None:
    """Write pairings and trips to JSON Lines files."""

    out_dir.mkdir(parents=True, exist_ok=True)
    pairings_path = out_dir / "pairings.jsonl"
    trips_path = out_dir / "trips.jsonl"
    with pairings_path.open("w") as pf:
        for pairing in pairings:
            pf.write(pairing.model_dump_json() + "\n")
    with trips_path.open("w") as tf:
        for pairing in pairings:
            for trip in pairing.trips:
                tf.write(trip.model_dump_json() + "\n")


__all__ = ["write_csv", "write_jsonl"]
