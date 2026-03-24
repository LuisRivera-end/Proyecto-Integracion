from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, func, and_
from datetime import datetime
from pydantic import BaseModel
from typing import List, Dict, Any
import asyncio
import pytz

from app.models.database import get_db
from app.models.models import Turno

router = APIRouter(prefix="/api", tags=["Caja Rápida"])

# ─── Estado en memoria ───
caja_rapida_state = {
    "activo": False,
    "expirado": False,
    "id_sector": None,
    "ventanillas": [],
    "hora_inicio": None,
    "hora_fin": None,
}

_timer_task = None
TZ = pytz.timezone('America/Mexico_City')

class ActivarCajaRequest(BaseModel):
    id_sector: int
    hora_fin: str
    ventanillas: List[int]

async def emit_caja_rapida_updated() -> None:
    """Emite el estado actualizado de la caja rápida a través de WebSockets."""
    try:
        from app.websocket.manager import manager
        await manager.broadcast_json({
            "type": "caja_rapida_updated",
            "data": caja_rapida_state
        })
    except Exception as e:
        print(f"Error al emitir actualización de Caja Rápida: {e}")

async def _contar_tickets_rapida_pendientes(db: AsyncSession) -> int:
    """Cuenta los tickets de caja rápida que están en estado pendiente (ID_Estados = 1).
    
    Args:
        db (AsyncSession): Sesión de la base de datos.
        
    Returns:
        int: Número de tickets pendientes.
    """
    q = select(func.count(Turno.ID_Turno)).where(
        and_(Turno.Tipo_Caja == 'rapida', Turno.ID_Estados == 1)
    )
    res = await db.execute(q)
    return res.scalar() or 0

async def _desactivar_caja_rapida() -> None:
    """Desactiva la caja rápida. Si hay tickets pendientes, entra en modo drenaje."""
    global _timer_task
    _timer_task = None

    from app.models.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        pendientes = await _contar_tickets_rapida_pendientes(db)

    if pendientes > 0:
        caja_rapida_state["activo"] = False
        caja_rapida_state["expirado"] = True
        print(f"⏰ Caja Rápida expirada — {pendientes} tickets pendientes, entrando en modo drenaje")
        await emit_caja_rapida_updated()
    else:
        await _desactivar_completo_interno()

async def _desactivar_completo_interno() -> None:
    """Desactiva completamente la caja rápida y resetea su estado."""
    global _timer_task
    if _timer_task and not _timer_task.done():
        _timer_task.cancel()
    _timer_task = None
    
    caja_rapida_state["activo"] = False
    caja_rapida_state["expirado"] = False
    caja_rapida_state["id_sector"] = None
    caja_rapida_state["ventanillas"] = []
    caja_rapida_state["hora_inicio"] = None
    caja_rapida_state["hora_fin"] = None
    
    print("🛑 Caja Rápida desactivada completamente")
    await emit_caja_rapida_updated()

async def _programar_expiracion(hora_fin_str: str) -> None:
    """Programa la desactivación de la caja rápida a una hora determinada.
    
    Args:
        hora_fin_str (str): Hora de finalización en formato 'HH:MM'.
    """
    global _timer_task

    if _timer_task and not _timer_task.done():
        _timer_task.cancel()
    
    try:
        ahora = datetime.now(TZ)
        hoy = ahora.date()
        hora_fin = datetime.strptime(hora_fin_str, "%H:%M").time()
        fin_dt = TZ.localize(datetime.combine(hoy, hora_fin))
        
        segundos = (fin_dt - ahora).total_seconds()
        
        if segundos <= 0:
            await _desactivar_caja_rapida()
            return
            
        print(f"⏰ Caja Rápida se desactivará en {int(segundos)} segundos ({hora_fin_str})")
        
        async def wait_and_deactivate():
            await asyncio.sleep(segundos)
            await _desactivar_caja_rapida()
            
        _timer_task = asyncio.create_task(wait_and_deactivate())
        
    except Exception as e:
        print(f"Error al programar expiración: {e}")

@router.post("/caja-rapida/activar", status_code=200)
async def activar_caja_rapida(req: ActivarCajaRequest) -> Dict[str, Any]:
    """Activa la caja rápida.
    
    Args:
        req (ActivarCajaRequest): Datos de activación de la caja rápida.
        
    Returns:
        dict: Estado actualizado de la caja rápida.
    """
    if not req.ventanillas:
        raise HTTPException(status_code=400, detail="Debes seleccionar al menos una ventanilla")

    ahora = datetime.now(TZ)

    caja_rapida_state["activo"] = True
    caja_rapida_state["expirado"] = False
    caja_rapida_state["id_sector"] = req.id_sector
    caja_rapida_state["ventanillas"] = req.ventanillas
    caja_rapida_state["hora_inicio"] = ahora.strftime("%H:%M")
    caja_rapida_state["hora_fin"] = req.hora_fin

    await _programar_expiracion(req.hora_fin)

    print(f"🚀 Caja Rápida ACTIVADA - Sector {req.id_sector}, Ventanillas {req.ventanillas}, hasta {req.hora_fin}")
    await emit_caja_rapida_updated()

    return {
        "message": "Caja Rápida activada",
        **caja_rapida_state
    }

@router.post("/caja-rapida/desactivar", status_code=200)
async def desactivar_caja_rapida_endpoint() -> Dict[str, Any]:
    """Desactiva manualmente la caja rápida.
    
    Returns:
        dict: Estado actualizado de la caja rápida.
    """
    await _desactivar_completo_interno()
    return {
        "message": "Caja Rápida desactivada",
        **caja_rapida_state
    }

@router.get("/caja-rapida/estado")
async def estado_caja_rapida() -> Dict[str, Any]:
    """Obtiene el estado actual de la caja rápida.
    
    Returns:
        dict: Estado de la caja rápida.
    """
    return caja_rapida_state

@router.post("/caja-rapida/check-drenaje")
async def check_drenaje(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Verifica si la caja rápida está en modo drenaje y si ya terminó.
    
    Args:
        db (AsyncSession): Sesión de la base de datos.
        
    Returns:
        dict: Estado de drenaje y cantidad de tickets pendientes (si aplica).
    """
    if not caja_rapida_state["expirado"]:
        return {"drenando": False}

    try:
        pendientes = await _contar_tickets_rapida_pendientes(db)
        if pendientes == 0:
            await _desactivar_completo_interno()
            return {"drenando": False, "message": "Modo drenaje finalizado"}

        return {"drenando": True, "pendientes": pendientes}
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Error de integridad en la base de datos")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")
