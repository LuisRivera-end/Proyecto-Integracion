from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime
from pydantic import BaseModel
from typing import List
import asyncio
import pytz

from app.models.database import get_db

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

async def emit_caja_rapida_updated():
    try:
        from app.websocket.manager import manager
        await manager.broadcast_json({
            "type": "caja_rapida_updated",
            "data": caja_rapida_state
        })
    except Exception as e:
        print(f"Error al emitir actualización de Caja Rápida: {e}")

async def _contar_tickets_rapida_pendientes(db: AsyncSession):
    q = text("""
        SELECT COUNT(*) as total FROM Turno
        WHERE Tipo_Caja = 'rapida' AND ID_Estados = 1
    """)
    res = await db.execute(q)
    row = res.fetchone()
    return row[0] if row else 0

async def _desactivar_caja_rapida():
    global _timer_task
    _timer_task = None

    from app.models.database import get_db
    # We need a new session context here as this runs in background
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

async def _desactivar_completo_interno():
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

async def _programar_expiracion(hora_fin_str: str):
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
async def activar_caja_rapida(req: ActivarCajaRequest):
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
async def desactivar_caja_rapida_endpoint():
    await _desactivar_completo_interno()
    return {
        "message": "Caja Rápida desactivada",
        **caja_rapida_state
    }

@router.get("/caja-rapida/estado")
async def estado_caja_rapida():
    return caja_rapida_state

@router.post("/caja-rapida/check-drenaje")
async def check_drenaje(db: AsyncSession = Depends(get_db)):
    if not caja_rapida_state["expirado"]:
        return {"drenando": False}

    try:
        pendientes = await _contar_tickets_rapida_pendientes(db)
        if pendientes == 0:
            await _desactivar_completo_interno()
            return {"drenando": False, "message": "Modo drenaje finalizado"}

        return {"drenando": True, "pendientes": pendientes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
