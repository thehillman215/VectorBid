from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from app.models import BidLayerArtifact

ArtifactLike = BidLayerArtifact | Mapping[str, Any]


def _to_plain_dict(artifact: ArtifactLike) -> dict[str, Any]:
    if isinstance(artifact, BidLayerArtifact):
        return cast(dict[str, Any], artifact.model_dump())
    return cast(dict[str, Any], dict(artifact))


def _canonical_json(data: Mapping[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def append_hash(artifact: ArtifactLike) -> dict:
    core = _to_plain_dict(artifact)
    canonical = _canonical_json(core)
    export_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    core["export_hash"] = export_hash
    return core


def write_json(artifact: ArtifactLike, path: Path) -> Path:
    data = append_hash(artifact)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
    return path
