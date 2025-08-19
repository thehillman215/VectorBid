from __future__ import annotations

import os
from typing import Any

import jwt
from fastapi import Header, HTTPException, Query, status


def require_auth(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
    api_key: str | None = Query(default=None),
) -> dict[str, Any] | None:
    """Unified auth dependency supporting JWT or API key.

    Auth mode is determined by environment configuration:
    - If ``JWT_SECRET`` is set: expects ``Authorization: Bearer <token>`` and
      returns the decoded JWT payload.
    - Else if ``VECTORBID_API_KEY`` is set: expects header ``x-api-key`` or
      query parameter ``api_key`` to match the configured key.
    - If neither is set, authentication is disabled (no-op) to preserve the
      previous default behaviour.
    """
    jwt_secret = os.environ.get("JWT_SECRET")
    api_key_expected = os.environ.get("VECTORBID_API_KEY")

    if jwt_secret:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="missing bearer token",
            )
        token = authorization.split(" ", 1)[1]
        try:
            return jwt.decode(token, jwt_secret, algorithms=["HS256"])
        except Exception as e:  # pragma: no cover - specific errors not needed
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid token",
            ) from e

    if api_key_expected:
        provided = x_api_key or api_key
        if provided != api_key_expected:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid or missing api key",
            )
        return None

    # Auth disabled
    return None
