from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, update, insert, func, and_
from fastapi.responses import FileResponse
from pydantic import BaseModel
import asyncio
import os
from datetime import datetime

from app.models.database import get_db
from app.models.models import Ventanilla, EmpleadoVentanilla, Empleado, RolVentanilla, Sector, Rol
from app.utils.helpers import speak_to_file
from app.schemas.tickets import TurnoRequest
from app.schemas.ventanillas import VentanillaUpdateReq, EmpleadoVentanillaUpdateReq
from app.websocket.manager import manager

router = APIRouter(prefix="/api", tags=["Ventanillas"])

class EmpleadoVentanillaReq(BaseModel):
    id_empleado: int
    id_ventanilla: int

@router.get("/sectores/{id_sector}/ventanillas")
async def get_ventanillas_por_sector(id_sector: int, db: AsyncSession = Depends(get_db)):
    """Retorna todas las ventanillas de un sector con información de si están ocupadas"""
    try:
        q = (
            select(
                Ventanilla.ID_Ventanilla.label("ID_Ventanilla"),
                Ventanilla.Ventanilla.label("Ventanilla"),
                Ventanilla.Activa.label("Activa"),
                EmpleadoVentanilla.ID_Empleado.label("id_empleado"),
                func.concat(Empleado.nombre1, ' ', Empleado.Apellido1).label("nombre_empleado")
            )
            .outerjoin(
                EmpleadoVentanilla,
                and_(
                    Ventanilla.ID_Ventanilla == EmpleadoVentanilla.ID_Ventanilla,
                    EmpleadoVentanilla.ID_Estado == 1,
                    EmpleadoVentanilla.Fecha_Termino.is_(None)
                )
            )
            .outerjoin(Empleado, EmpleadoVentanilla.ID_Empleado == Empleado.ID_Empleado)
            .where(Ventanilla.ID_Sector == id_sector)
        )
        res = await db.execute(q)
        return res.mappings().fetchall()
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Error de integridad en la base de datos")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/ventanillas/libres/{id_empleado}")
async def ventanillas_libres(id_empleado: int, db: AsyncSession = Depends(get_db)):
    try:
        query_emp = select(Empleado.ID_ROL).where(Empleado.ID_Empleado == id_empleado)
        res_emp = await db.execute(query_emp)
        empleado = res_emp.fetchone()
        
        if not empleado:
            raise HTTPException(status_code=404, detail="Empleado no encontrado")
            
        id_rol = empleado[0]

        query_ventanillas = (
            select(
                Ventanilla.ID_Ventanilla.label("ID_Ventanilla"),
                Ventanilla.Ventanilla.label("Ventanilla"),
                Sector.Sector.label("Sector")
            )
            .join(RolVentanilla, Ventanilla.ID_Ventanilla == RolVentanilla.ID_Ventanilla)
            .join(Sector, Ventanilla.ID_Sector == Sector.ID_Sector)
            .outerjoin(
                EmpleadoVentanilla,
                and_(
                    Ventanilla.ID_Ventanilla == EmpleadoVentanilla.ID_Ventanilla,
                    EmpleadoVentanilla.ID_Estado == 1
                )
            )
            .where(
                and_(
                    EmpleadoVentanilla.ID_Ventanilla.is_(None),
                    RolVentanilla.ID_Rol == id_rol,
                    Ventanilla.Activa == True
                )
            )
        )

        res_ventanillas = await db.execute(query_ventanillas)
        return res_ventanillas.mappings().fetchall()
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error en ventanillas_libres: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/ventanilla/iniciar", status_code=201)
async def iniciar_ventanilla(req: EmpleadoVentanillaReq, db: AsyncSession = Depends(get_db)):
    try:
        # Check if ventanilla is occupied
        q_occ = (
            select(EmpleadoVentanilla.ID_Asignacion)
            .where(
                and_(
                    EmpleadoVentanilla.ID_Ventanilla == req.id_ventanilla,
                    EmpleadoVentanilla.ID_Estado == 1,
                    EmpleadoVentanilla.Fecha_Termino.is_(None)
                )
            )
            .limit(1)
        )
        res_occ = await db.execute(q_occ)
        if res_occ.fetchone():
            raise HTTPException(status_code=400, detail="Ventanilla ocupada")

        # Terminate previous sessions of this employee
        q_term = (
            update(EmpleadoVentanilla)
            .where(
                and_(
                    EmpleadoVentanilla.ID_Empleado == req.id_empleado,
                    EmpleadoVentanilla.ID_Estado == 1,
                    EmpleadoVentanilla.Fecha_Termino.is_(None)
                )
            )
            .values(Fecha_Termino=func.now(), ID_Estado=2)
        )
        await db.execute(q_term)

        # Insert new session
        q_ins = insert(EmpleadoVentanilla).values(
            ID_Empleado=req.id_empleado,
            ID_Ventanilla=req.id_ventanilla,
            Fecha_Inicio=func.now(),
            Fecha_Termino=None,
            ID_Estado=1
        )
        await db.execute(q_ins)
        
        # Get Ventanilla Info
        q_info = (
            select(Ventanilla.ID_Ventanilla, Ventanilla.Ventanilla, Sector.Sector)
            .join(Sector, Ventanilla.ID_Sector == Sector.ID_Sector)
            .where(Ventanilla.ID_Ventanilla == req.id_ventanilla)
        )
        res_info = await db.execute(q_info)
        ventanilla_info = res_info.mappings().fetchone()
        
        await db.commit()
        
        if not ventanilla_info:
            return {
                "message": "Ventanilla iniciada pero no se pudo obtener información",
                "ID_Ventanilla": req.id_ventanilla,
                "Nombre_Ventanilla": "Desconocida",
                "Sector_Ventanilla": "Desconocido"
            }
        
        return {
            "message": "Ventanilla iniciada correctamente",
            "ID_Ventanilla": ventanilla_info["ID_Ventanilla"],
            "Nombre_Ventanilla": ventanilla_info["Ventanilla"],
            "Sector_Ventanilla": ventanilla_info["Sector"]
        }
        
    except HTTPException:
        await db.rollback()
        raise
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Error de integridad en la base de datos")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/ventanillas/disponibles/{id_rol}")
async def get_ventanillas_disponibles(
    id_rol: int, 
    excluir_empleado: int = Query(None), 
    db: AsyncSession = Depends(get_db)):
    try:
        if excluir_empleado:
            subq = (
                select(EmpleadoVentanilla.ID_Ventanilla)
                .where(
                    and_(
                        EmpleadoVentanilla.Fecha_Termino.is_(None),
                        EmpleadoVentanilla.ID_Estado == 1,
                        EmpleadoVentanilla.ID_Empleado != excluir_empleado
                    )
                )
            )
            query = (
                select(Ventanilla.ID_Ventanilla, Ventanilla.Ventanilla)
                .join(RolVentanilla, Ventanilla.ID_Ventanilla == RolVentanilla.ID_Ventanilla)
                .where(
                    and_(
                        RolVentanilla.ID_Rol == id_rol,
                        Ventanilla.Activa == True,
                        Ventanilla.ID_Ventanilla.notin_(subq)
                    )
                )
                .order_by(Ventanilla.ID_Ventanilla)
            )
            res = await db.execute(query)
        else:
            subq = (
                select(EmpleadoVentanilla.ID_Ventanilla)
                .where(
                    and_(
                        EmpleadoVentanilla.Fecha_Termino.is_(None),
                        EmpleadoVentanilla.ID_Estado == 1
                    )
                )
            )
            query = (
                select(Ventanilla.ID_Ventanilla, Ventanilla.Ventanilla)
                .join(RolVentanilla, Ventanilla.ID_Ventanilla == RolVentanilla.ID_Ventanilla)
                .where(
                    and_(
                        RolVentanilla.ID_Rol == id_rol,
                        Ventanilla.Activa == True,
                        Ventanilla.ID_Ventanilla.notin_(subq)
                    )
                )
                .order_by(Ventanilla.ID_Ventanilla)
            )
            res = await db.execute(query)
        
        return res.mappings().fetchall()

    except IntegrityError:
        raise HTTPException(status_code=400, detail="Error de integridad en la base de datos")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.put("/ventanillas/{id_ventanilla}")
async def update_ventanilla(id_ventanilla: int, req: VentanillaUpdateReq, db: AsyncSession = Depends(get_db)):
    """Actualiza el estado (Activa) o el nombre de una ventanilla"""
    try:
        # Verificar que la ventanilla existe
        q_check = select(Ventanilla.ID_Ventanilla, Ventanilla.Ventanilla, Ventanilla.Activa).where(Ventanilla.ID_Ventanilla == id_ventanilla)
        res_check = await db.execute(q_check)
        ventanilla = res_check.mappings().fetchone()
        if not ventanilla:
            raise HTTPException(status_code=404, detail="Ventanilla no encontrada")

        # Cambiar estado activa/inactiva
        if req.activa is not None:
            nueva_activa = bool(int(req.activa))
            # Si se va a desactivar, verificar que no esté en uso
            if not nueva_activa:
                q_uso = (
                    select(EmpleadoVentanilla.ID_Asignacion)
                    .where(
                        and_(
                            EmpleadoVentanilla.ID_Ventanilla == id_ventanilla,
                            EmpleadoVentanilla.ID_Estado == 1,
                            EmpleadoVentanilla.Fecha_Termino.is_(None)
                        )
                    )
                    .limit(1)
                )
                res_uso = await db.execute(q_uso)
                if res_uso.fetchone():
                    raise HTTPException(status_code=400, detail="No se puede deshabilitar: la ventanilla está en uso por un empleado")

            q_update = update(Ventanilla).where(Ventanilla.ID_Ventanilla == id_ventanilla).values(Activa=nueva_activa)
            await db.execute(q_update)
            await db.commit()

            # Notificar vía WebSocket
            await manager.broadcast_json({"type": "ventanilla_status_changed"})
            await manager.broadcast_json({"type": "sectores_updated"})

            estado = "habilitada" if nueva_activa else "deshabilitada"
            return {"message": f"Ventanilla {estado} correctamente"}

        # Cambiar nombre
        if req.nombre is not None:
            nuevo_nombre = req.nombre
            if not nuevo_nombre:
                raise HTTPException(status_code=400, detail="El nombre no puede estar vacío")

            q_rename = update(Ventanilla).where(Ventanilla.ID_Ventanilla == id_ventanilla).values(Ventanilla=nuevo_nombre)
            await db.execute(q_rename)
            await db.commit()

            await manager.broadcast_json({"type": "ventanilla_status_changed"})
            await manager.broadcast_json({"type": "sectores_updated"})

            return {"message": f"Ventanilla renombrada a '{nuevo_nombre}'"}

        raise HTTPException(status_code=400, detail="Se requiere 'activa' o 'nombre' en el cuerpo de la solicitud")

    except HTTPException:
        await db.rollback()
        raise
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Error de integridad en la base de datos")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.put("/employees/{id_empleado}/ventanilla")
async def update_employee_ventanilla(
    id_empleado: int, 
    req: EmpleadoVentanillaUpdateReq, 
    db: AsyncSession = Depends(get_db)):
    id_ventanilla = req.id_ventanilla
    
    try:
        # Cerrar sesión activa previa
        q_term = (
            update(EmpleadoVentanilla)
            .where(
                and_(
                    EmpleadoVentanilla.ID_Empleado == id_empleado,
                    EmpleadoVentanilla.ID_Estado == 1,
                    EmpleadoVentanilla.Fecha_Termino.is_(None)
                )
            )
            .values(Fecha_Termino=func.now(), ID_Estado=2)
        )
        await db.execute(q_term)

        if id_ventanilla:
            # Check if ventanilla is occupied by another
            q_occ = (
                select(EmpleadoVentanilla.ID_Empleado)
                .where(
                    and_(
                        EmpleadoVentanilla.ID_Ventanilla == id_ventanilla,
                        EmpleadoVentanilla.ID_Estado == 1,
                        EmpleadoVentanilla.ID_Empleado != id_empleado,
                        EmpleadoVentanilla.Fecha_Termino.is_(None)
                    )
                )
            )
            res_occ = await db.execute(q_occ)
            if res_occ.fetchone():
                raise HTTPException(status_code=400, detail="Esta ventanilla ya está ocupada, seleccione otra.")
            
            q_ins = insert(EmpleadoVentanilla).values(
                ID_Empleado=id_empleado,
                ID_Ventanilla=id_ventanilla,
                Fecha_Inicio=func.now(),
                Fecha_Termino=None,
                ID_Estado=1
            )
            await db.execute(q_ins)
        
        await db.commit()
        
        # Notificar a los administradores vía WebSocket para refrescar lista
        await manager.broadcast_json({"type": "ventanilla_status_changed"})
        
        return {"message": "Ventanilla actualizada correctamente"}
        
    except HTTPException:
        await db.rollback()
        raise
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Error de integridad en la base de datos")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor")
        
@router.post("/turno/llamar")
async def llamar_turno(turno: TurnoRequest, db: AsyncSession = Depends(get_db)):
    ventanilla_nombre = turno.ventanilla_nombre
    if turno.id_ventanilla:
        q = select(Ventanilla.Ventanilla).where(Ventanilla.ID_Ventanilla == turno.id_ventanilla)
        res = await db.execute(q)
        row = res.mappings().fetchone()
        if row:
            ventanilla_nombre = row["Ventanilla"]

    texto = f"Turno {turno.folio}, pasar a la ventanilla {ventanilla_nombre}"
    
    # Run heavy Audio I/O without blocking main thread
    audio_file = await asyncio.to_thread(speak_to_file, texto)

    return {
        "mensaje": "Turno llamado",
        "audio_url": f"/api/audio/{audio_file}"
    }

@router.get("/audio/{filename}")
async def get_audio(filename: str):
    # Sanitize input to prevent Path Traversal
    safe_filename = os.path.basename(filename)
    file_path = f"/app/audio/{safe_filename}"
    if not os.path.exists(file_path):
        # Allow Windows testing environment fallback
        import platform
        if platform.system() == "Windows":
             file_path = f"backend/app/audio/{safe_filename}"
        if not os.path.exists(file_path):
             raise HTTPException(status_code=404, detail="Archivo de audio no encontrado")
             
    return FileResponse(file_path, media_type="audio/mpeg")
