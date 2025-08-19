from __future__ import annotations

from typing import Any, Optional

from fastapi import Header

from .auth import require_auth


def require_jwt(authorization: Optional[str] = Header(default=None)) -> dict[str, Any]:
    """Backward-compatible wrapper for JWT auth."""
    return require_auth(authorization=authorization)
