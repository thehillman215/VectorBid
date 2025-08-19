from __future__ import annotations

from datetime import datetime
from typing import Any

from app.db import Audit, SessionLocal


def log_event(ctx_id: str, stage: str, payload: Optional[dict[str, Any]] = None) -> None:
    """Persist an audit event for a context."""
    if not ctx_id:
        return
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
