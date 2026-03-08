from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.models.database import AsyncSessionLocal
from .manager import manager
import json

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
                    if id_empleado:
                        manager.sid_to_employee[client_id] = id_empleado
                        manager.active_ventanilla_employees.add(id_empleado)
                        print(f"🟢 Empleado {id_empleado} activo en ventanilla (SID: {client_id})")
                        await manager.broadcast_json({"type": "ventanilla_status_changed"})

                elif event_type == "ventanilla_disconnect":
                    # Limpiará en el loop continue o try catch
                    await manager.disconnect(client_id)
                
                else:
                    print(f"Evento Desconocido: {event_type}")

            except json.JSONDecodeError:
                pass # Payload no valido
                
    except WebSocketDisconnect:
        await manager.disconnect(client_id)
