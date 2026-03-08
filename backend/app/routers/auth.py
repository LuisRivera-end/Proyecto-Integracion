from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from hashlib import sha256
from typing import List

from app.models.database import get_db
from app.schemas.auth import LoginRequest, LoginResponse, RolResponse, EstadoEmpleadoResponse

router = APIRouter(prefix="/api", tags=["Autenticación"])

# Tracking de sesiones activo manual (similar to Flask logic)
active_sessions = {}

@router.post("/login", response_model=LoginResponse)
async def login(request: Request, credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
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

        # Check in active sessions
        if user["ID_Empleado"] in active_sessions:
            # Replicating existing logic for concurrent WS checks
            from app.websocket.manager import manager # We will define this later
            if str(user["ID_Empleado"]) in manager.active_connections.get("empleados", {}):
                raise HTTPException(status_code=403, detail="El usuario ya tiene una sesión iniciada en otro dispositivo o pestaña")

        hashed_pw = sha256(credentials.password.encode()).hexdigest()
        if user["Passwd"] != hashed_pw:
            raise HTTPException(status_code=401, detail="Contraseña incorrecta")

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

        active_sessions[user["ID_Empleado"]] = True
        request.session["user_id"] = user["ID_Empleado"]
        request.session["rol"] = user["ID_ROL"]

        return {
            "id": user["ID_Empleado"],
            "nombre": f"{user['nombre1']} {user['Apellido1']}",
            "rol": user["ID_ROL"],
            "sector": sector,
            "estado": user["Estado_Empleado"],
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

@router.get("/check_session")
async def check_session(request: Request):
    if "user_id" in request.session:
        return {"status": "ok", "user_id": request.session["user_id"]}
    raise HTTPException(status_code=401, detail="No session")

@router.post("/logout")
async def logout(request: Request):
    user_id = request.session.get("user_id")
    if user_id is not None:
        active_sessions.pop(user_id, None)
    request.session.clear()
    return {"message": "Sesión cerrada"}

@router.get("/roles", response_model=List[RolResponse])
async def get_roles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT ID_Rol, Rol FROM Rol ORDER BY ID_Rol"))
    return result.mappings().fetchall()

@router.get("/estados_empleado", response_model=List[EstadoEmpleadoResponse])
async def get_estados_empleado(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT ID_Estado, Nombre FROM Estado_Empleado"))
    return result.mappings().fetchall()
