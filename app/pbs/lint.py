from __future__ import annotations

from typing import Any, cast

from app.models import BidLayerArtifact

ArtifactLike = BidLayerArtifact | dict[str, Any]


def _to_plain_dict(artifact: ArtifactLike) -> dict[str, Any]:
    if isinstance(artifact, BidLayerArtifact):
        return cast(dict[str, Any], artifact.model_dump())
    return cast(dict[str, Any], dict(artifact))


def lint_shadowing(artifact: ArtifactLike) -> list[str]:
    data = _to_plain_dict(artifact)
    warnings: list[str] = []
    seen: list[tuple] = []
    layers = data.get("layers") or []
    for layer in layers:
        n = layer.get("n")
        key = tuple(
            sorted(
                (
                    f.get("type"),
                    f.get("op"),
                    tuple(f.get("values", [])),
                )
                for f in layer.get("filters", [])
            )
        )
        if key in seen:
            warnings.append(f"layer {n}: shadowed by previous layer")
        else:
            seen.append(key)
    return warnings


def lint_unreachable(artifact: ArtifactLike) -> list[str]:
    data = _to_plain_dict(artifact)
    warnings: list[str] = []
    layers = data.get("layers") or []
    for layer in layers:
        n = layer.get("n")
        for f in layer.get("filters", []) or []:
            op = str(f.get("op", "")).upper()
            values = f.get("values") or []
            if op in {"IN", "EQUALS", "=="} and not values:
                warnings.append(f"layer {n}: {f.get('type')} has no values")
            if op in {"IN", "EQUALS", "=="} and len(values) != len(set(values)):
                warnings.append(f"layer {n}: {f.get('type')} has redundant equals")
    return warnings


def lint_artifact(artifact: ArtifactLike) -> dict[str, list[str]]:
    warnings: list[str] = []
    warnings.extend(lint_shadowing(artifact))
    warnings.extend(lint_unreachable(artifact))
    return {"errors": [], "warnings": warnings}


# Back-compat alias
lint_layers = lint_artifact
