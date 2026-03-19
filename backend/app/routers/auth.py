from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from hashlib import sha256
from typing import List
import uuid
import asyncio
from datetime import datetime, timedelta

from app.models.database import get_db
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
        query = text("""
            SELECT 
                e.*, 
                e.Passwd,
                r.Rol, 
                ee.Nombre as Estado_Empleado,
                ev.ID_Ventanilla,
                v.Ventanilla,
                s.Sector as Sector_Ventanilla,
                sj.Sector as Sector_Jefe
            FROM Empleado e 
            LEFT JOIN Rol r ON e.ID_ROL = r.ID_Rol 
            LEFT JOIN Estado_Empleado ee ON e.ID_Estado = ee.ID_Estado
            LEFT JOIN Empleado_Ventanilla ev ON e.ID_Empleado = ev.ID_Empleado 
                AND ev.ID_Estado = 1 
                AND ev.Fecha_Termino IS NULL
            LEFT JOIN Ventanillas v ON ev.ID_Ventanilla = v.ID_Ventanilla
            LEFT JOIN Sectores s ON v.ID_Sector = s.ID_Sector
            LEFT JOIN Sectores sj ON e.ID_Sector = sj.ID_Sector
            WHERE e.Usuario = :username
        """)
        
        result = await db.execute(query, {"username": credentials.username})
        user = result.mappings().fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="Usuario no existe")

        if user["ID_Estado"] != 1:
            estado_empleado = user["Estado_Empleado"] or "Inactivo"
            raise HTTPException(status_code=403, detail=f"Usuario no activo. Estado actual: {estado_empleado}")

        hashed_pw = sha256(credentials.password.encode()).hexdigest()
        if user["Passwd"] != hashed_pw:
            raise HTTPException(status_code=401, detail="Contraseña incorrecta")

        # ── 2. Verificar si ya tiene sesión activa en DB ──
        active_check = await db.execute(text("""
            SELECT Token FROM Sesion_Activa
            WHERE ID_Empleado = :emp_id AND Activa = 1 AND Expira > NOW()
        """), {"emp_id": user["ID_Empleado"]})
        existing_session = active_check.mappings().fetchone()

        if existing_session:
            # Rechazar login — ya tiene sesión activa
            _broadcast_session_event("session_already_active", user["ID_Empleado"])
            raise HTTPException(
                status_code=403,
                detail="Este usuario ya tiene una sesión activa. Cierre la sesión antes de volver a iniciar."
            )

        # ── 3. Limpiar sesiones expiradas del usuario ──
        await db.execute(text("""
            UPDATE Sesion_Activa SET Activa = 0
            WHERE ID_Empleado = :emp_id AND (Activa = 1 AND Expira <= NOW())
        """), {"emp_id": user["ID_Empleado"]})

        # ── 4. Determinar sector ──
        if user["ID_ROL"] == 6:
            sector = user["Sector_Jefe"] or "Sin Sector"
        elif user["ID_ROL"] == 1:
            sector = "Admin"
        else:
            sector_query = text("""
                SELECT DISTINCT s.Sector
                FROM Rol_Ventanilla rv
                JOIN Ventanillas v ON rv.ID_Ventanilla = v.ID_Ventanilla
                JOIN Sectores s ON v.ID_Sector = s.ID_Sector
                WHERE rv.ID_Rol = :id_rol
                LIMIT 1
            """)
            sector_res = await db.execute(sector_query, {"id_rol": user["ID_ROL"]})
            sector_row = sector_res.mappings().fetchone()
            sector = sector_row["Sector"] if sector_row else "Desconocido"

        # ── 5. Crear nueva sesión ──
        session_token = str(uuid.uuid4())
        expira = datetime.utcnow() + timedelta(hours=SESSION_DURATION_HOURS)

        await db.execute(text("""
            INSERT INTO Sesion_Activa (Token, ID_Empleado, Activa, Expira)
            VALUES (:token, :emp_id, 1, :expira)
        """), {"token": session_token, "emp_id": user["ID_Empleado"], "expira": expira})
        await db.commit()

        # ── 6. Emitir evento WS ──
        _broadcast_session_event("session_started", user["ID_Empleado"])

        return {
            "id": user["ID_Empleado"],
            "nombre": f"{user['nombre1']} {user['Apellido1']}",
            "rol": user["ID_ROL"],
            "sector": sector,
            "estado": user["Estado_Empleado"],
            "session_token": session_token,
            "id_ventanilla": user["ID_Ventanilla"],
            "ventanilla": user["Ventanilla"],
            "sector_ventanilla": user["Sector_Ventanilla"]
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

    result = await db.execute(text("""
        SELECT sa.ID_Empleado, sa.Expira, e.ID_ROL
        FROM Sesion_Activa sa
        JOIN Empleado e ON sa.ID_Empleado = e.ID_Empleado
        WHERE sa.Token = :token AND sa.Activa = 1
    """), {"token": session_token})
    row = result.mappings().fetchone()

    if not row:
        raise HTTPException(status_code=401, detail="No session")

    # Verificar expiración
    if row["Expira"] < datetime.utcnow():
        await db.execute(text("""
            UPDATE Sesion_Activa SET Activa = 0 WHERE Token = :token
        """), {"token": session_token})
        await db.commit()
        raise HTTPException(status_code=401, detail="Session expired")

    return {"status": "ok", "user_id": row["ID_Empleado"], "rol": row["ID_ROL"]}


@router.post("/logout")
async def logout(request: Request, body: LogoutRequest, db: AsyncSession = Depends(get_db)):
    # Buscar el empleado asociado al token antes de desactivarlo
    result = await db.execute(
        text("SELECT ID_Empleado FROM Sesion_Activa WHERE Token = :token AND Activa = 1"),
        {"token": body.session_token}
    )
    row = result.mappings().fetchone()
    employee_id = row["ID_Empleado"] if row else None

    # Marcar sesión como inactiva
    await db.execute(
        text("UPDATE Sesion_Activa SET Activa = 0 WHERE Token = :token"),
        {"token": body.session_token}
    )
    await db.commit()

    # Emitir evento WS
    if employee_id:
        _broadcast_session_event("session_ended", employee_id)

    return {"message": "Sesión cerrada"}


@router.get("/roles", response_model=List[RolResponse])
async def get_roles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT ID_Rol, Rol FROM Rol ORDER BY ID_Rol"))
    return result.mappings().fetchall()

@router.get("/estados_empleado", response_model=List[EstadoEmpleadoResponse])
async def get_estados_empleado(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT ID_Estado, Nombre FROM Estado_Empleado"))
    return result.mappings().fetchall()
