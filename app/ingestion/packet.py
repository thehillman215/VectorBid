from __future__ import annotations

from pathlib import Path
import json
from typing import Optional

from app.audit import log_event
from app.db import BidPackage, SessionLocal

def parse_bid_packet(upload_path: str, ctx_id: Optional[str] = None) -> dict:
    """Parse a bid packet into a canonical pairing feature dict.

    MVP v0.3: support JSON inputs only. Expected formats:
      - {"pairings": [...]} (preferred)
      - [...] (treated as pairings list)

    Returns a dict: {"pairings": [...]}."""

    path = Path(upload_path)
    if not path.exists():
        raise FileNotFoundError(f"bid packet not found: {upload_path}")

    if path.suffix.lower() == ".json":
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "pairings" in data:
            parsed = {"pairings": data.get("pairings") or []}
        elif isinstance(data, list):
            parsed = {"pairings": data}
        else:
            raise ValueError("unsupported JSON schema for bid packet")

        if ctx_id:
            with SessionLocal() as db:
                db.add(BidPackage(ctx_id=ctx_id, data=parsed))
                db.commit()
            log_event(ctx_id, "ingest", {"pairings": len(parsed.get("pairings", []))})
        return parsed

    raise ValueError("unsupported file type; only .json supported in MVP")
