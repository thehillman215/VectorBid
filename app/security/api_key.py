from __future__ import annotations

from typing import Optional

from fastapi import Header, Query

from .auth import require_auth


def get_api_key(
    x_api_key: Optional[str] = Header(default=None),
    api_key: Optional[str] = Query(default=None),
) -> Optional[str]:
    """Extract API key from header or query parameter."""
    return x_api_key or api_key


def require_api_key(
    authorization=Header(None),
    x_api_key=Header(None),
    api_key=Query(None),
) -> None:
    """Backward-compatible wrapper supporting both JWT and API key auth."""
    return require_auth(authorization=authorization, x_api_key=x_api_key, api_key=api_key)
