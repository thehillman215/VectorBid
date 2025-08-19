from __future__ import annotations

import os
from typing import Any

import jwt
from fastapi import Header, HTTPException, status


def require_jwt(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    """Validate a JWT from the Authorization header.

    Expects header: ``Authorization: Bearer <token>``.
    Secret key is read from ``JWT_SECRET``. Raises 401 on failure.
    Returns the decoded token payload.
    """

    secret = os.environ.get("JWT_SECRET")
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="jwt secret not configured",
        )

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token"
        )

    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except Exception as e:  # pragma: no cover - specific errors aren't relevant
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token"
        ) from e
    return payload
