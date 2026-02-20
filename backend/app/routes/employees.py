from flask import Blueprint, request, jsonify
from hashlib import sha256
from app.models.database import get_db_connection

bp = Blueprint('employees', __name__, url_prefix='/api')

# --------------------------------------------------------
# LISTA GENERAL DE EMPLEADOS (sin actualizar estados)
# --------------------------------------------------------
@bp.route("/employees", methods=["GET"])
def get_employees():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT 
                e.ID_Empleado AS id, 
                e.ID_ROL AS rol_id,
                CONCAT(e.nombre1, ' ', e.nombre2, ' ', e.Apellido1, ' ', e.Apellido2) AS name,
                r.Rol AS rol,
                ee.Nombre AS estado
            FROM Empleado e
            LEFT JOIN Rol r ON e.ID_ROL = r.ID_Rol
            LEFT JOIN Estado_Empleado ee ON e.ID_Estado = ee.ID_Estado
        """)

        empleados = cursor.fetchall()
        return jsonify(empleados), 200

    except Exception as e:
        print(f"Error en get_employees: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

# --------------------------------------------------------
# EMPLEADOS CON INFORMACIÓN COMPLETA
# --------------------------------------------------------
@bp.route("/employees/full", methods=["GET"])
def get_employees_full():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT 
                e.ID_Empleado,
                e.nombre1,
                e.nombre2,
                e.Apellido1,
                e.Apellido2,
                e.Usuario,
                e.ID_ROL,
                r.Rol,
                e.ID_Estado,
                ee.Nombre as Estado_Empleado,
                ev.ID_Ventanilla,
                v.Ventanilla,
                s.Sector as Sector_Ventanilla,
                ev.ID_Estado as Estado_Ventanilla,
                eev.Nombre as Nombre_Estado_Ventanilla
            FROM Empleado e
            LEFT JOIN Rol r ON e.ID_ROL = r.ID_Rol
            LEFT JOIN Estado_Empleado ee ON e.ID_Estado = ee.ID_Estado
            LEFT JOIN Empleado_Ventanilla ev ON e.ID_Empleado = ev.ID_Empleado 
                AND ev.Fecha_Termino IS NULL
            LEFT JOIN Ventanillas v ON ev.ID_Ventanilla = v.ID_Ventanilla
            LEFT JOIN Sectores s ON v.ID_Sector = s.ID_Sector
            LEFT JOIN Estado_empleado_ventanilla eev ON ev.ID_Estado = eev.ID_Estado
            ORDER BY e.ID_Empleado
        """)
        
        empleados = cursor.fetchall()
        return jsonify(empleados), 200
        
    except Exception as e:
        print(f"Error en get_employees_full: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# --------------------------------------------------------
# 4️⃣ CAMBIAR ESTADO MANUAL DE UN EMPLEADO
# --------------------------------------------------------
@bp.route("/employees/<int:id_empleado>/estado", methods=["PUT"])
def update_employee_status(id_empleado):
    data = request.get_json()
    nuevo_estado = data.get("estado")
    
    if not nuevo_estado or nuevo_estado not in [1, 2, 3, 4]:
        return jsonify({"error": "Estado inválido. Use: 1=Activo, 2=Suspendido, 3=Despedido, 4=Inactivo"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT ID_ROL FROM Empleado WHERE ID_Empleado = %s", (id_empleado,))
        empleado = cursor.fetchone()
        
        if not empleado:
            return jsonify({"error": "Empleado no encontrado"}), 404
            
        if empleado["ID_ROL"] == 1:
            return jsonify({"error": "No se puede cambiar el estado del administrador"}), 403
        
        cursor.execute("""
            UPDATE Empleado
            SET ID_Estado = %s
            WHERE ID_Empleado = %s
        """, (nuevo_estado, id_empleado))
        
        conn.commit()
        return jsonify({"message": "Estado actualizado correctamente"}), 200
        
    except Exception as e:
        print(f"Error al actualizar estado manual: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# --------------------------------------------------------
# 5️⃣ VENTANILLA ACTIVA DE UN EMPLEADO
# --------------------------------------------------------
@bp.route("/empleado/<int:id_empleado>/ventanilla-activa", methods=["GET"])
def get_ventanilla_activa_empleado(id_empleado):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT 
                v.ID_Ventanilla,
                v.Ventanilla,
                s.Sector
            FROM Empleado_Ventanilla ev
            JOIN Ventanillas v ON ev.ID_Ventanilla = v.ID_Ventanilla
            JOIN Sectores s ON v.ID_Sector = s.ID_Sector
            WHERE ev.ID_Empleado = %s 
                AND ev.ID_Estado = 1
                AND ev.Fecha_Termino IS NULL
            LIMIT 1
        """, (id_empleado,))
        
        ventanilla = cursor.fetchone()
        return jsonify(ventanilla if ventanilla else {}), 200
        
    except Exception as e:
        print(f"Error al obtener ventanilla activa: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# --------------------------------------------------------
# AÑADIR NUEVO EMPLEADO
# --------------------------------------------------------
@bp.route("/employees/add", methods=["POST"])
def add_employee():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        passwd_hash = sha256(data['passwd'].encode()).hexdigest()

        cursor.execute("""
            INSERT INTO Empleado
            (ID_ROL, nombre1, nombre2, Apellido1, Apellido2, Usuario, Passwd, ID_Estado)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            data['id_rol'], data['nombre1'], data['nombre2'], data['apellido1'],
            data['apellido2'], data['usuario'], passwd_hash, 1
        ))
        conn.commit()
        return jsonify({"message": "Empleado agregado"}), 201
    except Exception as e:
        print(f"Error en add_employee: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        cursor.close()
        conn.close()

@bp.route("/employees/<int:id_empleado>/ventanilla", methods=["PUT"])
def asignar_ventanilla(id_empleado):
    data = request.get_json()
    nueva_ventanilla = data.get("id_ventanilla")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Estados
        cursor.execute("SELECT ID_Estado FROM Estado_empleado_ventanilla WHERE Nombre = 'Activo' LIMIT 1")
        estado_activo_id = cursor.fetchone()["ID_Estado"]

        cursor.execute("SELECT ID_Estado FROM Estado_empleado_ventanilla WHERE Nombre = 'Inactivo' LIMIT 1")
        estado_inactivo_id = cursor.fetchone()["ID_Estado"]

        # 1️⃣ Cerrar ventanilla actual SIEMPRE
        cursor.execute("""
            UPDATE Empleado_Ventanilla
            SET Fecha_Termino = NOW(), ID_Estado = %s
            WHERE ID_Empleado = %s AND Fecha_Termino IS NULL
        """, (estado_inactivo_id, id_empleado))

        # 2️⃣ Si se envió "null" → significa quitar ventanilla, NO asignar nueva
        if nueva_ventanilla is None:
            conn.commit()
            return jsonify({"message": "Ventanilla removida correctamente"}), 200

        # 3️⃣ VALIDAR que la nueva ventanilla no esté ocupada
        cursor.execute("""
            SELECT 1
            FROM Empleado_Ventanilla
            WHERE ID_Ventanilla = %s AND Fecha_Termino IS NULL AND ID_Estado = %s
        """, (nueva_ventanilla, estado_activo_id))

        if cursor.fetchone():
            return jsonify({"error": "La ventanilla ya está asignada a otro empleado"}), 400

        # 4️⃣ Insertar nueva ventanilla
        cursor.execute("""
            INSERT INTO Empleado_Ventanilla (ID_Empleado, ID_Ventanilla, Fecha_Inicio, ID_Estado)
            VALUES (%s, %s, NOW(), %s)
        """, (id_empleado, nueva_ventanilla, estado_activo_id))

        conn.commit()
        return jsonify({"message": "Ventanilla actualizada correctamente"}), 200

    except Exception as e:
        conn.rollback()
        print(f"Error al asignar ventanilla: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

# --------------------------------------------------------
# ACTUALIZAR DATOS BÁSICOS DE UN EMPLEADO
# --------------------------------------------------------
@bp.route("/employees/<int:id_empleado>", methods=["PUT"])
def update_employee(id_empleado):
    data = request.get_json()

    nombre1   = data.get("nombre1", "").strip()
    nombre2   = data.get("nombre2", "").strip()
    apellido1 = data.get("apellido1", "").strip()
    apellido2 = data.get("apellido2", "").strip()
    usuario   = data.get("usuario", "").strip()
    passwd    = data.get("passwd", "").strip()

    if not nombre1 or not apellido1 or not usuario:
        return jsonify({"error": "nombre1, apellido1 y usuario son obligatorios"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Protect admin
        cursor.execute("SELECT ID_ROL FROM Empleado WHERE ID_Empleado = %s", (id_empleado,))
        emp = cursor.fetchone()
        if not emp:
            return jsonify({"error": "Empleado no encontrado"}), 404
        if emp["ID_ROL"] == 1:
            return jsonify({"error": "No se puede editar al administrador"}), 403

        # Check username uniqueness (excluding current employee)
        cursor.execute(
            "SELECT 1 FROM Empleado WHERE Usuario = %s AND ID_Empleado != %s LIMIT 1",
            (usuario, id_empleado)
        )
        if cursor.fetchone():
            return jsonify({"error": "El nombre de usuario ya está en uso"}), 409

        if passwd:
            passwd_hash = sha256(passwd.encode()).hexdigest()
            cursor.execute("""
                UPDATE Empleado
                SET nombre1=%s, nombre2=%s, Apellido1=%s, Apellido2=%s, Usuario=%s, Passwd=%s
                WHERE ID_Empleado=%s
            """, (nombre1, nombre2, apellido1, apellido2, usuario, passwd_hash, id_empleado))
        else:
            cursor.execute("""
                UPDATE Empleado
                SET nombre1=%s, nombre2=%s, Apellido1=%s, Apellido2=%s, Usuario=%s
                WHERE ID_Empleado=%s
            """, (nombre1, nombre2, apellido1, apellido2, usuario, id_empleado))

        conn.commit()
        return jsonify({"message": "Empleado actualizado correctamente"}), 200

    except Exception as e:
        conn.rollback()
        print(f"Error en update_employee: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# --------------------------------------------------------
# VERIFICAR SI UN USUARIO YA EXISTE
# --------------------------------------------------------
@bp.route("/employees/exists/<usuario>", methods=["GET"])
def check_user_exists(usuario):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT 1 FROM Empleado WHERE Usuario = %s LIMIT 1", (usuario,))
        exists = cursor.fetchone() is not None
        return jsonify({"exists": exists}), 200
    except Exception as e:
        print(f"Error en check_user_exists: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
