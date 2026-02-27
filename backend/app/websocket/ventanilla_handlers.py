# app/websocket/ventanilla_handlers.py
from flask import request

# Tracking de empleados activos en ventanilla
active_ventanilla_employees = set()   # {id_empleado, ...}
sid_to_employee = {}                   # {sid: id_empleado}

def register_ventanilla_handlers(socketio):
    """Registrar handlers de WebSocket para ventanilla."""

    @socketio.on('ventanilla_register')
    def handle_ventanilla_register(data):
        """Un empleado de ventanilla se registra como activo."""
        id_empleado = data.get('id_empleado')
        if id_empleado:
            sid_to_employee[request.sid] = id_empleado
            active_ventanilla_employees.add(id_empleado)
            print(f'🟢 Empleado {id_empleado} activo en ventanilla (SID: {request.sid})')
            socketio.emit('ventanilla_status_changed', namespace='/')

    @socketio.on('ventanilla_disconnect')
    def handle_ventanilla_cleanup():
        """Limpieza manual si el frontend avisa antes de cerrar."""
        _cleanup_employee(request.sid, socketio)

    def _cleanup_employee(sid, sio):
        """Remover empleado del tracking al desconectarse."""
        id_empleado = sid_to_employee.pop(sid, None)
        if id_empleado:
            active_ventanilla_employees.discard(id_empleado)
            print(f'🔴 Empleado {id_empleado} salió de ventanilla (SID: {sid})')
            sio.emit('ventanilla_status_changed', namespace='/')

    # Exponer la función de limpieza para que print_handlers la use en disconnect
    return _cleanup_employee
