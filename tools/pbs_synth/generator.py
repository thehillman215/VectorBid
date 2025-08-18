"""Deterministic synthetic dataset generator."""

from __future__ import annotations

from datetime import date
from random import Random

from .schema import Pairing, Trip

AIRPORTS = ["EWR", "ORD", "IAH", "DEN", "LAX"]


def generate_pairings(
    month: date, base: str, fleet: str, seed: int, count: int = 5
) -> list[Pairing]:
    """Generate a deterministic list of pairings."""

    rng = Random(seed)
    pairings: list[Pairing] = []
    for i in range(count):
        pairing_id = f"{base}-{fleet}-{i + 1:03d}"
        trips: list[Trip] = []
        for t in range(rng.randint(1, 3)):
            day = rng.randint(1, 28)
            origin = rng.choice(AIRPORTS)
            dest_choices = [a for a in AIRPORTS if a != origin]
            destination = rng.choice(dest_choices)
            trips.append(
                Trip(
                    trip_id=f"{pairing_id}-T{t + 1}",
                    pairing_id=pairing_id,
                    day=day,
                    origin=origin,
                    destination=destination,
                )
            )
        pairings.append(
            Pairing(
                pairing_id=pairing_id, base=base, fleet=fleet, month=month, trips=trips
            )
        )
    return pairings


__all__ = ["generate_pairings"]
