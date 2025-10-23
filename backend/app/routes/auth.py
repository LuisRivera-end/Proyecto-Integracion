from flask import Blueprint, request, jsonify
from hashlib import sha256
from app.models.database import get_db_connection
from flask import session

bp = Blueprint('auth', __name__, url_prefix='/api')

@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT 
                e.*, 
                r.Rol, 
                ee.Nombre as Estado_Empleado,
                ev.ID_Ventanilla,
                v.Ventanilla,
                s.Sector as Sector_Ventanilla
            FROM Empleado e 
            LEFT JOIN Rol r ON e.ID_ROL = r.ID_Rol 
            LEFT JOIN Estado_Empleado ee ON e.ID_Estado = ee.ID_Estado
            LEFT JOIN Empleado_Ventanilla ev ON e.ID_Empleado = ev.ID_Empleado 
                AND ev.ID_Estado = 1 
                AND ev.Fecha_Termino IS NULL
            LEFT JOIN Ventanillas v ON ev.ID_Ventanilla = v.ID_Ventanilla
            LEFT JOIN Sectores s ON v.ID_Sector = s.ID_Sector
            WHERE e.Usuario = %s
        """, (username,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "Usuario no existe"}), 404

        if user["ID_Estado"] != 1:
            estado_empleado = user["Estado_Empleado"] or "Inactivo"
            return jsonify({"error": f"Usuario no activo. Estado actual: {estado_empleado}"}), 403

        hashed_pw = sha256(password.encode()).hexdigest()
        if user["Passwd"] != hashed_pw:
            return jsonify({"error": "Contraseña incorrecta"}), 401
        
        rol_a_sector = {
            1: "Admin",
            2: "Cajas", 
            3: "Becas",
            4: "Servicios Escolares"
        }
        
        sector = rol_a_sector.get(user["ID_ROL"], "Desconocido")
        
        session['user_id'] = user["ID_Empleado"]
        session['username'] = user["Usuario"]
        session['rol'] = user["ID_ROL"]
        session['sector'] = sector

        return jsonify({
            "id": user["ID_Empleado"],
            "nombre": f"{user['nombre1']} {user['Apellido1']}",
            "rol": user["ID_ROL"],
            "sector": sector,
            "estado": user["Estado_Empleado"],
            "id_ventanilla": user["ID_Ventanilla"],
            "ventanilla": user["Ventanilla"],
            "sector_ventanilla": user["Sector_Ventanilla"]
        })
        
    except Exception as e:
        print(f"Error en login: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        cursor.close()
        conn.close()
        
@bp.route('/logout', methods=['POST'])
def logout():
    session.clear()  # borra toda la sesión
    return jsonify({"message": "Sesión cerrada"}), 200

@bp.route('/check_session', methods=['GET'])
def check_session():
    if 'user_id' in session:
        return jsonify({"logged_in": True}), 200
    return jsonify({"logged_in": False}), 401

@bp.route('/roles', methods=['GET'])
def get_roles():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT ID_Rol, Rol FROM Rol WHERE ID_Rol != 1")
    roles = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(roles), 200

@bp.route('/estados_empleado', methods=['GET'])
def get_estados_empleado():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT ID_Estado, Nombre FROM Estado_Empleado")
    estados = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(estados), 200