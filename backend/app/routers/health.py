from fastapi import APIRouter

router = APIRouter(tags=["Health"])

@router.get("/v1/health")
async def health_check():
    return {"status": "ok"}
