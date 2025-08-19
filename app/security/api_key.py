from __future__ import annotations

from fastapi import Header, Query

from .auth import require_auth


def get_api_key(
    x_api_key: str | None = Header(default=None),
    api_key: str | None = Query(default=None),
) -> str | None:
    """Extract API key from header or query parameter."""
    return x_api_key or api_key


def require_api_key(
    authorization=Header(None),
    x_api_key=Header(None),
    api_key=Query(None),
) -> None:
    """Backward-compatible wrapper supporting both JWT and API key auth."""
    return require_auth(authorization=authorization, x_api_key=x_api_key, api_key=api_key)
