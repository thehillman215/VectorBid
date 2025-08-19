from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from app.models import BidLayerArtifact, CandidateSchedule, FeatureBundle


def _next_month_tag(dt: datetime) -> str:
    y, m = dt.year, dt.month
    if m == 12:
        y, m = y + 1, 1
    else:
        m += 1
    return f"{y:04d}-{m:02d}"


def _canonical_sha256(obj) -> str:
    """Deterministic hash for export fingerprint."""
    data = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def candidates_to_layers(topk: list[CandidateSchedule], bundle: FeatureBundle) -> BidLayerArtifact:
    # Build simple 1:1 layers from the ranked candidates
    layers = []
    for i, c in enumerate(topk, start=1):
        layers.append(
            {
                "n": i,
                "filters": [{"type": "PairingId", "op": "IN", "values": [c.candidate_id]}],
                "prefer": "YES",
            }
        )

    # Airline priority: preference_schema.airline → context.airline → "UNK"
    airline = bundle.preference_schema.airline or bundle.context.airline or "UNK"

    month = _next_month_tag(datetime.now(timezone.utc))
    artifact = BidLayerArtifact(
        airline=airline,
        format="PBS2",
        month=month,
        layers=layers,
        lint={"errors": [], "warnings": []},
        export_hash="",  # fill after hashing
    )

    # Compute export hash deterministically from a plain dict (exclude non-essential fields)
    core = artifact.model_dump(exclude={"lint", "export_hash"})
    artifact.export_hash = _canonical_sha256(core)
    return artifact
