"""
Authentication router handles user login, session validation, logout,
forced session closure, emergency PIN validation, and session reset.
It also provides lookup endpoints for roles and employee statuses.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, update, insert, delete, and_, text
from hashlib import sha256
from typing import List
import uuid
import asyncio
import secrets
from datetime import datetime, timedelta

from app.models.database import get_db
from app.models.models import Rol, EstadoEmpleado, SesionActiva, Empleado, EmpleadoVentanilla, Ventanilla, Sector, RolVentanilla
from sqlalchemy.orm import aliased
from app.schemas.auth import LoginRequest, LoginResponse, LogoutRequest, RolResponse, EstadoEmpleadoResponse

router = APIRouter(prefix="/api", tags=["Autenticación"])

SESSION_DURATION_HOURS = 8


def _broadcast_session_event(event_type: str, employee_id: int):
    """
    Helper function to emit session events via WebSocket in the background.
    
    Args:
        event_type (str): The type of session event to broadcast (e.g., 'session_started', 'session_ended')
        employee_id (int): The ID of the employee associated with the event
    
    Returns:
        None: This function runs asynchronously in the background and doesn't return a value
    """
    async def _emit():
        try:
            from app.websocket.manager import manager
            await manager.broadcast_json({
                "type": event_type,
                "employee_id": employee_id
            })
        except Exception as e:
            print(f"⚠️ Error emitiendo {event_type}: {e}")

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_emit())
    except RuntimeError:
        pass


@router.post("/login", response_model=LoginResponse)
async def login(request: Request, credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        # ── 1. Buscar usuario ──
        SectorJefe = aliased(Sector)
        query = (
            select(
                Empleado,
                Rol.Rol.label("Rol"),
                EstadoEmpleado.Nombre.label("Estado_Empleado"),
                EmpleadoVentanilla.ID_Ventanilla,
                Ventanilla.Ventanilla.label("Ventanilla"),
                Sector.Sector.label("Sector_Ventanilla"),
                SectorJefe.Sector.label("Sector_Jefe")
            )
            .outerjoin(Rol, Empleado.ID_ROL == Rol.ID_Rol)
            .outerjoin(EstadoEmpleado, Empleado.ID_Estado == EstadoEmpleado.ID_Estado)
            .outerjoin(
                EmpleadoVentanilla,
                and_(
                    Empleado.ID_Empleado == EmpleadoVentanilla.ID_Empleado,
                    EmpleadoVentanilla.ID_Estado == 1,
                    EmpleadoVentanilla.Fecha_Termino.is_(None)
                )
            )
            .outerjoin(Ventanilla, EmpleadoVentanilla.ID_Ventanilla == Ventanilla.ID_Ventanilla)
            .outerjoin(Sector, Ventanilla.ID_Sector == Sector.ID_Sector)
            .outerjoin(SectorJefe, Empleado.ID_Sector == SectorJefe.ID_Sector)
            .where(Empleado.Usuario == credentials.username)
        )

        result = await db.execute(query)
        user_row = result.mappings().fetchone()

        if not user_row:
            raise HTTPException(status_code=404, detail="Usuario no existe")

        user = user_row["Empleado"]
        if user.ID_Estado != 1:
            estado_empleado = user_row["Estado_Empleado"] or "Inactivo"
            raise HTTPException(status_code=403, detail=f"Usuario no activo. Estado actual: {estado_empleado}")

        hashed_pw = sha256(credentials.password.encode()).hexdigest()
        if user.Passwd != hashed_pw:
            raise HTTPException(status_code=401, detail="Contraseña incorrecta")

        # ── 2. Verificar si ya tiene sesión activa en DB ──
        active_check = await db.execute(
            select(SesionActiva.Token)
            .where(
                and_(
                    SesionActiva.ID_Empleado == user.ID_Empleado,
                    SesionActiva.Activa == True,
                    SesionActiva.Expira > datetime.utcnow()
                )
            )
        )
        existing_session = active_check.mappings().fetchone()

        if existing_session:
            # Rechazar login — ya tiene sesión activa
            _broadcast_session_event("session_already_active", user.ID_Empleado)
            raise HTTPException(
                status_code=403,
                detail="Este usuario ya tiene una sesión activa. Cierre la sesión antes de volver a iniciar."
            )

        # ── 3. Limpiar sesiones expiradas del usuario ──
        await db.execute(
            update(SesionActiva)
            .where(
                and_(
                    SesionActiva.ID_Empleado == user.ID_Empleado,
                    SesionActiva.Activa == True,
                    SesionActiva.Expira <= datetime.utcnow()
                )
            )
            .values(Activa=False)
        )

        # ── 4. Determinar sector ──
        if user.ID_ROL == 6:
            sector = user_row["Sector_Jefe"] or "Sin Sector"
        elif user.ID_ROL == 1:
            sector = "Admin"
        else:
            sector_query = (
                select(Sector.Sector)
                .select_from(RolVentanilla)
                .join(Ventanilla, RolVentanilla.ID_Ventanilla == Ventanilla.ID_Ventanilla)
                .join(Sector, Ventanilla.ID_Sector == Sector.ID_Sector)
                .where(RolVentanilla.ID_Rol == user.ID_ROL)
                .distinct()
                .limit(1)
            )
            sector_res = await db.execute(sector_query)
            sector_row_val = sector_res.mappings().fetchone()
            sector = sector_row_val["Sector"] if sector_row_val else "Desconocido"

        # ── 5. Validar que operadores tengan ventanilla asignada ──
        # Roles que requieren ventanilla: todos excepto Admin (1) y Subjefe (6)
        if user.ID_ROL not in (1, 6):
            if not user_row["ID_Ventanilla"]:
                raise HTTPException(
                    status_code=403,
                    detail="No tiene una ventanilla asignada. Contacte al administrador."
                )

        # ── 6. Crear nueva sesión con expiración basada en el rol ──
        session_token = str(uuid.uuid4())
        if user.ID_ROL in (1, 6): # Admin o Jefe de Departamento
            expira = datetime.utcnow() + timedelta(minutes=5) # Token corto que se renueva con actividad
        else:
            expira = datetime.utcnow() + timedelta(hours=SESSION_DURATION_HOURS) # 8 horas fijo para otros roles

        await db.execute(
            insert(SesionActiva)
            .values(Token=session_token, ID_Empleado=user.ID_Empleado, Activa=True, Expira=expira)
        )
        await db.commit()

        # ── 7. Emitir evento WS ──
        _broadcast_session_event("session_started", user.ID_Empleado)

        return {
            "id": user.ID_Empleado,
            "nombre": f"{user.nombre1} {user.Apellido1}",
            "rol": user.ID_ROL,
            "sector": sector,
            "id_sector": user.ID_Sector,
            "estado": user_row["Estado_Empleado"],
            "session_token": session_token,
            "id_ventanilla": user_row["ID_Ventanilla"],
            "ventanilla": user_row["Ventanilla"],
            "sector_ventanilla": user_row["Sector_Ventanilla"]
        }

    except HTTPException:
        raise
    except Exception as e:
        import sys, traceback
        traceback.print_exc(file=sys.stderr)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/check_session")
async def check_session(request: Request, db: AsyncSession = Depends(get_db)):
    """Valida un session_token contra la BD. Retorna user_id y rol."""
    try:
        body = await request.json()
        session_token = body.get("session_token")
    except Exception:
        raise HTTPException(status_code=400, detail="Body inválido")

    if not session_token:
        raise HTTPException(status_code=401, detail="No session")

    query = (
        select(SesionActiva.ID_Empleado, SesionActiva.Expira, Empleado.ID_ROL)
        .join(Empleado, SesionActiva.ID_Empleado == Empleado.ID_Empleado)
        .where(and_(SesionActiva.Token == session_token, SesionActiva.Activa == True))
    )
    result = await db.execute(query)
    row = result.mappings().fetchone()

    if not row:
        raise HTTPException(status_code=401, detail="No session")

    # Verificar expiración
    if row["Expira"] < datetime.utcnow():
        await db.execute(
            update(SesionActiva)
            .where(SesionActiva.Token == session_token)
            .values(Activa=False)
        )
        await db.commit()
        raise HTTPException(status_code=401, detail="Session expired")

    # Extender sesión para administradores y jefes de departamento (ventana deslizante)
    if row["ID_ROL"] in (1, 6):
        new_expira = datetime.utcnow() + timedelta(minutes=5)
        await db.execute(
            update(SesionActiva)
            .where(SesionActiva.Token == session_token)
            .values(Expira=new_expira)
        )
        await db.commit()

    return {"status": "ok", "user_id": row["ID_Empleado"], "rol": row["ID_ROL"]}


@router.post("/logout")
async def logout(request: Request, body: LogoutRequest, db: AsyncSession = Depends(get_db)):
    # Buscar el empleado asociado al token antes de desactivarlo
    result = await db.execute(
        select(SesionActiva.ID_Empleado)
        .where(and_(SesionActiva.Token == body.session_token, SesionActiva.Activa == True))
    )
    row = result.mappings().fetchone()
    employee_id = row["ID_Empleado"] if row else None

    # Marcar sesión como inactiva
    await db.execute(
        update(SesionActiva)
        .where(SesionActiva.Token == body.session_token)
        .values(Activa=False)
    )
    await db.commit()

    # Emitir evento WS
    if employee_id:
        _broadcast_session_event("session_ended", employee_id)

    return {"message": "Sesión cerrada"}


@router.post("/employees/{id_empleado}/forzar-cierre", status_code=200)
async def force_close_session(id_empleado: int, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        body = await request.json()
        session_token = body.get("session_token")
    except Exception:
        raise HTTPException(status_code=400, detail="Body inválido")

    if not session_token:
        raise HTTPException(status_code=401, detail="No session")

    # ── 1. Validar token + obtener rol en una sola consulta (JOIN) ──
    result = await db.execute(
        select(SesionActiva.ID_Empleado, SesionActiva.Expira, Empleado.ID_ROL)
        .join(Empleado, SesionActiva.ID_Empleado == Empleado.ID_Empleado)
        .where(and_(SesionActiva.Token == session_token, SesionActiva.Activa == True))
    )
    row = result.mappings().fetchone()

    if not row:
        raise HTTPException(status_code=401, detail="Session expired or invalid")

    if row["Expira"] < datetime.utcnow():
        await db.execute(
            update(SesionActiva).where(SesionActiva.Token == session_token).values(Activa=False)
        )
        await db.commit()
        raise HTTPException(status_code=401, detail="Session expired")

    if row["ID_ROL"] != 1:
        raise HTTPException(status_code=403, detail="Solo los administradores pueden forzar el cierre de sesiones")

    # ── 2. Extender sesión admin + cerrar sesión del empleado objetivo (un solo commit) ──
    await db.execute(
        update(SesionActiva).where(SesionActiva.Token == session_token)
        .values(Expira=datetime.utcnow() + timedelta(minutes=5))
    )
    await db.execute(
        update(SesionActiva)
        .where(and_(SesionActiva.ID_Empleado == id_empleado, SesionActiva.Activa == True))
        .values(Activa=False)
    )
    await db.commit()

    _broadcast_session_event("session_force_closed", id_empleado)

    return {"message": f"Sesión forzada a cerrar para el empleado {id_empleado}"}


# ── Tokens temporales para emergencia ──
_emergency_tokens: dict[str, float] = {}


@router.post("/emergency/validate-pin")
async def validate_emergency_pin(request: Request):
    """Valida el PIN de emergencia y retorna un token temporal."""
    from app.config import settings

    try:
        body = await request.json()
        pin = body.get("pin", "")
    except Exception:
        raise HTTPException(status_code=400, detail="Body inválido")

    if str(pin) != settings.SESSION_RESET_PIN:
        raise HTTPException(status_code=403, detail="PIN incorrecto")

    # Generar token temporal (válido 5 minutos)
    temp_token = secrets.token_urlsafe(32)
    _emergency_tokens[temp_token] = datetime.utcnow().timestamp() + 300

    # Limpiar tokens expirados
    now = datetime.utcnow().timestamp()
    expired = [k for k, v in _emergency_tokens.items() if v < now]
    for k in expired:
        del _emergency_tokens[k]

    return {"status": "ok", "emergency_token": temp_token}


@router.post("/emergency/reset-sessions")
async def reset_sessions(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Elimina todas las sesiones activas. Requiere token de emergencia.
    
    Args:
        request: Objeto Request de FastAPI para obtener el cuerpo JSON.
        db: Sesión de base de datos asíncrona inyectada por dependencia.
    
    Returns:
        dict: Mensaje de éxito indicando que todas las sesiones fueron reiniciadas.
    
    Raises:
        HTTPException: Si el cuerpo es inválido, el token de emergencia es incorrecto o expirado.
    """
    try:
        body = await request.json()
        emergency_token = body.get("emergency_token", "")
    except Exception:
        raise HTTPException(status_code=400, detail="Body inválido")

    # Validar token temporal
    expiry = _emergency_tokens.get(emergency_token)
    if not expiry or expiry < datetime.utcnow().timestamp():
        raise HTTPException(status_code=403, detail="Token de emergencia inválido o expirado")

    # Consumir token (uso único)
    del _emergency_tokens[emergency_token]

    # Eliminar todas las sesiones activas usando ORM en lugar de TRUNCATE crudo
    await db.execute(delete(SesionActiva))
    await db.commit()

    # Notificar por WS a todos los clientes
    try:
        from app.websocket.manager import manager
        await manager.broadcast_json({"type": "sessions_reset"})
    except Exception:
        pass

    return {"status": "ok", "message": "Todas las sesiones han sido reiniciadas"}


@router.get("/roles", response_model=List[RolResponse])
async def get_roles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Rol.ID_Rol, Rol.Rol).order_by(Rol.ID_Rol))
    return result.mappings().fetchall()


@router.get("/estados_empleado", response_model=List[EstadoEmpleadoResponse])
async def get_estados_empleado(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EstadoEmpleado.ID_Estado, EstadoEmpleado.Nombre))
    return result.mappings().fetchall()
