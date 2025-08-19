from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


def _db_path() -> Path:
    base = os.environ.get("EXPORT_DB_PATH")
    if base:
        return Path(base)
    export_dir = Path(os.environ.get("EXPORT_DIR", Path.cwd() / "exports"))
    return export_dir / "exports.db"


def insert_record(export_id: str, ctx_id: str, path: Path, sha256: str) -> None:
    """Insert a row into the exports audit table."""
    dbp = _db_path()
    dbp.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(dbp)
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS exports ("
            "id TEXT PRIMARY KEY,"
            "ctx_id TEXT,"
            "path TEXT,"
            "sha256 TEXT,"
            "created_at TEXT)"
        )
        conn.execute(
            "INSERT INTO exports (id, ctx_id, path, sha256, created_at) VALUES (?, ?, ?, ?, ?)",
            (export_id, ctx_id, str(path), sha256, datetime.utcnow().isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def get_record(export_id: str) -> Optional[dict[str, Any]]:
    dbp = _db_path()
    if not dbp.exists():
        return None
    conn = sqlite3.connect(dbp)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            "SELECT id, ctx_id, path, sha256, created_at FROM exports WHERE id = ?",
            (export_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()
