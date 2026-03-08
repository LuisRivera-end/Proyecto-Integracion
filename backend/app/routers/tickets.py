import asyncio
import base64
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional
from datetime import datetime
import pytz
import app.utils.helpers as helpers
from app.models.database import get_db
from app.schemas.tickets import TicketCreate
from app.utils.helpers import generar_folio_unico, obtener_fecha_actual, obtener_fecha_publico
from app.models.pdf_generator import generar_ticket_PDF

# Temporary mock until Phase 4 (Manager WS Native)
async def emit_tickets_update():
    from app.websocket.manager import manager
    await manager.broadcast_json({"type": "tickets_updated"})

router = APIRouter(prefix="/api", tags=["Tickets"])

@router.get("/sectores")
async def obtener_sectores(db: AsyncSession = Depends(get_db)):
    try:
        query = text("""
            SELECT s.ID_Sector, s.Sector,
                   COUNT(v.ID_Ventanilla) AS Ventanillas
            FROM Sectores s
            LEFT JOIN Ventanillas v ON s.ID_Sector = v.ID_Sector
            GROUP BY s.ID_Sector, s.Sector
            ORDER BY s.Sector
        """)
        result = await db.execute(query)
        return result.mappings().fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno al obtener sectores")

@router.post("/ticket", status_code=201)
async def generar_ticket(req: dict, db: AsyncSession = Depends(get_db)):
    sector_nombre = req.get("sector")
    tipo_caja = req.get("tipo_caja", "normal")

    if not sector_nombre:
        raise HTTPException(status_code=400, detail="sector es requerido")

    if tipo_caja not in ('normal', 'rapida'):
        tipo_caja = 'normal'

    try:
        # Check if sector exists
        q_sec = text("SELECT ID_Sector FROM Sectores WHERE Sector = :sector")
        res_sec = await db.execute(q_sec, {"sector": sector_nombre})
        row_sec = res_sec.fetchone()
        
        if not row_sec:
            raise HTTPException(status_code=404, detail="No se encontró el sector especificado")
            
        ID_Sector = row_sec[0]
        
        # Estas funciones helper deberan refactorizarse a async en su momento o ser wrapped 
        # (ya que llaman db y filesystem) - por ahora las ejecutare síncronamente via engine
        # Idealmente `generar_folio_unico` usa db.execute() en la misma session para ACID.
        Folio = await helpers.generar_folio_unico(sector_nombre, db)
        Fecha_Ticket = helpers.obtener_fecha_actual()
        Fecha_Ticket_publico = helpers.obtener_fecha_publico()

        q_ins = text("""
            INSERT INTO Turno (ID_Sector, ID_Ventanilla, Fecha_Ticket, Folio, ID_Estados, Fecha_Ultimo_Estado, Tipo_Caja)
            VALUES (:id_sec, NULL, :f_tkt, :folio, 1, :f_tkt, :tipo_caja)
        """)
        await db.execute(q_ins, {
            "id_sec": ID_Sector, 
            "f_tkt": Fecha_Ticket, 
            "folio": Folio, 
            "tipo_caja": tipo_caja
        })

        await db.commit()

        # Emitir evento WS nativo (mocked temporal)
        await emit_tickets_update()

        return {
            "mensaje": "Ticket generado exitosamente",
            "folio": Folio,
            "fecha": Fecha_Ticket_publico,
            "sector": sector_nombre,
            "tipo_caja": tipo_caja
        }
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ticket/print")
async def request_ticket_print(req: Request):
    data = await req.json()
    try:
        if not data or 'numero_ticket' not in data:
            raise HTTPException(status_code=400, detail="Datos incompletos: numero_ticket es requerido")

        required_fields = ['numero_ticket', 'sector', 'fecha']
        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"Campo requerido faltante: {field}")
            
        # Generación intensiva CPU (en hilo secundario)
        pdf_bytes = await asyncio.to_thread(
            generar_ticket_PDF,
            data['numero_ticket'], 
            data['sector'],
            data['fecha']
        )
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
        # Obtener handler de impresión del Scope FastAPI app
        send_print_job = req.app.state.SEND_PRINT_JOB if hasattr(req.app.state, 'SEND_PRINT_JOB') else None
        
        if not send_print_job:
            raise HTTPException(status_code=500, detail="Servicio de impresión no disponible")
            
        # Para llamar funciones WS asincronas del print_service:   
        if asyncio.iscoroutinefunction(send_print_job):     
            success, message = await send_print_job(
                pdf_content=pdf_base64,
                ticket_number=data['numero_ticket'],
                sector=data['sector']
            )
        else: # Helper bloqueante de la migracion actual
            success, message = await asyncio.to_thread(
                 send_print_job, pdf_base64, data['numero_ticket'], data['sector']
            )
        
        if success:
            return {
                "message": message,
                "ticket_number": data['numero_ticket']
            }
        else:
            raise HTTPException(status_code=500, detail=message)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tickets")
async def get_tickets(
    sector: Optional[str] = Query(None),
    id_empleado: Optional[int] = Query(None),
    tipo_caja: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    try:
        if id_empleado:
            q_emp = text("""
                SELECT DISTINCT s.Sector 
                FROM Empleado e
                JOIN Rol_Ventanilla rv ON e.ID_ROL = rv.ID_Rol
                JOIN Ventanillas v ON rv.ID_Ventanilla = v.ID_Ventanilla
                JOIN Sectores s ON v.ID_Sector = s.ID_Sector
                WHERE e.ID_Empleado = :id_empleado
            """)
            res_emp = await db.execute(q_emp, {"id_empleado": id_empleado})
            sector_empleado = res_emp.fetchone()
            if sector_empleado:
                sector = sector_empleado[0]

        base_query = """
            SELECT 
                t.Folio AS folio,
                t.ID_Turno AS id_turno,
                s.Sector AS sector,
                et.Nombre AS estado,
                t.Fecha_Ticket AS fecha_ticket,
                t.Tipo_Caja AS tipo_caja,
                'normal' AS tipo
            FROM Turno t
            JOIN Sectores s ON t.ID_Sector = s.ID_Sector
            JOIN Estados_Turno et ON t.ID_Estados = et.ID_Estado
            WHERE t.ID_Estados = 1
        """
        params = {}

        if sector:
            base_query += " AND s.Sector = :sector"
            params["sector"] = sector

        if tipo_caja and tipo_caja in ('normal', 'rapida'):
            base_query += " AND t.Tipo_Caja = :tipo_caja"
            params["tipo_caja"] = tipo_caja

        res = await db.execute(text(base_query), params)
        tickets = res.mappings().fetchall()
        
        # Sort manually using mappings to dict conversion
        tickets_list = [dict(t) for t in tickets]
        tickets_list.sort(key=lambda x: str(x['fecha_ticket']))
        
        return tickets_list

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/tickets/{folio}/attend")
async def attend_ticket(folio: str, req: dict, db: AsyncSession = Depends(get_db)):
    id_ventanilla = req.get("id_ventanilla")
    if not id_ventanilla:
        raise HTTPException(status_code=400, detail="ID de ventanilla requerido")

    import app.utils.helpers as sync_helpers
    nueva_fecha = sync_helpers.obtener_fecha_actual()
    
    try:
        q_upd = text("""
            UPDATE Turno
            SET ID_Estados = 3, 
                Fecha_Ultimo_Estado = :nueva_fecha, 
                ID_Ventanilla = :id_ventanilla
            WHERE Folio = :folio AND ID_Estados = 1
        """)
        res = await db.execute(q_upd, {
            "nueva_fecha": nueva_fecha,
            "id_ventanilla": id_ventanilla,
            "folio": folio
        })

        if res.rowcount == 0:
            raise HTTPException(status_code=404, detail="Ticket no encontrado o ya atendido")

        await db.commit()
        await emit_tickets_update()
        
        return {"message": f"Ticket {folio} en estado 'Atendiendo' por ventanilla {id_ventanilla}"}
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/tickets/{folio}/complete")
async def complete_ticket(folio: str, db: AsyncSession = Depends(get_db)):
    import app.utils.helpers as sync_helpers
    nueva_fecha = sync_helpers.obtener_fecha_actual()
    try:
        q_upd = text("""
            UPDATE Turno
            SET ID_Estados = 4, Fecha_Ultimo_Estado = :nueva_fecha
            WHERE Folio = :folio
        """)
        await db.execute(q_upd, {"nueva_fecha": nueva_fecha, "folio": folio})
        await db.commit()
        await emit_tickets_update()
        
        return {"message": f"Ticket {folio} marcado como 'Completado'"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/tickets/{folio}/cancel")
async def cancel_ticket(folio: str, db: AsyncSession = Depends(get_db)):
    import app.utils.helpers as sync_helpers
    nueva_fecha = sync_helpers.obtener_fecha_actual()
    try:
        q_upd = text("""
            UPDATE Turno
            SET ID_Estados = 2, Fecha_Ultimo_Estado = :nueva_fecha
            WHERE Folio = :folio AND ID_Estados = 3
        """)
        res = await db.execute(q_upd, {"nueva_fecha": nueva_fecha, "folio": folio})
        
        if res.rowcount == 0:
            raise HTTPException(status_code=404, detail="Ticket no encontrado o no está siendo atendido")
            
        await db.commit()
        await emit_tickets_update()
        
        return {"message": f"Ticket {folio} cancelado exitosamente"}
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tickets_count")
async def get_tickets_count(db: AsyncSession = Depends(get_db)):
    try:
        q = text("""
            SELECT 
                s.Sector AS nombre_sector,
                COUNT(t.ID_Turno) AS cantidad
            FROM Turno t
            JOIN Sectores s ON t.ID_Sector = s.ID_Sector
            WHERE t.ID_Estados = 1
            GROUP BY s.Sector
        """)
        res = await db.execute(q)
        rows = res.mappings().fetchall()
        
        return {r["nombre_sector"]: r["cantidad"] for r in rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/total_tickets")
async def total_tickets(db: AsyncSession = Depends(get_db)):
    try:
        tz = pytz.timezone('America/Mexico_City')
        hoy_local = datetime.now(tz).strftime('%Y-%m-%d')

        q = text("SELECT COUNT(ID_Turno) AS cantidad FROM Turno WHERE DATE(Fecha_Ticket) = :hoy")
        res = await db.execute(q, {"hoy": hoy_local})
        
        row = res.fetchone()
        return {"cantidad": row[0] if row else 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tickets/activo/{id_ventanilla}")
async def get_ticket_activo(id_ventanilla: int, db: AsyncSession = Depends(get_db)):
    try:
        q = text("""
            SELECT t.Folio AS folio
            FROM Turno t
            WHERE t.ID_Ventanilla = :id_ventanilla AND t.ID_Estados = 3
            ORDER BY t.Fecha_Ultimo_Estado DESC
            LIMIT 1
        """)
        res = await db.execute(q, {"id_ventanilla": id_ventanilla})
        ticket = res.fetchone()
        
        if not ticket:
            return {"activo": False}
            
        return {"activo": True, "folio": ticket[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tickets/llamar-siguiente")
async def llamar_siguiente_ticket(req: dict, db: AsyncSession = Depends(get_db)):
    id_ventanilla = req.get("id_ventanilla")
    id_empleado = req.get("id_empleado")
    tipo_caja = req.get("tipo_caja") 

    if not id_ventanilla or not id_empleado:
        raise HTTPException(status_code=400, detail="Ventanilla y empleado requeridos")

    try:
        q_emp = text("""
            SELECT DISTINCT s.ID_Sector, s.Sector
            FROM Empleado e
            JOIN Rol_Ventanilla rv ON e.ID_ROL = rv.ID_Rol
            JOIN Ventanillas v ON rv.ID_Ventanilla = v.ID_Ventanilla
            JOIN Sectores s ON v.ID_Sector = s.ID_Sector
            WHERE e.ID_Empleado = :id_empleado
        """)
        res_emp = await db.execute(q_emp, {"id_empleado": id_empleado})
        sector_emp = res_emp.mappings().fetchone()
        
        if not sector_emp:
            raise HTTPException(status_code=400, detail="Empleado no tiene ventanillas/sectores asignados")
            
        id_sector = sector_emp["ID_Sector"]

        q_next = """
            SELECT t.Folio, t.ID_Turno as id, t.Fecha_Ticket
            FROM Turno t
            WHERE t.ID_Estados = 1 AND t.ID_Sector = :id_sector
        """
        params = {"id_sector": id_sector}
        if tipo_caja and tipo_caja in ('normal', 'rapida'):
            q_next += " AND t.Tipo_Caja = :tipo_caja"
            params["tipo_caja"] = tipo_caja

        q_next += " ORDER BY t.Fecha_Ticket ASC LIMIT 1"

        res_next = await db.execute(text(q_next), params)
        siguiente = res_next.mappings().fetchone()
        
        if not siguiente:
            raise HTTPException(status_code=404, detail="No hay tickets pendientes en tu sector")
            
        folio = siguiente["Folio"]
        import app.utils.helpers as sync_helpers
        nueva_fecha = sync_helpers.obtener_fecha_actual()

        q_upd = text("""
            UPDATE Turno
            SET ID_Estados = 3, 
                Fecha_Ultimo_Estado = :nueva_fecha, 
                ID_Ventanilla = :id_ventanilla
            WHERE Folio = :folio AND ID_Estados = 1
        """)
        res_upd = await db.execute(q_upd, {
            "nueva_fecha": nueva_fecha,
            "id_ventanilla": id_ventanilla,
            "folio": folio
        })
        
        if res_upd.rowcount == 0:
            raise HTTPException(status_code=409, detail="El ticket ya fue tomado por otro operador")
            
        await db.commit()
        await emit_tickets_update()

        return {
            "message": f"Ticket {folio} llamado para atención",
            "folio": folio,
        }
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/turno/{id_turno}/estado")
async def actualizar_estado_turno(id_turno: int, req: dict, db: AsyncSession = Depends(get_db)):
    nuevo_estado = req.get("estado")
    if not nuevo_estado:
        raise HTTPException(status_code=400, detail="Estado requerido")

    import app.utils.helpers as sync_helpers
    nueva_fecha = sync_helpers.obtener_fecha_actual()
    try:
        q_upd = text("""
            UPDATE Turno
            SET ID_Estados = :nuevo_estado, Fecha_Ultimo_Estado = :nueva_fecha
            WHERE ID_Turno = :id_turno
        """)
        res = await db.execute(q_upd, {
            "nuevo_estado": nuevo_estado,
            "nueva_fecha": nueva_fecha,
            "id_turno": id_turno
        })
        
        if res.rowcount == 0:
            raise HTTPException(status_code=404, detail="Turno no encontrado")
            
        await db.commit()
        await emit_tickets_update()
        return {"mensaje": "Estado actualizado correctamente"}
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tickets/historial")
async def get_historial_tickets(db: AsyncSession = Depends(get_db)):
    try:
        q = text("""
            SELECT 
                t.Folio AS folio,
                t.ID_Turno AS id_turno,
                s.Sector AS sector,
                et.Nombre AS estado,
                t.Fecha_Ticket AS fecha_ticket,
                t.Fecha_Ultimo_Estado AS fecha_ultimo_estado,
                'normal' AS tipo
            FROM Turno t
            JOIN Sectores s ON t.ID_Sector = s.ID_Sector
            JOIN Estados_Turno et ON t.ID_Estados = et.ID_Estado
            ORDER BY t.Fecha_Ticket DESC
            LIMIT 100
        """)
        res = await db.execute(q)
        return res.mappings().fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tickets/publico")
async def get_tickets_publico(db: AsyncSession = Depends(get_db)):
    try:
        q = text("""
            SELECT 
                t.Folio AS folio,
                t.ID_Turno AS id_turno,
                t.ID_Ventanilla AS id_ventanilla,
                v.Ventanilla AS ventanilla,
                s.Sector AS sector,
                et.Nombre AS estado,
                et.ID_Estado AS estado_id,
                t.Fecha_Ticket AS fecha_ticket,
                'normal' AS tipo
            FROM Turno t
            JOIN Sectores s ON t.ID_Sector = s.ID_Sector
            JOIN Estados_Turno et ON t.ID_Estados = et.ID_Estado
            LEFT JOIN Ventanillas v ON t.ID_Ventanilla = v.ID_Ventanilla
            WHERE t.ID_Estados IN (1, 3)
        """)
        res = await db.execute(q)
        tickets = [dict(r) for r in res.mappings().fetchall()]
        
        # Sort
        tickets.sort(key=lambda x: (x['estado_id'] != 3, str(x['fecha_ticket'])))
        return tickets
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
