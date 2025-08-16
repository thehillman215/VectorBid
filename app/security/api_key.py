from __future__ import annotations
import os
from typing import Optional
from fastapi import Header, Query, HTTPException, status

def require_api_key(
    x_api_key: Optional[str] = Header(default=None),
    api_key: Optional[str] = Query(default=None),
) -> None:
    """
    If VECTORBID_API_KEY is set:
      - accept either header `x-api-key` or query param `?api_key=`
      - else 401 Unauthorized
    If not set: no-op (keeps tests/local dev unchanged).
    """
    expected = os.environ.get("VECTORBID_API_KEY")
    if not expected:
        return  # auth disabled
    provided = x_api_key or api_key
    if provided != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or missing api key",
        )
