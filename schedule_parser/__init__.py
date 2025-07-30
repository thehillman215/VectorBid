"""
Unified entry-point.  Call:

    from schedule_parser import parse_schedule
"""
from pathlib import Path
from .pdf_parser import parse_pdf
from .csv_parser import parse_csv
from .txt_parser import parse_txt


def parse_schedule(file_bytes: bytes, filename: str) -> list[dict]:
    suffix = Path(filename).suffix.lower()

    if suffix == ".pdf":
        return parse_pdf(file_bytes)
    if suffix in {".csv", ".tsv"}:
        return parse_csv(file_bytes)
    if suffix in {".txt"}:
        return parse_txt(file_bytes)

    raise ValueError(f"Unsupported file type: {suffix}")
