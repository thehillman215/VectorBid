from __future__ import annotations

import os
from pathlib import Path


def export_dir() -> Path:
    """
    Root directory for persisted exports.
    ENV override: EXPORT_DIR
    Default: <repo_root>/exports
    """
    p = os.environ.get("EXPORT_DIR")
    if p:
        return Path(p).expanduser().resolve()
    return Path(__file__).resolve().parents[2] / "exports"
