"""No-op optimizer stub for sanity checks."""

from __future__ import annotations

from .contracts import Pairing


def optimize(pairings: list[Pairing]) -> dict[str, int]:
    """Return simple counts for the supplied pairings."""

    trips = sum(len(p.trips) for p in pairings)
    return {"pairings": len(pairings), "trips": trips}


__all__ = ["optimize"]
