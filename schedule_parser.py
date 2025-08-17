"""Compatibility shim for schedule parser.

This module exposes :func:`parse_schedule` for tests and other callers by
importing the implementation from :mod:`src.lib.schedule_parser`.
"""

from src.lib.schedule_parser import parse_schedule

__all__ = ["parse_schedule"]
