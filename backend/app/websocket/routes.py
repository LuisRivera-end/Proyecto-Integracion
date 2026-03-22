from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy import text
from app.models.database import AsyncSessionLocal
from app.models.models import SesionActiva
from .manager import manager
import json
from datetime import datetime, timedelta

router = APIRouter()


async def renew_session_if_privileged(client_id: str):
    """Extend session expiration for admin/subjefe roles on activity."""
    session_token = manager.sid_to_token.get(client_id)
    if not session_token:
        return
    async with AsyncSessionLocal() as db:
        # Get the role of the user tied to this token
        q = select(SesionActiva.ID_Empleado).where(SesionActiva.Token == session_token)
        res = await db.execute(q)
        id_empleado_row = res.fetchone()
        if not id_empleado_row:
            return
        id_empleado = id_empleado_row[0]
        # Get role from Empleado
        from app.models.models import Empleado
        q2 = select(Empleado.ID_ROL).where(Empleado.ID_Empleado == id_empleado)
        res2 = await db.execute(q2)
        role_row = res2.fetchone()
        if not role_row:
            return
        id_rol = role_row[0]
        if id_rol in (1, 6):
            new_expira = datetime.utcnow() + timedelta(seconds=30)
            await db.execute(
                update(SesionActiva)
                .where(SesionActiva.Token == session_token)
                .values(Expira=new_expira)
            )
            await db.commit()


router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Generamos un ID de conexion
    client_id = str(id(websocket))
    await manager.connect(client_id, websocket, "public")
    
    try:
        while True:
            # Emulando los eventos estilo Socket.IO via JSON puro
            # Formato esperado: {"type": "event_name", "data": {...}}
            data_raw = await websocket.receive_text()
            try:
                message = json.loads(data_raw)
                event_type = message.get("type")
                event_data = message.get("data", {})
                
                print(f"📥 WS Evento: {event_type} desde {client_id}")
                
                if event_type == "register_printer":
                    printer_name = event_data.get('printer_name', 'POS-58')
                    location = event_data.get('location', 'Recepcion')
                    manager.register_printer(client_id, printer_name, location)
                    await manager.send_personal_json({
                        "type": "registration_success",
                        "message": f"Registrado como {printer_name}",
                        "client_id": client_id
                    }, client_id)

                elif event_type == "print_completed":
                    if client_id in manager.printers:
                        manager.printers[client_id]['status'] = 'available'
                    
                    print(f"✅ Impresión completada: {event_data.get('ticket_number')}")
                    await manager.broadcast_json({
                        "type": "print_success",
                        "ticket_number": event_data.get('ticket_number'),
                        "client_id": client_id
                    })

                elif event_type == "print_failed":
                    if client_id in manager.printers:
                        manager.printers[client_id]['status'] = 'available'
                    
                    print(f"❌ Impresión fallida: {event_data.get('error')}")
                    await manager.send_personal_json({
                        "type": "print_error",
                        "error": event_data.get('error'),
                        "ticket_number": event_data.get('ticket_number')
                    }, client_id)

                elif event_type == "check_sector_ventanillas":
                    id_sector = event_data.get('id_sector')
                    if not id_sector:
                        await manager.send_personal_json({
                            "type": "sector_ventanillas_status",
                            "puede_modificar": False,
                            "error": "ID de sector requerido"
                        }, client_id)
                        continue
                    
                    # Llamada a DB Asincrona para chechar ventanillas    
                    async with AsyncSessionLocal() as db:
                        q = text("""
                            SELECT 
                                e.ID_Empleado,
                                CONCAT(e.nombre1, ' ', e.Apellido1) AS nombre,
                                v.Ventanilla
                            FROM Empleado_Ventanilla ev
                            JOIN Ventanillas v ON ev.ID_Ventanilla = v.ID_Ventanilla
                            JOIN Empleado e ON ev.ID_Empleado = e.ID_Empleado
                            WHERE v.ID_Sector = :id_sector
                            AND ev.Fecha_Termino IS NULL
                            AND ev.ID_Estado = 1
                        """)
                        res = await db.execute(q, {"id_sector": id_sector})
                        empleados_con_ventanilla = [dict(r) for r in res.mappings().fetchall()]
                        
                    await manager.send_personal_json({
                        "type": "sector_ventanillas_status",
                        "id_sector": id_sector,
                        "puede_modificar": len(empleados_con_ventanilla) == 0,
                        "empleados_con_ventanilla": empleados_con_ventanilla
                    }, client_id)

                elif event_type == "ventanilla_register":
                    id_empleado = event_data.get('id_empleado')
                    session_token = event_data.get('session_token')
                    if id_empleado:
                        # Cancelar cualquier desconexión pendiente (por si fue un reload)
                        manager.cancel_disconnect(id_empleado)
                        
                        manager.sid_to_employee[client_id] = id_empleado
                        if session_token:
                            manager.sid_to_token[client_id] = session_token
                        manager.active_ventanilla_employees.add(id_empleado)
                        print(f"🟢 Empleado {id_empleado} activo en ventanilla (SID: {client_id})")
                        await manager.broadcast_json({"type": "ventanilla_status_changed"})

                elif event_type == "ventanilla_disconnect":
                    # Limpiará en el loop continue o try catch
                    await manager.disconnect(client_id)
                 
                else:
                    print(f"Evento Desconocido: {event_type}")

                # Renew session for privileged roles on any valid activity
                await renew_session_if_privileged(client_id)

            except json.JSONDecodeError:
                pass # Payload no valido
                
    except WebSocketDisconnect:
        await manager.disconnect(client_id)
