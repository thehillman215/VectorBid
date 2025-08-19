from __future__ import annotations

from typing import Any

from fastapi import Header

from .auth import require_auth


def require_jwt(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    """Backward-compatible wrapper for JWT auth."""
    return require_auth(authorization=authorization)
