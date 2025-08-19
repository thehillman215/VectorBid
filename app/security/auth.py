from __future__ import annotations

import os
from typing import Any

import jwt
from fastapi import Header, HTTPException, Query, status


def require_auth(
    authorization=Header(None),
    x_api_key=Header(None),
    api_key=Query(None),
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
        # Handle both string and Header object cases
        auth_value = str(authorization) if authorization is not None else None
        if not auth_value or auth_value == "None" or not auth_value.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="missing bearer token",
            )
        token = auth_value.split(" ", 1)[1]
        try:
            return jwt.decode(token, jwt_secret, algorithms=["HS256"])
        except Exception as e:  # pragma: no cover - specific errors not needed
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid token",
            ) from e

    if api_key_expected:
        x_api_key_str = str(x_api_key) if x_api_key is not None else None
        api_key_str = str(api_key) if api_key is not None else None

        # Handle case where None converts to string "None"
        if x_api_key_str == "None":
            x_api_key_str = None
        if api_key_str == "None":
            api_key_str = None

        provided = x_api_key_str or api_key_str
        if provided != api_key_expected:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid or missing api key",
            )
        return None

    # Auth disabled
    return None
