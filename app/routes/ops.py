from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def root_health():
    return {"status": "ok"}


@router.get("/ping")
def ping():
    """Simple ping endpoint for CI smoke tests"""
    return {"ping": "pong"}
