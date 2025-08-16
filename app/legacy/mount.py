from __future__ import annotations
from fastapi import APIRouter, FastAPI
from typing import Optional

def mount_legacy(app: FastAPI, import_path: str = "legacy_app:app") -> None:
    """
    Try to mount an existing WSGI legacy app at /legacy.
    If not present, expose a shim router with /legacy/health.
    """
    try:
        module_name, attr = import_path.split(":")
        mod = __import__(module_name, fromlist=[attr])
        legacy_app = getattr(mod, attr)
        # Starlette's built-in WSGI adapter (FastAPI dependency)
        from starlette.middleware.wsgi import WSGIMiddleware  # no extra dep
        app.mount("/legacy", WSGIMiddleware(legacy_app))
        return
    except Exception:
        pass  # fall through to shim

    router = APIRouter(prefix="/legacy", tags=["Legacy"])
    @router.get("/health")
    def legacy_health() -> dict:
        return {"status": "legacy-shim", "mounted": False}
    app.include_router(router)
