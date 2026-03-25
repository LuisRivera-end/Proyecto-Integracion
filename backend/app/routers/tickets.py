import asyncio
import base64
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, update, insert, func, and_
from typing import Optional
from datetime import datetime
import pytz
import app.utils.helpers as helpers
from app.models.database import get_db
from app.models.models import Sector, Ventanilla, Turno, EstadoTurno, Empleado, RolVentanilla
from app.schemas.tickets import TicketCreate, TicketGenerateReq, TicketAttendReq, TicketNextReq, TurnoStatusReq
from app.schemas.empleados import SectorCreateReq, SectorUpdateReq
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
        query = (
            select(Sector.ID_Sector, Sector.Sector, func.count(Ventanilla.ID_Ventanilla).label("Ventanillas"))
            .outerjoin(Ventanilla, Sector.ID_Sector == Ventanilla.ID_Sector)
            .group_by(Sector.ID_Sector, Sector.Sector)
            .order_by(Sector.Sector)
        )
        result = await db.execute(query)
        return result.mappings().fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno al obtener sectores")

@router.post("/sectores", status_code=201)
async def crear_sector(req: SectorCreateReq, db: AsyncSession = Depends(get_db)):
    try:
        q_ins = insert(Sector).values(Sector=req.sector)
        res = await db.execute(q_ins)
        id_sector = res.inserted_primary_key[0]
        
        if req.ventanillas > 0:
            ventanillas_data = [{"ID_Sector": id_sector, "Ventanilla": f"Ventanilla {i+1}"} for i in range(req.ventanillas)]
            await db.execute(insert(Ventanilla).values(ventanillas_data))
            
        await db.commit()
        return {"mensaje": "Sector creado exitosamente", "id_sector": id_sector}
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Error de integridad en la base de datos")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.put("/sectores/{id_sector}")
async def actualizar_sector(id_sector: int, req: SectorUpdateReq, db: AsyncSession = Depends(get_db)):
    try:
        q_upd = update(Sector).where(Sector.ID_Sector == id_sector).values(Sector=req.sector)
        res = await db.execute(q_upd)
        if res.rowcount == 0:
            raise HTTPException(status_code=404, detail="Sector no encontrado")
            
        await db.commit()
        return {"mensaje": "Sector actualizado exitosamente"}
    except HTTPException:
        await db.rollback()
        raise
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Error de integridad en la base de datos")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/ticket", status_code=201)
async def generar_ticket(req: TicketGenerateReq, db: AsyncSession = Depends(get_db)):
    sector_nombre = req.sector
    tipo_caja = req.tipo_caja or "normal"

    if tipo_caja not in ('normal', 'rapida'):
        tipo_caja = 'normal'

    try:
        # Check if sector exists
        q_sec = select(Sector.ID_Sector).where(Sector.Sector == sector_nombre)
        res_sec = await db.execute(q_sec)
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

        q_ins = insert(Turno).values(
            ID_Sector=ID_Sector, 
            ID_Ventanilla=None, 
            Fecha_Ticket=Fecha_Ticket, 
            Folio=Folio, 
            ID_Estados=1, 
            Fecha_Ultimo_Estado=Fecha_Ticket, 
            Tipo_Caja=tipo_caja
        )
        await db.execute(q_ins)

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
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Error de integridad en la base de datos")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor")

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
            data['fecha'],
            data.get('tipo_caja', 'normal')
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
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Error de integridad en la base de datos")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/tickets")
async def get_tickets(
    sector: Optional[str] = Query(None),
    id_empleado: Optional[int] = Query(None),
    tipo_caja: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    try:
        # If id_empleado is provided, resolve their sector
        if id_empleado:
            q_emp = (
                select(Sector.Sector)
                .select_from(Empleado)
                .join(RolVentanilla, Empleado.ID_ROL == RolVentanilla.ID_Rol)
                .join(Ventanilla, RolVentanilla.ID_Ventanilla == Ventanilla.ID_Ventanilla)
                .join(Sector, Ventanilla.ID_Sector == Sector.ID_Sector)
                .where(Empleado.ID_Empleado == id_empleado)
                .distinct()
            )
            res_emp = await db.execute(q_emp)
            sector_empleado = res_emp.fetchone()
            if sector_empleado:
                sector = sector_empleado[0]

        q = (
            select(
                Turno.Folio.label("folio"),
                Turno.ID_Turno.label("id_turno"),
                Sector.Sector.label("sector"),
                EstadoTurno.ID_Estado.label("estado_id"),
                EstadoTurno.Nombre.label("estado"),
                Turno.Fecha_Ticket.label("fecha_ticket"),
            )
            .join(Sector, Turno.ID_Sector == Sector.ID_Sector)
            .join(EstadoTurno, Turno.ID_Estados == EstadoTurno.ID_Estado)
            .where(Turno.ID_Estados == 1)
            .order_by(Turno.Fecha_Ticket.asc())
        )

        if sector:
            q = q.where(Sector.Sector == sector)
        if tipo_caja and tipo_caja in ('normal', 'rapida'):
            q = q.where(Turno.Tipo_Caja == tipo_caja)

        res = await db.execute(q)
        return [dict(r) for r in res.mappings().fetchall()]
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Error de integridad en la base de datos")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/total_tickets")
async def total_tickets(db: AsyncSession = Depends(get_db)):
    try:
        tz = pytz.timezone('America/Mexico_City')
        hoy_local = datetime.now(tz).strftime('%Y-%m-%d')

        q = (
            select(func.count(Turno.ID_Turno).label("cantidad"))
            .where(func.date(Turno.Fecha_Ticket) == hoy_local)
        )
        res = await db.execute(q)
        
        row = res.fetchone()
        return {"cantidad": row[0] if row else 0}
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Error de integridad en la base de datos")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/tickets/activo/{id_ventanilla}")
async def get_ticket_activo(id_ventanilla: int, db: AsyncSession = Depends(get_db)):
    try:
        q = (
            select(Turno.Folio.label("folio"))
            .where(and_(Turno.ID_Ventanilla == id_ventanilla, Turno.ID_Estados == 3))
            .order_by(Turno.Fecha_Ultimo_Estado.desc())
            .limit(1)
        )
        res = await db.execute(q)
        ticket = res.fetchone()
        
        if not ticket:
            return {"activo": False}
            
        return {"activo": True, "folio": ticket[0]}
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Error de integridad en la base de datos")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/tickets/llamar-siguiente")
async def llamar_siguiente_ticket(req: TicketNextReq, db: AsyncSession = Depends(get_db)):
    id_ventanilla = req.id_ventanilla
    id_empleado = req.id_empleado
    tipo_caja = req.tipo_caja 

    try:
        q_emp = (
            select(Sector.ID_Sector, Sector.Sector)
            .select_from(Empleado)
            .join(RolVentanilla, Empleado.ID_ROL == RolVentanilla.ID_Rol)
            .join(Ventanilla, RolVentanilla.ID_Ventanilla == Ventanilla.ID_Ventanilla)
            .join(Sector, Ventanilla.ID_Sector == Sector.ID_Sector)
            .where(Empleado.ID_Empleado == id_empleado)
            .distinct()
        )
        res_emp = await db.execute(q_emp)
        sector_emp = res_emp.mappings().fetchone()
        
        if not sector_emp:
            raise HTTPException(status_code=400, detail="Empleado no tiene ventanillas/sectores asignados")
            
        id_sector = sector_emp["ID_Sector"]

        q_next = (
            select(Turno.Folio, Turno.ID_Turno.label("id"), Turno.Fecha_Ticket)
            .where(and_(Turno.ID_Estados == 1, Turno.ID_Sector == id_sector))
        )
        
        if tipo_caja and tipo_caja in ('normal', 'rapida'):
            q_next = q_next.where(Turno.Tipo_Caja == tipo_caja)

        q_next = q_next.order_by(Turno.Fecha_Ticket.asc()).limit(1)

        res_next = await db.execute(q_next)
        siguiente = res_next.mappings().fetchone()
        
        if not siguiente:
            raise HTTPException(status_code=404, detail="No hay tickets pendientes en tu sector")
            
        folio = siguiente["Folio"]
        import app.utils.helpers as sync_helpers
        nueva_fecha = sync_helpers.obtener_fecha_actual()

        q_upd = (
            update(Turno)
            .where(and_(Turno.Folio == folio, Turno.ID_Estados == 1))
            .values(
                ID_Estados=3,
                Fecha_Ultimo_Estado=nueva_fecha,
                ID_Ventanilla=id_ventanilla
            )
        )
        res_upd = await db.execute(q_upd)
        
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
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Error de integridad en la base de datos")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.put("/turno/{id_turno}/estado")
async def actualizar_estado_turno(id_turno: int, req: TurnoStatusReq, db: AsyncSession = Depends(get_db)):
    nuevo_estado = req.estado

    import app.utils.helpers as sync_helpers
    nueva_fecha = sync_helpers.obtener_fecha_actual()
    try:
        q_upd = (
            update(Turno)
            .where(Turno.ID_Turno == id_turno)
            .values(ID_Estados=nuevo_estado, Fecha_Ultimo_Estado=nueva_fecha)
        )
        res = await db.execute(q_upd)
        
        if res.rowcount == 0:
            raise HTTPException(status_code=404, detail="Turno no encontrado")
            
        await db.commit()
        await emit_tickets_update()
        return {"mensaje": "Estado actualizado correctamente"}
        
    except HTTPException:
        await db.rollback()
        raise
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Error de integridad en la base de datos")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.put("/tickets/{folio}/complete")
async def completar_ticket(folio: str, db: AsyncSession = Depends(get_db)):
    """Marca un ticket como completado (estado 4) usando su folio."""
    import app.utils.helpers as sync_helpers
    nueva_fecha = sync_helpers.obtener_fecha_actual()
    try:
        q_upd = (
            update(Turno)
            .where(and_(Turno.Folio == folio, Turno.ID_Estados == 3))
            .values(ID_Estados=4, Fecha_Ultimo_Estado=nueva_fecha)
        )
        res = await db.execute(q_upd)

        if res.rowcount == 0:
            raise HTTPException(status_code=404, detail="Ticket no encontrado o no está en atención")

        await db.commit()
        await emit_tickets_update()
        return {"mensaje": f"Ticket {folio} completado exitosamente", "folio": folio}

    except HTTPException:
        await db.rollback()
        raise
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Error de integridad en la base de datos")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.put("/tickets/{folio}/cancel")
async def cancelar_ticket(folio: str, db: AsyncSession = Depends(get_db)):
    """Marca un ticket como cancelado (estado 2) usando su folio."""
    import app.utils.helpers as sync_helpers
    nueva_fecha = sync_helpers.obtener_fecha_actual()
    try:
        q_upd = (
            update(Turno)
            .where(and_(Turno.Folio == folio, Turno.ID_Estados.in_([1, 3])))
            .values(ID_Estados=2, Fecha_Ultimo_Estado=nueva_fecha)
        )
        res = await db.execute(q_upd)

        if res.rowcount == 0:
            raise HTTPException(status_code=404, detail="Ticket no encontrado o ya fue procesado")

        await db.commit()
        await emit_tickets_update()
        return {"mensaje": f"Ticket {folio} cancelado", "folio": folio}

    except HTTPException:
        await db.rollback()
        raise
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Error de integridad en la base de datos")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/tickets/historial")
async def get_historial_tickets(db: AsyncSession = Depends(get_db)):
    try:
        from sqlalchemy.exc import IntegrityError
        from sqlalchemy import literal_column
        q = (
            select(
                Turno.Folio.label("folio"),
                Turno.ID_Turno.label("id_turno"),
                Sector.Sector.label("sector"),
                EstadoTurno.Nombre.label("estado"),
                Turno.Fecha_Ticket.label("fecha_ticket"),
                Turno.Fecha_Ultimo_Estado.label("fecha_ultimo_estado"),
                literal_column("'normal'").label("tipo")
            )
            .join(Sector, Turno.ID_Sector == Sector.ID_Sector)
            .join(EstadoTurno, Turno.ID_Estados == EstadoTurno.ID_Estado)
            .order_by(Turno.Fecha_Ticket.desc())
            .limit(100)
        )
        res = await db.execute(q)
        return res.mappings().fetchall()
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Error de integridad en la base de datos")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/tickets/publico")
async def get_tickets_publico(db: AsyncSession = Depends(get_db)):
    try:
        from sqlalchemy.exc import IntegrityError
        from sqlalchemy import literal_column
        q = (
            select(
                Turno.Folio.label("folio"),
                Turno.ID_Turno.label("id_turno"),
                Turno.ID_Ventanilla.label("id_ventanilla"),
                Ventanilla.Ventanilla.label("ventanilla"),
                Sector.Sector.label("sector"),
                EstadoTurno.Nombre.label("estado"),
                EstadoTurno.ID_Estado.label("estado_id"),
                Turno.Fecha_Ticket.label("fecha_ticket"),
                literal_column("'normal'").label("tipo")
            )
            .join(Sector, Turno.ID_Sector == Sector.ID_Sector)
            .join(EstadoTurno, Turno.ID_Estados == EstadoTurno.ID_Estado)
            .outerjoin(Ventanilla, Turno.ID_Ventanilla == Ventanilla.ID_Ventanilla)
            .where(Turno.ID_Estados.in_([1, 3]))
        )
        res = await db.execute(q)
        tickets = [dict(r) for r in res.mappings().fetchall()]
        
        # Sort
        tickets.sort(key=lambda x: (x['estado_id'] != 3, str(x['fecha_ticket'])))
        return tickets
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Error de integridad en la base de datos")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")
