"""Contracts for normalized PBS parser structures."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class Base(BaseModel):
    code: str


class Fleet(BaseModel):
    code: str


class Trip(BaseModel):
    trip_id: str
    pairing_id: str
    day: int
    origin: str
    destination: str


class Pairing(BaseModel):
    pairing_id: str
    base: str
    fleet: str
    month: date
    trips: list[Trip] = Field(default_factory=list)


__all__ = ["Base", "Fleet", "Trip", "Pairing"]
