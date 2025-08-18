"""Typed models for synthetic PBS datasets."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class Base(BaseModel):
    """Pilot base representation."""

    code: str


class Fleet(BaseModel):
    """Aircraft fleet representation."""

    code: str


class Trip(BaseModel):
    """Individual trip within a pairing."""

    trip_id: str
    pairing_id: str
    day: int
    origin: str
    destination: str


class Pairing(BaseModel):
    """Grouping of trips for bidding."""

    pairing_id: str
    base: str
    fleet: str
    month: date
    trips: list[Trip] = Field(default_factory=list)


__all__ = ["Base", "Fleet", "Trip", "Pairing"]
