"""Custom exceptions for the PBS parser."""

from __future__ import annotations

from pathlib import Path


class ParserError(Exception):
    """Base class for parser errors."""


class FileMissingError(ParserError):
    """Raised when expected files are missing."""

    def __init__(self, path: Path) -> None:
        super().__init__(f"Expected file not found: {path}")
        self.path = path
