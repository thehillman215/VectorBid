from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def root_health():
    return {"ok": True, "service": "web"}
