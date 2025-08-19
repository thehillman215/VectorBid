from __future__ import annotations

import json
from pathlib import Path


def parse_bid_packet(upload_path: str) -> dict:
    """Parse a bid packet into a canonical pairing feature dict.

    MVP v0.3: support JSON inputs only. Expected formats:
      - {"pairings": [...]} (preferred)
      - [...] (treated as pairings list)

    Returns a dict: {"pairings": [...]}.
    """

    path = Path(upload_path)
    if not path.exists():
        raise FileNotFoundError(f"bid packet not found: {upload_path}")

    if path.suffix.lower() == ".json":
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "pairings" in data:
            return {"pairings": data.get("pairings") or []}
        if isinstance(data, list):
            return {"pairings": data}
        raise ValueError("unsupported JSON schema for bid packet")

    raise ValueError("unsupported file type; only .json supported in MVP")
