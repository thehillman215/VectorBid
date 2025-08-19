from __future__ import annotations

from fastapi import Header, Query

from .auth import require_auth


def require_api_key(
    x_api_key: str | None = Header(default=None),
    api_key: str | None = Query(default=None),
) -> None:
    """Backward-compatible wrapper for API key auth."""
    return require_auth(x_api_key=x_api_key, api_key=api_key)
