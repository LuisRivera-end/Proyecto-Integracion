from flask import Blueprint, request, jsonify, send_from_directory
from app.models.database import get_db_connection
from app.utils.helpers import speak_to_file
import os

API_BASE_URL = os.getenv("IP_ADDRESS", "https://localhost:4443")

bp = Blueprint('ventanillas', __name__, url_prefix='/api')

@bp.route("/ventanillas/libres/<int:id_empleado>", methods=["GET"])
def ventanillas_libres(id_empleado):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT ID_ROL FROM Empleado WHERE ID_Empleado = %s", (id_empleado,))
        empleado = cursor.fetchone()
        
        if not empleado:
            return jsonify({"error": "Empleado no encontrado"}), 404
            
        id_rol = empleado["ID_ROL"]

        cursor.execute("""
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
                AND RV.ID_Rol = %s
        """, (id_rol,))

        ventanillas = cursor.fetchall()
        return jsonify(ventanillas), 200
        
    except Exception as e:
        print(f"Error en ventanillas_libres: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        cursor.close()
        conn.close()

@bp.route("/ventanilla/iniciar", methods=["POST", "OPTIONS"])
def iniciar_ventanilla():
    if request.method == "OPTIONS":
        response = jsonify({"message": "Preflight OK"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response, 200
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se recibió JSON"}), 400
    
    id_empleado = data.get("id_empleado")
    id_ventanilla = data.get("id_ventanilla")
    
    print(f"Iniciando ventanilla - Empleado: {id_empleado}, Ventanilla: {id_ventanilla}")

    if not id_empleado or not id_ventanilla:
        return jsonify({"error": "Empleado y ventanilla requeridos"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT 1 FROM Empleado_Ventanilla
            WHERE ID_Ventanilla = %s AND ID_Estado = 1 AND Fecha_Termino IS NULL
        """, (id_ventanilla,))
        
        if cursor.fetchone():
            return jsonify({"error": "Ventanilla ocupada"}), 400

        cursor.execute("""
            UPDATE Empleado_Ventanilla 
            SET Fecha_Termino = NOW(), ID_Estado = 2 
            WHERE ID_Empleado = %s AND ID_Estado = 1 AND Fecha_Termino IS NULL
        """, (id_empleado,))

        cursor.execute("""
            INSERT INTO Empleado_Ventanilla 
            (ID_Empleado, ID_Ventanilla, Fecha_Inicio, Fecha_Termino, ID_Estado)
            VALUES (%s, %s, NOW(), NULL, 1)
        """, (id_empleado, id_ventanilla))
        
        cursor.execute("""
            SELECT v.ID_Ventanilla, v.Ventanilla, s.Sector 
            FROM Ventanillas v 
            JOIN Sectores s ON v.ID_Sector = s.ID_Sector 
            WHERE v.ID_Ventanilla = %s
        """, (id_ventanilla,))
        ventanilla_info = cursor.fetchone()
        
        conn.commit()
        
        if not ventanilla_info:
            return jsonify({
                "message": "Ventanilla iniciada pero no se pudo obtener información",
                "ID_Ventanilla": id_ventanilla,
                "Nombre_Ventanilla": "Desconocida",
                "Sector_Ventanilla": "Desconocido"
            }), 201
        
        print(f"Ventanilla {id_ventanilla} iniciada para empleado {id_empleado}")
        
        return jsonify({
            "message": "Ventanilla iniciada correctamente",
            "ID_Ventanilla": ventanilla_info["ID_Ventanilla"],
            "Nombre_Ventanilla": ventanilla_info["Ventanilla"],
            "Sector_Ventanilla": ventanilla_info["Sector"]
        }), 201
        
    except Exception as e:
        conn.rollback()
        print(f"Error en iniciar_ventanilla: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

@bp.route("/ventanillas/disponibles/<int:id_rol>", methods=["GET"])
def get_ventanillas_disponibles(id_rol):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT 
                v.ID_Ventanilla,
                v.Ventanilla
            FROM Ventanillas v
            JOIN Rol_Ventanilla rv ON v.ID_Ventanilla = rv.ID_Ventanilla
            WHERE rv.ID_Rol = %s
            ORDER BY v.ID_Ventanilla
        """, (id_rol,))
        
        ventanillas = cursor.fetchall()
        return jsonify(ventanillas), 200
        
    except Exception as e:
        print(f"Error al obtener ventanillas: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@bp.route("/employees/<int:id_empleado>/ventanilla", methods=["PUT"])
def update_employee_ventanilla(id_empleado):
    data = request.get_json()
    id_ventanilla = data.get("id_ventanilla")
    
    if not id_ventanilla:
        return jsonify({"error": "ID de ventanilla requerido"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        conn.start_transaction()
        cursor.execute("""
        SELECT ID_Empleado 
            FROM Empleado_Ventanilla 
            WHERE ID_Ventanilla = %s AND ID_Estado = 1
        """, (id_ventanilla,))
        ocupada = cursor.fetchone()

        if ocupada:
            return jsonify({"error": "Esta ventanilla ya está ocupada, seleccione otra."}), 400
        
        cursor.execute("""
            INSERT INTO Empleado_Ventanilla 
            (ID_Empleado, ID_Ventanilla, Fecha_Inicio, Fecha_Termino, ID_Estado)
            VALUES (%s, %s, NOW(), NULL, 1)
        """, (id_empleado, id_ventanilla))
        
        conn.commit()
        return jsonify({"message": "Ventanilla asignada correctamente"}), 200
        
    except Exception as e:
        conn.rollback()
        print(f"Error al asignar ventanilla: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
        
@bp.route("/turno/llamar", methods=["POST"])
def llamar_turno():
    data = request.json
    folio = data["folio"]
    ventanilla = data["ventanilla"]

    texto = f"Turno {folio}, pasar a la ventanilla {ventanilla}"
    audio_file = speak_to_file(texto)

    return jsonify({
        "mensaje": "Turno llamado",
        "audio_url": f"{API_BASE_URL}/api/audio/{audio_file}"
    })
@bp.route("/audio/<filename>")
def get_audio(filename):
    return send_from_directory("/app/audio", filename)