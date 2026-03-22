from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert, func, and_, or_, null
from typing import Optional, List
from hashlib import sha256

from app.models.database import get_db
from app.models.models import Empleado, Rol, EstadoEmpleado, EmpleadoVentanilla, Ventanilla, Sector, RolVentanilla, EstadoEmpleadoVentanilla, SesionActiva
from sqlalchemy.orm import aliased
from app.schemas.empleados import EmpleadoCreateReq, EmpleadoUpdateReq, EmpleadoStatusReq, EmpleadoSectorReq

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

    q = select(Empleado.ID_Sector).where(Empleado.ID_Empleado == user_id)
    res = await db.execute(q)
    jefe = res.fetchone()
    
    return jefe[0] if jefe and jefe[0] else None

@router.get("/employees")
async def get_employees(req: Request, db: AsyncSession = Depends(get_db)):
    try:
        jefe_sector_id = await _get_jefe_sector_filter(req, db)

        query = (
            select(
                Empleado.ID_Empleado.label("id"),
                Empleado.ID_ROL.label("rol_id"),
                func.concat(Empleado.nombre1, ' ', Empleado.nombre2, ' ', Empleado.Apellido1, ' ', Empleado.Apellido2).label("name"),
                Rol.Rol.label("rol"),
                EstadoEmpleado.Nombre.label("estado")
            )
            .outerjoin(Rol, Empleado.ID_ROL == Rol.ID_Rol)
            .outerjoin(EstadoEmpleado, Empleado.ID_Estado == EstadoEmpleado.ID_Estado)
            .outerjoin(
                EmpleadoVentanilla,
                and_(
                    Empleado.ID_Empleado == EmpleadoVentanilla.ID_Empleado,
                    EmpleadoVentanilla.Fecha_Termino.is_(None)
                )
            )
            .outerjoin(Ventanilla, EmpleadoVentanilla.ID_Ventanilla == Ventanilla.ID_Ventanilla)
        )

        if jefe_sector_id is not None:
            query = query.where(
                or_(
                    Empleado.ID_Sector == jefe_sector_id,
                    Ventanilla.ID_Sector == jefe_sector_id,
                    select(RolVentanilla)
                    .join(Ventanilla, RolVentanilla.ID_Ventanilla == Ventanilla.ID_Ventanilla)
                    .where(
                        and_(
                            RolVentanilla.ID_Rol == Empleado.ID_ROL,
                            Ventanilla.ID_Sector == jefe_sector_id
                        )
                    )
                    .exists()
                )
            )

        res = await db.execute(query)
        return res.mappings().fetchall()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/employees/full")
async def get_employees_full(req: Request, db: AsyncSession = Depends(get_db)):
    try:
        jefe_sector_id = await _get_jefe_sector_filter(req, db)

        SectorJefe = aliased(Sector)
        query = (
            select(
                Empleado.ID_Empleado,
                Empleado.nombre1,
                Empleado.nombre2,
                Empleado.Apellido1,
                Empleado.Apellido2,
                Empleado.Usuario,
                Empleado.ID_ROL,
                Rol.Rol,
                Empleado.ID_Estado,
                EstadoEmpleado.Nombre.label("Estado_Empleado"),
                EmpleadoVentanilla.ID_Ventanilla,
                Ventanilla.Ventanilla,
                Sector.Sector.label("Sector_Ventanilla"),
                EmpleadoVentanilla.ID_Estado.label("Estado_Ventanilla"),
                EstadoEmpleadoVentanilla.Nombre.label("Nombre_Estado_Ventanilla"),
                Empleado.ID_Sector.label("ID_Sector_Jefe"),
                SectorJefe.Sector.label("Nombre_Sector_Jefe"),
                SesionActiva.Token.label("session_token"),
                (SesionActiva.ID_Empleado.isnot(null)).label("sesion_activa")
            )
            .outerjoin(Rol, Empleado.ID_ROL == Rol.ID_Rol)
            .outerjoin(EstadoEmpleado, Empleado.ID_Estado == EstadoEmpleado.ID_Estado)
            .outerjoin(
                EmpleadoVentanilla,
                and_(
                    Empleado.ID_Empleado == EmpleadoVentanilla.ID_Empleado,
                    EmpleadoVentanilla.Fecha_Termino.is_(None)
                )
            )
            .outerjoin(Ventanilla, EmpleadoVentanilla.ID_Ventanilla == Ventanilla.ID_Ventanilla)
            .outerjoin(Sector, Ventanilla.ID_Sector == Sector.ID_Sector)
            .outerjoin(SectorJefe, Empleado.ID_Sector == SectorJefe.ID_Sector)
            .outerjoin(EstadoEmpleadoVentanilla, EmpleadoVentanilla.ID_Estado == EstadoEmpleadoVentanilla.ID_Estado)
            .outerjoin(SesionActiva, and_(
                Empleado.ID_Empleado == SesionActiva.ID_Empleado,
                SesionActiva.Activa == True
            ))
        )

        if jefe_sector_id is not None:
            query = query.where(
                or_(
                    Empleado.ID_Sector == jefe_sector_id,
                    Sector.ID_Sector == jefe_sector_id,
                    select(RolVentanilla)
                    .join(Ventanilla, RolVentanilla.ID_Ventanilla == Ventanilla.ID_Ventanilla)
                    .where(
                        and_(
                            RolVentanilla.ID_Rol == Empleado.ID_ROL,
                            Ventanilla.ID_Sector == jefe_sector_id
                        )
                    )
                    .exists()
                )
            )

        query = query.order_by(Empleado.ID_Empleado)

        res = await db.execute(query)
        return res.mappings().fetchall()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/employees/{id_empleado}/estado")
async def update_employee_status(id_empleado: int, request_data: EmpleadoStatusReq, db: AsyncSession = Depends(get_db)):
    nuevo_estado = request_data.estado
    
    if not nuevo_estado or nuevo_estado not in [1, 2, 3, 4]:
        raise HTTPException(status_code=400, detail="Estado inválido. Use: 1=Activo, 2=Suspendido, 3=Despedido, 4=Inactivo")
    
    try:
        q_emp = select(Empleado.ID_ROL).where(Empleado.ID_Empleado == id_empleado)
        res_emp = await db.execute(q_emp)
        empleado = res_emp.fetchone()
        
        if not empleado:
            raise HTTPException(status_code=404, detail="Empleado no encontrado")
            
        if empleado[0] == 1:
            raise HTTPException(status_code=403, detail="No se puede cambiar el estado del administrador")
        
        q_upd = (
            update(Empleado)
            .where(Empleado.ID_Empleado == id_empleado)
            .values(ID_Estado=nuevo_estado)
        )
        await db.execute(q_upd)
        
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
        q = (
            select(Ventanilla.ID_Ventanilla, Ventanilla.Ventanilla, Sector.Sector)
            .select_from(EmpleadoVentanilla)
            .join(Ventanilla, EmpleadoVentanilla.ID_Ventanilla == Ventanilla.ID_Ventanilla)
            .join(Sector, Ventanilla.ID_Sector == Sector.ID_Sector)
            .where(
                and_(
                    EmpleadoVentanilla.ID_Empleado == id_empleado,
                    EmpleadoVentanilla.ID_Estado == 1,
                    EmpleadoVentanilla.Fecha_Termino.is_(None)
                )
            )
            .limit(1)
        )
        
        res = await db.execute(q)
        ventanilla = res.mappings().fetchone()
        
        return ventanilla if ventanilla else {}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/employees/add", status_code=201)
async def add_employee(req_data: EmpleadoCreateReq, req: Request, db: AsyncSession = Depends(get_db)):
    try:
        passwd_hash = sha256(req_data.passwd.encode()).hexdigest()

        id_sector = req_data.id_sector
        
        rol_sesion = getattr(req.state, "rol", None)
        user_id_sesion = getattr(req.state, "user_id", None)
        
        if rol_sesion == 6:
            if user_id_sesion:
                q_jefe = select(Empleado.ID_Sector).where(Empleado.ID_Empleado == user_id_sesion)
                r_jefe = await db.execute(q_jefe)
                jefe_row = r_jefe.fetchone()
                if jefe_row:
                    id_sector = jefe_row[0]

        if req_data.id_rol == 6 and id_sector:
            q_chk = (
                select(Empleado.ID_Empleado)
                .where(and_(Empleado.ID_ROL == 6, Empleado.ID_Sector == id_sector))
                .limit(1)
            )
            r_chk = await db.execute(q_chk)
            if r_chk.fetchone():
                raise HTTPException(status_code=409, detail="Ya existe un Jefe de Departamento en este sector")

        q_ins = insert(Empleado).values(
            ID_ROL=req_data.id_rol,
            nombre1=req_data.nombre1,
            nombre2=req_data.nombre2,
            Apellido1=req_data.apellido1,
            Apellido2=req_data.apellido2,
            Usuario=req_data.usuario,
            Passwd=passwd_hash,
            ID_Estado=1,
            ID_Sector=id_sector
        )
        await db.execute(q_ins)
        
        await db.commit()
        return {"message": "Empleado agregado"}
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/employees/{id_empleado}")
async def update_employee(id_empleado: int, req_data: EmpleadoUpdateReq, req: Request, db: AsyncSession = Depends(get_db)):
    nombre1   = req_data.nombre1
    nombre2   = req_data.nombre2
    apellido1 = req_data.apellido1
    apellido2 = req_data.apellido2
    usuario   = req_data.usuario
    passwd    = req_data.passwd

    if not nombre1 or not apellido1 or not usuario:
        raise HTTPException(status_code=400, detail="nombre1, apellido1 y usuario son obligatorios")

    try:
        q_emp = select(Empleado.ID_ROL, Empleado.ID_Sector).where(Empleado.ID_Empleado == id_empleado)
        res_emp = await db.execute(q_emp)
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

        q_dup = select(Empleado.ID_Empleado).where(and_(Empleado.Usuario == usuario, Empleado.ID_Empleado != id_empleado)).limit(1)
        res_dup = await db.execute(q_dup)
        if res_dup.fetchone():
            raise HTTPException(status_code=409, detail="El nombre de usuario ya está en uso")

        if passwd:
            passwd_hash = sha256(passwd.encode()).hexdigest()
            q_upd = (
                update(Empleado)
                .where(Empleado.ID_Empleado == id_empleado)
                .values(
                    nombre1=nombre1, nombre2=nombre2, Apellido1=apellido1, 
                    Apellido2=apellido2, Usuario=usuario, Passwd=passwd_hash
                )
            )
            await db.execute(q_upd)
        else:
            q_upd = (
                update(Empleado)
                .where(Empleado.ID_Empleado == id_empleado)
                .values(
                    nombre1=nombre1, nombre2=nombre2, Apellido1=apellido1, 
                    Apellido2=apellido2, Usuario=usuario
                )
            )
            await db.execute(q_upd)

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
        q = select(Empleado.ID_Empleado).where(Empleado.Usuario == usuario).limit(1)
        res = await db.execute(q)
        exists = res.fetchone() is not None
        return {"exists": exists}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/employees/{id_empleado}/sector")
async def update_employee_sector(id_empleado: int, request_data: EmpleadoSectorReq, db: AsyncSession = Depends(get_db)):
    id_sector = request_data.id_sector
    
    try:
        q_emp = select(Empleado.ID_ROL).where(Empleado.ID_Empleado == id_empleado)
        res_emp = await db.execute(q_emp)
        emp = res_emp.fetchone()
        
        if not emp:
            raise HTTPException(status_code=404, detail="Empleado no encontrado")

        if emp[0] == 6 and id_sector:
            q_chk = (
                select(Empleado.ID_Empleado)
                .where(and_(Empleado.ID_ROL == 6, Empleado.ID_Sector == id_sector, Empleado.ID_Empleado != id_empleado))
                .limit(1)
            )
            res_chk = await db.execute(q_chk)
            if res_chk.fetchone():
                raise HTTPException(status_code=409, detail="Ya existe un Jefe de Departamento en este sector")

        q_upd = (
            update(Empleado)
            .where(Empleado.ID_Empleado == id_empleado)
            .values(ID_Sector=id_sector)
        )
        await db.execute(q_upd)
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
        q = (
            select(Empleado.ID_Sector)
            .where(and_(Empleado.ID_ROL == 6, Empleado.ID_Sector.is_not(None), Empleado.ID_Estado != 3))
        )
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
        q = (
            select(EmpleadoVentanilla.ID_Empleado)
            .where(and_(EmpleadoVentanilla.ID_Estado == 1, EmpleadoVentanilla.Fecha_Termino.is_(None)))
            .distinct()
        )
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
