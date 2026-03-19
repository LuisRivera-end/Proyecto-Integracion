from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi.responses import FileResponse
from pydantic import BaseModel
import asyncio
import os

from app.models.database import get_db
from app.utils.helpers import speak_to_file
from app.schemas.tickets import TurnoRequest
from app.websocket.manager import manager

router = APIRouter(prefix="/api", tags=["Ventanillas"])

class EmpleadoVentanillaReq(BaseModel):
    id_empleado: int
    id_ventanilla: int

@router.get("/sectores/{id_sector}/ventanillas")
async def get_ventanillas_por_sector(id_sector: int, db: AsyncSession = Depends(get_db)):
    """Retorna todas las ventanillas de un sector con información de si están ocupadas"""
    try:
        q = text("""
            SELECT 
                v.ID_Ventanilla, 
                v.Ventanilla, 
                v.Activa,
                ev.ID_Empleado as id_empleado,
                CONCAT(e.nombre1, ' ', e.Apellido1) as nombre_empleado
            FROM Ventanillas v
            LEFT JOIN Empleado_Ventanilla ev ON v.ID_Ventanilla = ev.ID_Ventanilla 
                AND ev.ID_Estado = 1 AND ev.Fecha_Termino IS NULL
            LEFT JOIN Empleado e ON ev.ID_Empleado = e.ID_Empleado
            WHERE v.ID_Sector = :id_sector
        """)
        res = await db.execute(q, {"id_sector": id_sector})
        return res.mappings().fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ventanillas/libres/{id_empleado}")
async def ventanillas_libres(id_empleado: int, db: AsyncSession = Depends(get_db)):
    try:
        query_emp = text("SELECT ID_ROL FROM Empleado WHERE ID_Empleado = :id_empleado")
        res_emp = await db.execute(query_emp, {"id_empleado": id_empleado})
        empleado = res_emp.mappings().fetchone()
        
        if not empleado:
            raise HTTPException(status_code=404, detail="Empleado no encontrado")
            
        id_rol = empleado["ID_ROL"]

        query_ventanillas = text("""
            SELECT 
                V.ID_Ventanilla,
                V.Ventanilla,
                S.Sector
            FROM Ventanillas V
            JOIN Rol_Ventanilla RV ON V.ID_Ventanilla = RV.ID_Ventanilla
            JOIN Sectores S ON V.ID_Sector = S.ID_Sector
            LEFT JOIN Empleado_Ventanilla EV 
                ON V.ID_Ventanilla = EV.ID_Ventanilla 
                AND EV.ID_Estado = 1
            WHERE EV.ID_Ventanilla IS NULL
                AND RV.ID_Rol = :id_rol
                AND V.Activa = 1
        """)

        res_ventanillas = await db.execute(query_ventanillas, {"id_rol": id_rol})
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
        q_occ = text("""
            SELECT 1 FROM Empleado_Ventanilla
            WHERE ID_Ventanilla = :id_ventanilla AND ID_Estado = 1 AND Fecha_Termino IS NULL
        """)
        res_occ = await db.execute(q_occ, {"id_ventanilla": req.id_ventanilla})
        if res_occ.fetchone():
            raise HTTPException(status_code=400, detail="Ventanilla ocupada")

        # Terminate previous sessions of this employee
        q_term = text("""
            UPDATE Empleado_Ventanilla 
            SET Fecha_Termino = NOW(), ID_Estado = 2 
            WHERE ID_Empleado = :id_empleado AND ID_Estado = 1 AND Fecha_Termino IS NULL
        """)
        await db.execute(q_term, {"id_empleado": req.id_empleado})

        # Insert new session
        q_ins = text("""
            INSERT INTO Empleado_Ventanilla 
            (ID_Empleado, ID_Ventanilla, Fecha_Inicio, Fecha_Termino, ID_Estado)
            VALUES (:id_empleado, :id_ventanilla, NOW(), NULL, 1)
        """)
        await db.execute(q_ins, {"id_empleado": req.id_empleado, "id_ventanilla": req.id_ventanilla})
        
        # Get Ventanilla Info
        q_info = text("""
            SELECT v.ID_Ventanilla, v.Ventanilla, s.Sector 
            FROM Ventanillas v 
            JOIN Sectores s ON v.ID_Sector = s.ID_Sector 
            WHERE v.ID_Ventanilla = :id_ventanilla
        """)
        res_info = await db.execute(q_info, {"id_ventanilla": req.id_ventanilla})
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
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ventanillas/disponibles/{id_rol}")
async def get_ventanillas_disponibles(
    id_rol: int, 
    excluir_empleado: int = Query(None), 
    db: AsyncSession = Depends(get_db)):
    try:
        if excluir_empleado:
            query = text("""
                SELECT v.ID_Ventanilla, v.Ventanilla
                FROM Ventanillas v
                JOIN Rol_Ventanilla rv ON v.ID_Ventanilla = rv.ID_Ventanilla
                WHERE rv.ID_Rol = :id_rol
                  AND v.Activa = 1
                  AND (
                    v.ID_Ventanilla NOT IN (
                        SELECT ev.ID_Ventanilla
                        FROM Empleado_Ventanilla ev
                        WHERE ev.Fecha_Termino IS NULL
                          AND ev.ID_Estado = 1
                          AND ev.ID_Empleado != :excluir_empleado
                    )
                  )
                ORDER BY v.ID_Ventanilla
            """)
            res = await db.execute(query, {"id_rol": id_rol, "excluir_empleado": excluir_empleado})
        else:
            query = text("""
                SELECT v.ID_Ventanilla, v.Ventanilla
                FROM Ventanillas v
                JOIN Rol_Ventanilla rv ON v.ID_Ventanilla = rv.ID_Ventanilla
                WHERE rv.ID_Rol = :id_rol
                  AND v.Activa = 1
                  AND v.ID_Ventanilla NOT IN (
                      SELECT ev.ID_Ventanilla
                      FROM Empleado_Ventanilla ev
                      WHERE ev.Fecha_Termino IS NULL
                        AND ev.ID_Estado = 1
                  )
                ORDER BY v.ID_Ventanilla
            """)
            res = await db.execute(query, {"id_rol": id_rol})
        
        return res.mappings().fetchall()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/ventanillas/{id_ventanilla}")
async def update_ventanilla(id_ventanilla: int, req: dict, db: AsyncSession = Depends(get_db)):
    """Actualiza el estado (Activa) o el nombre de una ventanilla"""
    try:
        # Verificar que la ventanilla existe
        q_check = text("SELECT ID_Ventanilla, Ventanilla, Activa FROM Ventanillas WHERE ID_Ventanilla = :id")
        res_check = await db.execute(q_check, {"id": id_ventanilla})
        ventanilla = res_check.mappings().fetchone()
        if not ventanilla:
            raise HTTPException(status_code=404, detail="Ventanilla no encontrada")

        # Cambiar estado activa/inactiva
        if "activa" in req:
            nueva_activa = int(req["activa"])
            # Si se va a desactivar, verificar que no esté en uso
            if nueva_activa == 0:
                q_uso = text("""
                    SELECT 1 FROM Empleado_Ventanilla
                    WHERE ID_Ventanilla = :id AND ID_Estado = 1 AND Fecha_Termino IS NULL
                """)
                res_uso = await db.execute(q_uso, {"id": id_ventanilla})
                if res_uso.fetchone():
                    raise HTTPException(status_code=400, detail="No se puede deshabilitar: la ventanilla está en uso por un empleado")

            q_update = text("UPDATE Ventanillas SET Activa = :activa WHERE ID_Ventanilla = :id")
            await db.execute(q_update, {"activa": nueva_activa, "id": id_ventanilla})
            await db.commit()

            # Notificar vía WebSocket
            await manager.broadcast_json({"type": "ventanilla_status_changed"})
            await manager.broadcast_json({"type": "sectores_updated"})

            estado = "habilitada" if nueva_activa == 1 else "deshabilitada"
            return {"message": f"Ventanilla {estado} correctamente"}

        # Cambiar nombre
        if "nombre" in req:
            nuevo_nombre = req["nombre"].strip()
            if not nuevo_nombre:
                raise HTTPException(status_code=400, detail="El nombre no puede estar vacío")

            q_rename = text("UPDATE Ventanillas SET Ventanilla = :nombre WHERE ID_Ventanilla = :id")
            await db.execute(q_rename, {"nombre": nuevo_nombre, "id": id_ventanilla})
            await db.commit()

            await manager.broadcast_json({"type": "ventanilla_status_changed"})
            await manager.broadcast_json({"type": "sectores_updated"})

            return {"message": f"Ventanilla renombrada a '{nuevo_nombre}'"}

        raise HTTPException(status_code=400, detail="Se requiere 'activa' o 'nombre' en el cuerpo de la solicitud")

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/employees/{id_empleado}/ventanilla")
async def update_employee_ventanilla(
    id_empleado: int, 
    req: dict, 
    db: AsyncSession = Depends(get_db)):
    id_ventanilla = req.get("id_ventanilla")
    
    try:
        # Cerrar sesión activa previa
        q_term = text("""
            UPDATE Empleado_Ventanilla 
            SET Fecha_Termino = NOW(), ID_Estado = 2 
            WHERE ID_Empleado = :id_empleado AND ID_Estado = 1 AND Fecha_Termino IS NULL
        """)
        await db.execute(q_term, {"id_empleado": id_empleado})

        if id_ventanilla:
            # Check if ventanilla is occupied by another
            q_occ = text("""
                SELECT ID_Empleado 
                FROM Empleado_Ventanilla 
                WHERE ID_Ventanilla = :id_ventanilla AND ID_Estado = 1 AND ID_Empleado != :id_empleado
            """)
            res_occ = await db.execute(q_occ, {"id_ventanilla": id_ventanilla, "id_empleado": id_empleado})
            if res_occ.fetchone():
                raise HTTPException(status_code=400, detail="Esta ventanilla ya está ocupada, seleccione otra.")
            
            q_ins = text("""
                INSERT INTO Empleado_Ventanilla 
                (ID_Empleado, ID_Ventanilla, Fecha_Inicio, Fecha_Termino, ID_Estado)
                VALUES (:id_empleado, :id_ventanilla, NOW(), NULL, 1)
            """)
            await db.execute(q_ins, {"id_empleado": id_empleado, "id_ventanilla": id_ventanilla})
        
        await db.commit()
        
        # Notificar a los administradores vía WebSocket para refrescar lista
        await manager.broadcast_json({"type": "ventanilla_status_changed"})
        
        return {"message": "Ventanilla actualizada correctamente"}
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
        
@router.post("/turno/llamar")
async def llamar_turno(turno: TurnoRequest, db: AsyncSession = Depends(get_db)):
    ventanilla_nombre = turno.ventanilla_nombre
    if turno.id_ventanilla:
        q = text("SELECT Ventanilla FROM Ventanillas WHERE ID_Ventanilla = :id")
        res = await db.execute(q, {"id": turno.id_ventanilla})
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
    file_path = f"/app/audio/{filename}"
    if not os.path.exists(file_path):
        # Allow Windows testing environment fallback
        import platform
        if platform.system() == "Windows":
             file_path = f"backend/app/audio/{filename}"
        if not os.path.exists(file_path):
             raise HTTPException(status_code=404, detail="Archivo de audio no encontrado")
             
    return FileResponse(file_path, media_type="audio/mpeg")
