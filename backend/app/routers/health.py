from fastapi import APIRouter

router = APIRouter(tags=["Health"])

@router.get("/v1/health")
async def health_check() -> dict:
    """Endpoint para verificar el estado de salud del sistema.
    
    Returns:
        dict: Estado del sistema (ok).
    """
    return {"status": "ok"}
