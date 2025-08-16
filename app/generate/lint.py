from __future__ import annotations
from typing import Dict, List, Union
from app.models import BidLayerArtifact

ArtifactLike = Union[BidLayerArtifact, Dict]

def _to_plain_dict(artifact: ArtifactLike) -> Dict:
    if isinstance(artifact, BidLayerArtifact):
        return artifact.model_dump()
    return artifact  # assume dict-like

def lint_artifact(artifact: ArtifactLike) -> Dict[str, List[str]]:
    data = _to_plain_dict(artifact)
    errors: List[str] = []
    warnings: List[str] = []

    layers = data.get("layers") or []
    if not layers:
        errors.append("no layers")

    seen = set()
    for layer in layers:
        # layer is now a dict
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

        pref = str(layer.get("prefer", "")).upper()
        if pref not in {"YES", "NO", "NEUTRAL"}:
            warnings.append(f"layer {n}: unexpected prefer '{layer.get('prefer')}'")

    return {"errors": errors, "warnings": warnings}

# Back-compat alias expected by routes
def lint_layers(artifact: ArtifactLike) -> Dict[str, List[str]]:
    return lint_artifact(artifact)
