from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def root_health():
    return {"ok": True, "service": "web"}


@router.get("/ping")
def ping():
    """Simple ping endpoint for CI smoke tests"""
    return {"pong": True, "service": "web"}
