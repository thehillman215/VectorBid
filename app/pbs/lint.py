from __future__ import annotations

from typing import Any, Union, cast

from app.models import BidLayerArtifact

ArtifactLike = Union[BidLayerArtifact, dict[str, Any]]
LintMsg = dict[str, str]


def _to_plain_dict(artifact: ArtifactLike) -> dict[str, Any]:
    if isinstance(artifact, BidLayerArtifact):
        return cast(dict[str, Any], artifact.model_dump())
    return cast(dict[str, Any], dict(artifact))


def lint_shadowing(artifact: ArtifactLike) -> list[LintMsg]:
    data = _to_plain_dict(artifact)
    warnings: list[LintMsg] = []
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
            warnings.append(
                {
                    "code": "LAYER_SHADOWING",
                    "message": f"layer {n}: shadowed by previous layer",
                    "fix": f"remove layer {n}",
                }
            )
        else:
            seen.append(key)
    return warnings


def lint_mutually_exclusive_filters(artifact: ArtifactLike) -> list[LintMsg]:
    data = _to_plain_dict(artifact)
    errors: list[LintMsg] = []
    layers = data.get("layers") or []
    for layer in layers:
        n = layer.get("n")
        groups: dict[str, list[set[Any]]] = {}
        for f in layer.get("filters", []) or []:
            op = str(f.get("op", "")).upper()
            if op in {"IN", "EQUALS", "=="}:
                vals = set(f.get("values") or [])
                groups.setdefault(f.get("type"), []).append(vals)
        for t, sets in groups.items():
            if len(sets) > 1:
                intersection = set.intersection(*sets)
                if not intersection:
                    errors.append(
                        {
                            "code": "FILTERS_EXCLUSIVE",
                            "message": f"layer {n}: {t} filters are mutually exclusive",
                        }
                    )
    return errors


def lint_filter_values(artifact: ArtifactLike) -> list[LintMsg]:
    data = _to_plain_dict(artifact)
    warnings: list[LintMsg] = []
    layers = data.get("layers") or []
    for layer in layers:
        n = layer.get("n")
        for f in layer.get("filters", []) or []:
            op = str(f.get("op", "")).upper()
            values = f.get("values") or []
            t = f.get("type")
            if op in {"IN", "EQUALS", "=="} and not values:
                warnings.append(
                    {
                        "code": "FILTER_NO_VALUES",
                        "message": f"layer {n}: {t} has no values",
                    }
                )
            if op in {"IN", "EQUALS", "=="} and len(values) != len(set(values)):
                warnings.append(
                    {
                        "code": "FILTER_REDUNDANT_EQUALS",
                        "message": f"layer {n}: {t} has redundant equals",
                    }
                )
    return warnings


def lint_unreachable_layers(artifact: ArtifactLike) -> list[LintMsg]:
    data = _to_plain_dict(artifact)
    warnings: list[LintMsg] = []
    layers = data.get("layers") or []
    prev: list[tuple[int, dict[tuple[str, str], set[Any]]]] = []
    for layer in layers:
        n = layer.get("n")
        cur: dict[tuple[str, str], set[Any]] = {}
        for f in layer.get("filters", []) or []:
            op = str(f.get("op", "")).upper()
            if op in {"IN", "EQUALS", "=="}:
                cur[(f.get("type"), op)] = set(f.get("values") or [])
        for p_n, p in prev:
            if set(p.keys()).issubset(cur.keys()) and all(
                p[k].issuperset(cur[k]) for k in p.keys()
            ):
                warnings.append(
                    {
                        "code": "LAYER_UNREACHABLE",
                        "message": f"layer {n}: unreachable due to previous layer {p_n}",
                    }
                )
                break
        prev.append((n, cur))
    return warnings


def lint_artifact(artifact: ArtifactLike) -> dict[str, list[LintMsg]]:
    errors: list[LintMsg] = []
    warnings: list[LintMsg] = []
    warnings.extend(lint_shadowing(artifact))
    errors.extend(lint_mutually_exclusive_filters(artifact))
    warnings.extend(lint_unreachable_layers(artifact))
    warnings.extend(lint_filter_values(artifact))
    return {"errors": errors, "warnings": warnings}


# Back-compat alias
lint_layers = lint_artifact
