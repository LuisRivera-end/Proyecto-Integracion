from flask import Blueprint, request, jsonify, current_app
from app.extensions import socketio
from app.models.database import get_db_connection
from datetime import datetime
import threading
import pytz

bp = Blueprint('caja_rapida', __name__, url_prefix='/api')

# ─── Estado en memoria ───
caja_rapida_state = {
    "activo": False,
    "expirado": False,
    "id_sector": None,
    "ventanillas": [],
    "hora_inicio": None,
    "hora_fin": None,
}

_timer = None
_app = None  # referencia a la app Flask para uso en threads
TZ = pytz.timezone('America/Mexico_City')


@bp.record
def store_app(state):
    """Guarda referencia a la app cuando se registra el blueprint."""
    global _app
    _app = state.app


def _contar_tickets_rapida_pendientes():
    """Cuenta tickets tipo 'rapida' con estado Pendiente (1)."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT COUNT(*) as total FROM Turno
            WHERE Tipo_Caja = 'rapida' AND ID_Estados = 1
        """)
        row = cursor.fetchone()
        return row["total"] if row else 0
    except Exception as e:
        print(f"Error contando tickets rápida: {e}")
        return 0
    finally:
        cursor.close()
        conn.close()


def _desactivar_caja_rapida():
    """Se ejecuta al expirar el timer dentro del contexto de la app."""
    global _timer, _app
    _timer = None

    if _app is None:
        print("⚠️ No hay referencia a la app Flask, desactivando sin verificar tickets")
        _desactivar_completo_sin_contexto()
        return

    with _app.app_context():
        pendientes = _contar_tickets_rapida_pendientes()

        if pendientes > 0:
            caja_rapida_state["activo"] = False
            caja_rapida_state["expirado"] = True
            print(f"⏰ Caja Rápida expirada — {pendientes} tickets pendientes, entrando en modo drenaje")
            socketio.emit('caja_rapida_updated', caja_rapida_state, namespace='/')
        else:
            _desactivar_completo_interno()


def _desactivar_completo_interno():
    """Desactiva todo y emite evento (debe llamarse dentro de app context)."""
    global _timer
    if _timer is not None:
        _timer.cancel()
        _timer = None
    caja_rapida_state["activo"] = False
    caja_rapida_state["expirado"] = False
    caja_rapida_state["id_sector"] = None
    caja_rapida_state["ventanillas"] = []
    caja_rapida_state["hora_inicio"] = None
    caja_rapida_state["hora_fin"] = None
    print("🛑 Caja Rápida desactivada completamente")
    socketio.emit('caja_rapida_updated', caja_rapida_state, namespace='/')


def _desactivar_completo_sin_contexto():
    """Fallback sin app context — limpia estado sin emitir."""
    global _timer
    if _timer is not None:
        _timer.cancel()
        _timer = None
    caja_rapida_state["activo"] = False
    caja_rapida_state["expirado"] = False
    caja_rapida_state["id_sector"] = None
    caja_rapida_state["ventanillas"] = []
    caja_rapida_state["hora_inicio"] = None
    caja_rapida_state["hora_fin"] = None


def _desactivar_completo():
    """Desactiva completamente, manejando contexto de app."""
    global _app
    if _app:
        with _app.app_context():
            _desactivar_completo_interno()
    else:
        _desactivar_completo_sin_contexto()


def _programar_expiracion(hora_fin_str):
    """Programa un timer para ejecutar al llegar hora_fin."""
    global _timer

    if _timer is not None:
        _timer.cancel()
        _timer = None

    try:
        ahora = datetime.now(TZ)
        hoy = ahora.date()
        hora_fin = datetime.strptime(hora_fin_str, "%H:%M").time()
        fin_dt = TZ.localize(datetime.combine(hoy, hora_fin))

        segundos = (fin_dt - ahora).total_seconds()

        if segundos <= 0:
            _desactivar_caja_rapida()
            return

        print(f"⏰ Caja Rápida se desactivará en {int(segundos)} segundos ({hora_fin_str})")
        _timer = threading.Timer(segundos, _desactivar_caja_rapida)
        _timer.daemon = True
        _timer.start()

    except Exception as e:
        print(f"Error al programar expiración: {e}")


# ─── Endpoints ───

@bp.route('/caja-rapida/activar', methods=['POST'])
def activar_caja_rapida():
    data = request.get_json()
    id_sector = data.get('id_sector')
    hora_fin = data.get('hora_fin')
    ventanillas = data.get('ventanillas', [])

    if not id_sector or not hora_fin:
        return jsonify({"error": "id_sector y hora_fin son requeridos"}), 400

    if not ventanillas or not isinstance(ventanillas, list) or len(ventanillas) == 0:
        return jsonify({"error": "Debes seleccionar al menos una ventanilla"}), 400

    ahora = datetime.now(TZ)

    caja_rapida_state["activo"] = True
    caja_rapida_state["expirado"] = False
    caja_rapida_state["id_sector"] = id_sector
    caja_rapida_state["ventanillas"] = ventanillas
    caja_rapida_state["hora_inicio"] = ahora.strftime("%H:%M")
    caja_rapida_state["hora_fin"] = hora_fin

    _programar_expiracion(hora_fin)

    print(f"🚀 Caja Rápida ACTIVADA - Sector {id_sector}, Ventanillas {ventanillas}, hasta {hora_fin}")
    socketio.emit('caja_rapida_updated', caja_rapida_state, namespace='/')

    return jsonify({
        "message": "Caja Rápida activada",
        **caja_rapida_state
    }), 200


@bp.route('/caja-rapida/desactivar', methods=['POST'])
def desactivar_caja_rapida_endpoint():
    _desactivar_completo_interno()
    return jsonify({
        "message": "Caja Rápida desactivada",
        **caja_rapida_state
    }), 200


@bp.route('/caja-rapida/estado', methods=['GET'])
def estado_caja_rapida():
    return jsonify(caja_rapida_state), 200


@bp.route('/caja-rapida/check-drenaje', methods=['POST'])
def check_drenaje():
    """Llamado después de completar/cancelar un ticket rapida."""
    if not caja_rapida_state["expirado"]:
        return jsonify({"drenando": False}), 200

    pendientes = _contar_tickets_rapida_pendientes()
    if pendientes == 0:
        _desactivar_completo_interno()
        return jsonify({"drenando": False, "message": "Modo drenaje finalizado"}), 200

    return jsonify({"drenando": True, "pendientes": pendientes}), 200
