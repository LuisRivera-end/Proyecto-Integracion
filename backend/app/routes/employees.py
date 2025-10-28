from flask import Blueprint, request, jsonify
from hashlib import sha256
from app.models.database import get_db_connection

bp = Blueprint('employees', __name__, url_prefix='/api')

# --------------------------------------------------------
# 1️⃣ LISTA GENERAL DE EMPLEADOS (sin actualizar estados)
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
# 2️⃣ ACTUALIZAR ESTADOS AUTOMÁTICAMENTE (según descansos)
# --------------------------------------------------------
@bp.route("/employees/update-status", methods=["POST"])
def update_employee_status_auto():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE Empleado e
            SET ID_Estado = CASE
                WHEN EXISTS (
                    SELECT 1
                    FROM Empleado_Horario h
                    WHERE h.ID_Empleado = e.ID_Empleado
                      AND CURDATE() BETWEEN DATE(h.Fecha_Inicio_Ausencia) AND DATE(h.Fecha_Final_Ausencia)
                ) THEN 2 -- Descanso
                ELSE 1 -- Activo
            END
            WHERE e.ID_Estado IN (1, 2) -- Solo actualizar si estaba Activo o en Descanso
        """)
        conn.commit()
        return jsonify({"message": "Estados actualizados correctamente"}), 200
    except Exception as e:
        conn.rollback()
        print(f"Error en update_employee_status_auto: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()




# --------------------------------------------------------
# 3️⃣ EMPLEADOS CON INFORMACIÓN COMPLETA
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
# 6️⃣ AÑADIR NUEVO EMPLEADO
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


# --------------------------------------------------------
# 7️⃣ GUARDAR DESCANSOS / AGENDA DEL EMPLEADO
# --------------------------------------------------------
@bp.route("/agenda", methods=["POST"])
def save_agenda():
    data = request.get_json()
    employee_id = data.get("employeeId")
    descansos = data.get("descansos", [])

    if not employee_id or not isinstance(descansos, list):
        return jsonify({"error": "Datos inválidos"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Borrar descansos antiguos del empleado
        cursor.execute("DELETE FROM Empleado_Horario WHERE ID_Empleado = %s", (employee_id,))

        # Insertar descansos nuevos
        for d in descansos:
            cursor.execute("""
                INSERT INTO Empleado_Horario (ID_Horario, ID_Empleado, Fecha_Inicio_Ausencia, Fecha_Final_Ausencia)
                VALUES (%s, %s, %s, %s)
            """, (1, employee_id, d.get("inicio"), d.get("fin")))

        conn.commit()
        return jsonify({"message": "Agenda guardada correctamente"}), 201

    except Exception as e:
        conn.rollback()
        print(f"Error en save_agenda: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()