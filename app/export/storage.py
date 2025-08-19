from __future__ import annotations

import json
import os
import re
from pathlib import Path

from typing import Union, Optional
from app.generate.layers import _canonical_sha256  # consistent with generator
from app.models import BidLayerArtifact

ArtifactLike = Union[BidLayerArtifact, dict]

_AIRLINE_RE = re.compile(r"^[A-Z0-9_-]{2,8}$")
_MONTH_RE = re.compile(r"^\d{4}-\d{2}$")


def _to_dict(a: ArtifactLike) -> dict:
    return a.model_dump() if isinstance(a, BidLayerArtifact) else dict(a)


def _sanitize_airline(v: Optional[str]) -> str:
    v = (v or "UNK").upper().strip()
    return v if _AIRLINE_RE.fullmatch(v) else "UNK"


def _sanitize_month(v: Optional[str]) -> str:
    v = (v or "0000-00").strip()
    return v if _MONTH_RE.fullmatch(v) else "0000-00"


def _compute_hash(data: dict) -> str:
    # recompute ignoring non-essential fields to keep hash stable
    core = {k: v for k, v in data.items() if k not in {"export_hash", "lint"}}
    return _canonical_sha256(core)


def write_artifact(artifact: ArtifactLike, base_dir: Path) -> Path:
    """
    Persist artifact as exports/{AIRLINE}/{YYYY-MM}/{hash}.json
    - atomic write (temp file + os.replace)
    - idempotent (same path for same content)
    """
    data = _to_dict(artifact)

    # ensure deterministic, truthful export_hash
    # always recompute the hash from core fields so a stale or missing
    # value on the input artifact cannot leak through.
    export_hash = _compute_hash(data)
    data["export_hash"] = export_hash

    airline = _sanitize_airline(data.get("airline"))
    month = _sanitize_month(data.get("month"))

    out_dir = Path(base_dir).expanduser().resolve() / airline / month
    out_dir.mkdir(parents=True, exist_ok=True)

    target = out_dir / f"{export_hash}.json"
    tmp = target.with_suffix(target.suffix + ".tmp")

    # atomic write
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, target)

    return target
