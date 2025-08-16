from __future__ import annotations
from typing import Dict, List
from app.models import BidLayerArtifact

def lint_artifact(artifact: BidLayerArtifact) -> Dict[str, List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    # Basic structural checks
    if not artifact.layers:
        errors.append("no layers")

    seen = set()
    for layer in artifact.layers or []:
        n = layer.get("n")
        if n in seen:
            errors.append(f"duplicate layer n={n}")
        seen.add(n)
        filters = layer.get("filters") or []
        if not filters:
            errors.append(f"layer {n}: missing filters")
        else:
            for f in filters:
                if f.get("type") == "PairingId" and not f.get("values"):
                    errors.append(f"layer {n}: PairingId has no values")

        pref = (layer.get("prefer") or "").upper()
        if pref not in {"YES", "NO", "NEUTRAL"}:
            warnings.append(f"layer {n}: unexpected prefer '{layer.get('prefer')}'")

    return {"errors": errors, "warnings": warnings}
