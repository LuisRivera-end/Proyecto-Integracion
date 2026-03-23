from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert, and_
from hashlib import sha256
from typing import List
import uuid
import asyncio
from datetime import datetime, timedelta

from app.models.database import get_db
from app.models.models import Rol, EstadoEmpleado, SesionActiva, Empleado, EmpleadoVentanilla, Ventanilla, Sector, RolVentanilla
from sqlalchemy.orm import aliased
from app.schemas.auth import LoginRequest, LoginResponse, LogoutRequest, RolResponse, EstadoEmpleadoResponse

router = APIRouter(prefix="/api", tags=["Autenticación"])

SESSION_DURATION_HOURS = 8


def _broadcast_session_event(event_type: str, employee_id: int):
    """Helper para emitir eventos de sesión por WS en background."""
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
            expira = datetime.utcnow() + timedelta(seconds=30) # Token corto que se renueva con actividad
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
        new_expira = datetime.utcnow() + timedelta(seconds=30)
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
    # Only allow administrators (Rol=1) to force close sessions
    # Get the requester's employee ID from the session token
    try:
        body = await request.json()
        session_token = body.get("session_token")
    except Exception:
        raise HTTPException(status_code=400, detail="Body inválido")

    if not session_token:
        raise HTTPException(status_code=401, detail="No session")

    # Verify the session token and get the requester's employee ID and role
    token_query = (
        select(SesionActiva.ID_Empleado, SesionActiva.Expira)
        .where(and_(SesionActiva.Token == session_token, SesionActiva.Activa == True))
    )
    token_result = await db.execute(token_query)
    token_row = token_result.mappings().fetchone()

    if not token_row:
        raise HTTPException(status_code=401, detail="Session expired or invalid")

    requester_id = token_row["ID_Empleado"]
    # Check if the requester's session is expired
    if token_row["Expira"] < datetime.utcnow():
        await db.execute(
            update(SesionActiva)
            .where(SesionActiva.Token == session_token)
            .values(Activa=False)
        )
        await db.commit()
        raise HTTPException(status_code=401, detail="Session expired")

    # Get the requester's role
    requester_role_query = select(Empleado.ID_ROL).where(Empleado.ID_Empleado == requester_id)
    requester_role_result = await db.execute(requester_role_query)
    requester_role_row = requester_role_result.fetchone()
    if not requester_role_row:
        raise HTTPException(status_code=500, detail="Requester employee not found")
    requester_role = requester_role_row[0]

    # Only allow Rol=1 (Admin)
    if requester_role != 1:
        raise HTTPException(status_code=403, detail="Solo los administradores pueden forzar el cierre de sesiones")

    # Extend admin session (sliding window) - same logic as check_session
    if requester_role in (1, 6):
        new_expira = datetime.utcnow() + timedelta(seconds=30)
        await db.execute(
            update(SesionActiva)
            .where(SesionActiva.Token == session_token)
            .values(Expira=new_expira)
        )

    # Proceed to force close the target employee's session(s)
    # Set Activa=0 for any active session of the target employee
    await db.execute(
        update(SesionActiva)
        .where(and_(SesionActiva.ID_Empleado == id_empleado, SesionActiva.Activa == True))
        .values(Activa=False)
    )

    # Also terminate any active ventanilla assignment
    await db.execute(
        update(EmpleadoVentanilla)
        .where(
            and_(
                EmpleadoVentanilla.ID_Empleado == id_empleado,
                EmpleadoVentanilla.Fecha_Termino.is_(None),
                EmpleadoVentanilla.ID_Estado == 1
            )
        )
        .values(Fecha_Termino=datetime.utcnow(), ID_Estado=2)
    )

    await db.commit()

    # Emit WS event to notify that the session was forced closed (so the client can react if still connected)
    _broadcast_session_event("session_force_closed", id_empleado)
    _broadcast_session_event("ventanilla_status_changed", id_empleado)

    return {"message": f"Sesión forzada a cerrar para el empleado {id_empleado}"}


@router.get("/roles", response_model=List[RolResponse])
async def get_roles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Rol.ID_Rol, Rol.Rol).order_by(Rol.ID_Rol))
    return result.mappings().fetchall()


@router.get("/estados_empleado", response_model=List[EstadoEmpleadoResponse])
async def get_estados_empleado(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EstadoEmpleado.ID_Estado, EstadoEmpleado.Nombre))
    return result.mappings().fetchall()
