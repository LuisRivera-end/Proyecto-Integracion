from fastapi import WebSocket
from typing import Dict, Set, Any
import json
import asyncio

class ConnectionManager:
    def __init__(self):
        # Todos los WebSockets activos
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Tracking general por "Salas" o Namespaces
        self.rooms: Dict[str, Set[str]] = {
            "public": set(),      # Para pantallas al público
            "empleados": set()    # Para el dashboard de empleados
        }

        # Tracking de estado
        self.active_ventanilla_employees: Set[int] = set()
        self.sid_to_employee: Dict[str, int] = {}
        
        # Impresoras conectadas
        self.printers: Dict[str, Dict[str, Any]] = {}

    async def connect(self, client_id: str, websocket: WebSocket, room: str = "public"):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        
        if room not in self.rooms:
            self.rooms[room] = set()
        self.rooms[room].add(client_id)
        
        print(f"✅ WS Conectado: {client_id} (Room: {room})")

    async def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            
        for room_clients in self.rooms.values():
            room_clients.discard(client_id)

        # Limpiar empleado de ventanilla
        emp_id = self.sid_to_employee.pop(client_id, None)
        if emp_id:
            # Solo remover del set si NO hay otras conexiones para este mismo empleado (multi-pestaña)
            if emp_id not in self.sid_to_employee.values():
                self.active_ventanilla_employees.discard(emp_id)
                print(f"🔴 Empleado {emp_id} WS desconectado totalmente (SID: {client_id})")
                # Solo notificar cambio si el empleado realmente se fue del todo
                await self.broadcast_json({"type": "ventanilla_status_changed"})
            else:
                print(f"📉 Una conexión de Empleado {emp_id} cerrada, pero conserva otras activas.")

        # Limpiar impresora
        if client_id in self.printers:
            printer_name = self.printers[client_id]["printer_name"]
            del self.printers[client_id]
            print(f"❌ Impresora Desconectada: {printer_name} (ID: {client_id})")
        else:
            print(f"❌ WS Desconectado: {client_id}")

    async def _safe_send_json(self, client_id: str, ws: WebSocket, data: dict):
        try:
            # Timeout para evitar colgar el servidor si un cliente no responde
            await asyncio.wait_for(ws.send_json(data), timeout=2.0)
        except Exception:
            # No desconectar aquí para evitar recursividad infinita en disconnect()
            # el loop principal de routes.py se encargará vía WebSocketDisconnect
            pass

    async def broadcast_json(self, data: dict, room: str = None):
        """Envia un mensaje a todos o a una room especifica en paralelo"""
        if room and room in self.rooms:
            targets = [client_id for client_id in self.rooms[room]]
        else:
            targets = list(self.active_connections.keys())

        if not targets:
            return

        tasks = []
        for client_id in targets:
            ws = self.active_connections.get(client_id)
            if ws:
                tasks.append(self._safe_send_json(client_id, ws, data))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def send_personal_json(self, data: dict, client_id: str):
        ws = self.active_connections.get(client_id)
        if ws:
            try:
                await ws.send_json(data)
            except Exception:
                await self.disconnect(client_id)

    # ─── MÉTODOS DE IMPERSIÓN ───
    
    def register_printer(self, client_id: str, printer_name: str, location: str):
        self.printers[client_id] = {
            'printer_name': printer_name,
            'location': location,
            'status': 'available'
        }
        print(f"🖨️ Impresora registrada: {printer_name} en {location} (ID: {client_id})")

    def get_available_printer(self):
        for cid, pdata in self.printers.items():
            if pdata['status'] == 'available':
                return cid
        return None

    async def send_print_job(self, pdf_content: str, ticket_number: str, sector: str):
        client_id = self.get_available_printer()
        if not client_id:
            return False, 'No hay impresoras disponibles'
            
        data = {
            "type": "print_job",
            "pdf_content": pdf_content,
            "ticket_number": ticket_number,
            "sector": sector,
            "job_id": f"job_{ticket_number}"
        }
        
        await self.send_personal_json(data, client_id)
        self.printers[client_id]['status'] = 'printing'
        return True, f"Ticket enviado a {self.printers[client_id]['printer_name']}"

manager = ConnectionManager()
