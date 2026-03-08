from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional, List
from hashlib import sha256

from app.models.database import get_db

router = APIRouter(prefix="/api", tags=["Empleados"])

async def _get_jefe_sector_filter(req: Request, db: AsyncSession):
    """Refactorización de permisos con dependencias JWT/Session"""
    # NOTE: As of Flask to FastAPI migration, we need to adapt Session logic.
    # Currently assuming middleware sets req.state.rol and req.state.user_id
    # Alternatively this can be passed from a JWT Dependency in `deps.py`
    
    rol = getattr(req.state, "rol", None)
    user_id = getattr(req.state, "user_id", None)
    
    if rol != 6 or not user_id:
        return None

    q = text("SELECT ID_Sector FROM Empleado WHERE ID_Empleado = :user_id")
    res = await db.execute(q, {"user_id": user_id})
    jefe = res.fetchone()
    
    return jefe[0] if jefe and jefe[0] else None

@router.get("/employees")
async def get_employees(req: Request, db: AsyncSession = Depends(get_db)):
    try:
        jefe_sector_id = await _get_jefe_sector_filter(req, db)

        query = """
            SELECT 
                e.ID_Empleado AS id, 
                e.ID_ROL AS rol_id,
                CONCAT(e.nombre1, ' ', e.nombre2, ' ', e.Apellido1, ' ', e.Apellido2) AS name,
                r.Rol AS rol,
                ee.Nombre AS estado
            FROM Empleado e
            LEFT JOIN Rol r ON e.ID_ROL = r.ID_Rol
            LEFT JOIN Estado_Empleado ee ON e.ID_Estado = ee.ID_Estado
            LEFT JOIN Empleado_Ventanilla ev ON e.ID_Empleado = ev.ID_Empleado
                AND ev.Fecha_Termino IS NULL
            LEFT JOIN Ventanillas v ON ev.ID_Ventanilla = v.ID_Ventanilla
        """
        params = {}

        if jefe_sector_id is not None:
            query += """
                WHERE (
                    e.ID_Sector = :jefe_sector_id
                    OR v.ID_Sector = :jefe_sector_id
                    OR EXISTS (
                        SELECT 1 FROM Rol_Ventanilla rv
                        JOIN Ventanillas vr ON rv.ID_Ventanilla = vr.ID_Ventanilla
                        WHERE rv.ID_Rol = e.ID_ROL AND vr.ID_Sector = :jefe_sector_id
                    )
                )
            """
            params["jefe_sector_id"] = jefe_sector_id

        res = await db.execute(text(query), params)
        return res.mappings().fetchall()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/employees/full")
async def get_employees_full(req: Request, db: AsyncSession = Depends(get_db)):
    try:
        jefe_sector_id = await _get_jefe_sector_filter(req, db)

        query = """
            SELECT 
                e.ID_Empleado,
                e.nombre1,
                e.nombre2,
                e.Apellido1,
                e.Apellido2,
                e.Usuario,
                e.ID_ROL,
                r.Rol,
                e.ID_Estado,
                ee.Nombre as Estado_Empleado,
                ev.ID_Ventanilla,
                v.Ventanilla,
                s.Sector as Sector_Ventanilla,
                ev.ID_Estado as Estado_Ventanilla,
                eev.Nombre as Nombre_Estado_Ventanilla,
                e.ID_Sector as ID_Sector_Jefe,
                sj.Sector as Nombre_Sector_Jefe
            FROM Empleado e
            LEFT JOIN Rol r ON e.ID_ROL = r.ID_Rol
            LEFT JOIN Estado_Empleado ee ON e.ID_Estado = ee.ID_Estado
            LEFT JOIN Empleado_Ventanilla ev ON e.ID_Empleado = ev.ID_Empleado 
                AND ev.Fecha_Termino IS NULL
            LEFT JOIN Ventanillas v ON ev.ID_Ventanilla = v.ID_Ventanilla
            LEFT JOIN Sectores s ON v.ID_Sector = s.ID_Sector
            LEFT JOIN Sectores sj ON e.ID_Sector = sj.ID_Sector
            LEFT JOIN Estado_empleado_ventanilla eev ON ev.ID_Estado = eev.ID_Estado
        """
        params = {}

        if jefe_sector_id is not None:
            query += """
                WHERE (
                    e.ID_Sector = :jefe_sector_id
                    OR s.ID_Sector = :jefe_sector_id
                    OR EXISTS (
                        SELECT 1 FROM Rol_Ventanilla rv
                        JOIN Ventanillas vr ON rv.ID_Ventanilla = vr.ID_Ventanilla
                        WHERE rv.ID_Rol = e.ID_ROL AND vr.ID_Sector = :jefe_sector_id
                    )
                )
            """
            params["jefe_sector_id"] = jefe_sector_id

        query += " ORDER BY e.ID_Empleado"

        res = await db.execute(text(query), params)
        return res.mappings().fetchall()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/employees/{id_empleado}/estado")
async def update_employee_status(id_empleado: int, request_data: dict, db: AsyncSession = Depends(get_db)):
    nuevo_estado = request_data.get("estado")
    
    if not nuevo_estado or nuevo_estado not in [1, 2, 3, 4]:
        raise HTTPException(status_code=400, detail="Estado inválido. Use: 1=Activo, 2=Suspendido, 3=Despedido, 4=Inactivo")
    
    try:
        q_emp = text("SELECT ID_ROL FROM Empleado WHERE ID_Empleado = :id_empleado")
        res_emp = await db.execute(q_emp, {"id_empleado": id_empleado})
        empleado = res_emp.fetchone()
        
        if not empleado:
            raise HTTPException(status_code=404, detail="Empleado no encontrado")
            
        if empleado[0] == 1:
            raise HTTPException(status_code=403, detail="No se puede cambiar el estado del administrador")
        
        q_upd = text("""
            UPDATE Empleado
            SET ID_Estado = :nuevo_estado
            WHERE ID_Empleado = :id_empleado
        """)
        await db.execute(q_upd, {"nuevo_estado": nuevo_estado, "id_empleado": id_empleado})
        
        await db.commit()
        return {"message": "Estado actualizado correctamente"}
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/empleado/{id_empleado}/ventanilla-activa")
async def get_ventanilla_activa_empleado(id_empleado: int, db: AsyncSession = Depends(get_db)):
    try:
        q = text("""
            SELECT 
                v.ID_Ventanilla,
                v.Ventanilla,
                s.Sector
            FROM Empleado_Ventanilla ev
            JOIN Ventanillas v ON ev.ID_Ventanilla = v.ID_Ventanilla
            JOIN Sectores s ON v.ID_Sector = s.ID_Sector
            WHERE ev.ID_Empleado = :id_empleado 
                AND ev.ID_Estado = 1
                AND ev.Fecha_Termino IS NULL
            LIMIT 1
        """)
        
        res = await db.execute(q, {"id_empleado": id_empleado})
        ventanilla = res.mappings().fetchone()
        
        return ventanilla if ventanilla else {}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/employees/add", status_code=201)
async def add_employee(req_data: dict, req: Request, db: AsyncSession = Depends(get_db)):
    try:
        passwd_hash = sha256(req_data['passwd'].encode()).hexdigest()

        id_sector = req_data.get('id_sector')
        
        rol_sesion = getattr(req.state, "rol", None)
        user_id_sesion = getattr(req.state, "user_id", None)
        
        if rol_sesion == 6:
            if user_id_sesion:
                q_jefe = text("SELECT ID_Sector FROM Empleado WHERE ID_Empleado = :jefe_id")
                r_jefe = await db.execute(q_jefe, {"jefe_id": user_id_sesion})
                jefe_row = r_jefe.fetchone()
                if jefe_row:
                    id_sector = jefe_row[0]

        if int(req_data['id_rol']) == 6 and id_sector:
            q_chk = text("SELECT 1 FROM Empleado WHERE ID_ROL = 6 AND ID_Sector = :id_sector LIMIT 1")
            r_chk = await db.execute(q_chk, {"id_sector": id_sector})
            if r_chk.fetchone():
                raise HTTPException(status_code=409, detail="Ya existe un Jefe de Departamento en este sector")

        q_ins = text("""
            INSERT INTO Empleado
            (ID_ROL, nombre1, nombre2, Apellido1, Apellido2, Usuario, Passwd, ID_Estado, ID_Sector)
            VALUES (:id_rol, :n1, :n2, :a1, :a2, :usr, :pwd, 1, :id_sector)
        """)
        await db.execute(q_ins, {
            "id_rol": req_data['id_rol'],
            "n1": req_data['nombre1'],
            "n2": req_data['nombre2'],
            "a1": req_data['apellido1'],
            "a2": req_data['apellido2'],
            "usr": req_data['usuario'],
            "pwd": passwd_hash,
            "id_sector": id_sector
        })
        
        await db.commit()
        return {"message": "Empleado agregado"}
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/employees/{id_empleado}")
async def update_employee(id_empleado: int, req_data: dict, req: Request, db: AsyncSession = Depends(get_db)):
    nombre1   = req_data.get("nombre1", "").strip()
    nombre2   = req_data.get("nombre2", "").strip()
    apellido1 = req_data.get("apellido1", "").strip()
    apellido2 = req_data.get("apellido2", "").strip()
    usuario   = req_data.get("usuario", "").strip()
    passwd    = req_data.get("passwd", "").strip()

    if not nombre1 or not apellido1 or not usuario:
        raise HTTPException(status_code=400, detail="nombre1, apellido1 y usuario son obligatorios")

    try:
        q_emp = text("SELECT ID_ROL, ID_Sector FROM Empleado WHERE ID_Empleado = :id_empleado")
        res_emp = await db.execute(q_emp, {"id_empleado": id_empleado})
        emp = res_emp.mappings().fetchone()
        
        if not emp:
            raise HTTPException(status_code=404, detail="Empleado no encontrado")
            
        if emp["ID_ROL"] == 1:
            raise HTTPException(status_code=403, detail="No se puede editar al administrador")

        rol_sesion = getattr(req.state, "rol", None)
        if rol_sesion == 6:
            jefe_sector_id = await _get_jefe_sector_filter(req, db)
            if jefe_sector_id is not None and emp.get("ID_Sector") != jefe_sector_id:
                raise HTTPException(status_code=403, detail="No tiene permisos para editar este empleado")

        q_dup = text("SELECT 1 FROM Empleado WHERE Usuario = :usuario AND ID_Empleado != :id_empleado LIMIT 1")
        res_dup = await db.execute(q_dup, {"usuario": usuario, "id_empleado": id_empleado})
        if res_dup.fetchone():
            raise HTTPException(status_code=409, detail="El nombre de usuario ya está en uso")

        if passwd:
            passwd_hash = sha256(passwd.encode()).hexdigest()
            q_upd = text("""
                UPDATE Empleado
                SET nombre1=:n1, nombre2=:n2, Apellido1=:a1, Apellido2=:a2, Usuario=:usr, Passwd=:pwd
                WHERE ID_Empleado=:id_empleado
            """)
            await db.execute(q_upd, {
                "n1": nombre1, "n2": nombre2, "a1": apellido1, "a2": apellido2, 
                "usr": usuario, "pwd": passwd_hash, "id_empleado": id_empleado
            })
        else:
            q_upd = text("""
                UPDATE Empleado
                SET nombre1=:n1, nombre2=:n2, Apellido1=:a1, Apellido2=:a2, Usuario=:usr
                WHERE ID_Empleado=:id_empleado
            """)
            await db.execute(q_upd, {
                "n1": nombre1, "n2": nombre2, "a1": apellido1, "a2": apellido2, 
                "usr": usuario, "id_empleado": id_empleado
            })

        await db.commit()
        return {"message": "Empleado actualizado correctamente"}

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/employees/exists/{usuario}")
async def check_user_exists(usuario: str, db: AsyncSession = Depends(get_db)):
    try:
        q = text("SELECT 1 FROM Empleado WHERE Usuario = :usuario LIMIT 1")
        res = await db.execute(q, {"usuario": usuario})
        exists = res.fetchone() is not None
        return {"exists": exists}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/employees/{id_empleado}/sector")
async def update_employee_sector(id_empleado: int, request_data: dict, db: AsyncSession = Depends(get_db)):
    id_sector = request_data.get("id_sector")
    
    try:
        q_emp = text("SELECT ID_ROL FROM Empleado WHERE ID_Empleado = :id_empleado")
        res_emp = await db.execute(q_emp, {"id_empleado": id_empleado})
        emp = res_emp.fetchone()
        
        if not emp:
            raise HTTPException(status_code=404, detail="Empleado no encontrado")

        if emp[0] == 6 and id_sector:
            q_chk = text("""
                SELECT 1 FROM Empleado 
                WHERE ID_ROL = 6 AND ID_Sector = :id_sector AND ID_Empleado != :id_empleado LIMIT 1
            """)
            res_chk = await db.execute(q_chk, {"id_sector": id_sector, "id_empleado": id_empleado})
            if res_chk.fetchone():
                raise HTTPException(status_code=409, detail="Ya existe un Jefe de Departamento en este sector")

        q_upd = text("""
            UPDATE Empleado
            SET ID_Sector = :id_sector
            WHERE ID_Empleado = :id_empleado
        """)
        await db.execute(q_upd, {"id_sector": id_sector, "id_empleado": id_empleado})
        await db.commit()
        
        return {"message": "Sector actualizado correctamente"}
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sectores/ocupados")
async def get_sectores_ocupados(db: AsyncSession = Depends(get_db)):
    try:
        q = text("""
            SELECT ID_Sector FROM Empleado
            WHERE ID_ROL = 6 AND ID_Sector IS NOT NULL AND ID_Estado != 3
        """)
        res = await db.execute(q)
        rows = res.fetchall()
        return [r[0] for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/employees/activos")
async def get_active_employees_ids(db: AsyncSession = Depends(get_db)):
    """Retorna lista de IDs de empleados que tienen una sesión en DB Y están conectados por WS"""
    try:
        # 1. Obtener empleados con sesión activa en DB
        q = text("SELECT DISTINCT ID_Empleado FROM Empleado_Ventanilla WHERE ID_Estado = 1 AND Fecha_Termino IS NULL")
        res = await db.execute(q)
        db_active_ids = {r[0] for r in res.fetchall()}
        
        # 2. Obtener empleados con WebSocket activo
        from app.websocket.manager import manager
        ws_active_ids = manager.active_ventanilla_employees
        
        # 3. Intersección: Solo los que están en ambos
        real_active_ids = list(db_active_ids.intersection(ws_active_ids))
        
        return real_active_ids
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
