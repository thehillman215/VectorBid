"""
Unified entry-point.  Call:

    from schedule_parser import parse_schedule
"""

import mimetypes
import pathlib

from .csv_parser import parse_csv
from .txt_parser import parse_txt

__all__ = ["parse_schedule"]


def parse_schedule(file_bytes: bytes, filename: str) -> list[dict]:
    """Dispatch to the correct parser based on extension."""
    ext = pathlib.Path(filename).suffix.lower()

    if ext in {".csv", ".tsv"}:
        return parse_csv(file_bytes)
    elif ext in {".txt", ".log"}:
        return parse_txt(file_bytes)
    elif ext in {".pdf"}:
        # lazy import so PyMuPDF loads only when required
        from .pdf_parser import parse_pdf

        return parse_pdf(file_bytes)
    else:
        raise ValueError(f"Unsupported schedule type: {ext}")
