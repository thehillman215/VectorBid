from __future__ import annotations

from typing import Any
from datetime import datetime

from app.db import Audit, SessionLocal


def log_event(ctx_id: str, stage: str, payload: dict[str, Any] | None = None) -> None:
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
