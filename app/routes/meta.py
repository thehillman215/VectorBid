from fastapi import APIRouter

router = APIRouter()


@router.get("/api/meta/health")
def meta_health():
    return {"ok": True, "service": "api"}
