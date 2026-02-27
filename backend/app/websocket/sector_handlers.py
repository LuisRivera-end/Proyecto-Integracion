# app/websocket/sector_handlers.py
from flask import request
from app.models.database import get_db_connection


def register_sector_handlers(socketio):
    """Registrar handlers de WebSocket para sectores."""

    @socketio.on('check_sector_ventanillas')
    def handle_check_sector_ventanillas(data):
        """Verifica si algún empleado del sector tiene ventanilla activa."""
        id_sector = data.get('id_sector')
        if not id_sector:
            socketio.emit('sector_ventanillas_status', {
                'puede_modificar': False,
                'error': 'ID de sector requerido'
            }, room=request.sid)
            return

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            # Buscar empleados del sector que tengan ventanilla activa
            cursor.execute("""
                SELECT 
                    e.ID_Empleado,
                    CONCAT(e.nombre1, ' ', e.Apellido1) AS nombre,
                    v.Ventanilla
                FROM Empleado_Ventanilla ev
                JOIN Ventanillas v ON ev.ID_Ventanilla = v.ID_Ventanilla
                JOIN Empleado e ON ev.ID_Empleado = e.ID_Empleado
                WHERE v.ID_Sector = %s
                  AND ev.Fecha_Termino IS NULL
                  AND ev.ID_Estado = 1
            """, (id_sector,))

            empleados_con_ventanilla = cursor.fetchall()

            socketio.emit('sector_ventanillas_status', {
                'id_sector': id_sector,
                'puede_modificar': len(empleados_con_ventanilla) == 0,
                'empleados_con_ventanilla': empleados_con_ventanilla
            }, room=request.sid)

        except Exception as e:
            print(f"Error en check_sector_ventanillas: {e}")
            socketio.emit('sector_ventanillas_status', {
                'id_sector': id_sector,
                'puede_modificar': False,
                'error': str(e)
            }, room=request.sid)
        finally:
            cursor.close()
            conn.close()
