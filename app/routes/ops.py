from fastapi import APIRouter

router = APIRouter()


@router.get("/ops/health")
def ops_health():
    """Operations health check"""
    return {"ok": True, "service": "ops"}


@router.get("/ops/ping")
def ops_ping():
    """Operations ping endpoint for CI smoke tests"""
    return {"pong": True, "service": "ops"}
