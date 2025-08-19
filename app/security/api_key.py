from __future__ import annotations

from fastapi import Header, Query

from .auth import require_auth


def require_api_key(
    authorization=Header(None),
    x_api_key=Header(None),
    api_key=Query(None),
) -> None:
    """Backward-compatible wrapper supporting both JWT and API key auth."""
    return require_auth(authorization=authorization, x_api_key=x_api_key, api_key=api_key)
