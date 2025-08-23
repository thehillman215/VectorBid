from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

try:
    from app.db import Audit, SessionLocal
    DB_AVAILABLE = True
except Exception:
    DB_AVAILABLE = False
    Audit = None
    SessionLocal = None


def log_event(ctx_id: str, stage: str, payload: Optional[dict[str, Any]] = None) -> None:
    """Persist an audit event for a context."""
    if not ctx_id or not DB_AVAILABLE:
        return
    try:
        with SessionLocal() as db:
            db.add(
                Audit(
                    ctx_id=ctx_id,
                    stage=stage,
                    payload=payload or {},
                    timestamp=datetime.utcnow(),
                )
            )
            db.commit()
    except Exception:
        # Silently fail if database is not available
        pass
