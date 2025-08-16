from __future__ import annotations
from pathlib import Path
from typing import Dict, Union
import json, os, re

from app.models import BidLayerArtifact
from app.generate.layers import _canonical_sha256  # consistent with generator

ArtifactLike = Union[BidLayerArtifact, Dict]

_AIRLINE_RE = re.compile(r"^[A-Z0-9_-]{2,8}$")
_MONTH_RE = re.compile(r"^\d{4}-\d{2}$")


def _to_dict(a: ArtifactLike) -> Dict:
    return a.model_dump() if isinstance(a, BidLayerArtifact) else dict(a)


def _sanitize_airline(v: str | None) -> str:
    v = (v or "UNK").upper().strip()
    return v if _AIRLINE_RE.fullmatch(v) else "UNK"


def _sanitize_month(v: str | None) -> str:
    v = (v or "0000-00").strip()
    return v if _MONTH_RE.fullmatch(v) else "0000-00"


def _compute_hash(data: Dict) -> str:
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
    export_hash = data.get("export_hash") or _compute_hash(data)
    # if present but mismatched, correct it
    if data.get("export_hash") != export_hash:
        data["export_hash"] = export_hash
    else:
        data["export_hash"] = export_hash

    airline = _sanitize_airline(data.get("airline"))
    month = _sanitize_month(data.get("month"))

    out_dir = (Path(base_dir).expanduser().resolve() / airline / month)
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
