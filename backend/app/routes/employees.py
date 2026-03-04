from flask import Blueprint, request, jsonify, session
from hashlib import sha256
from app.models.database import get_db_connection
from app import socketio
from app.websocket.ventanilla_handlers import active_ventanilla_employees

bp = Blueprint('employees', __name__, url_prefix='/api')


def _get_jefe_sector_filter(cursor):
    """Devuelve el ID de sector del jefe autenticado (rol 6), si aplica."""
    if session.get("rol") != 6:
        return None

    user_id = session.get("user_id")
    if not user_id:
        return None

    cursor.execute("SELECT ID_Sector FROM Empleado WHERE ID_Empleado = %s", (user_id,))
    jefe = cursor.fetchone()
    return jefe["ID_Sector"] if jefe and jefe.get("ID_Sector") else None

# --------------------------------------------------------
# LISTA GENERAL DE EMPLEADOS (sin actualizar estados)
# --------------------------------------------------------
@bp.route("/employees", methods=["GET"])
def get_employees():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        jefe_sector_id = _get_jefe_sector_filter(cursor)

        query = """
            SELECT 
                e.ID_Empleado AS id, 
                e.ID_ROL AS rol_id,
                CONCAT(e.nombre1, ' ', e.nombre2, ' ', e.Apellido1, ' ', e.Apellido2) AS name,
                r.Rol AS rol,
                ee.Nombre AS estado
            FROM Empleado e
            LEFT JOIN Rol r ON e.ID_ROL = r.ID_Rol
            LEFT JOIN Estado_Empleado ee ON e.ID_Estado = ee.ID_Estado
            LEFT JOIN Empleado_Ventanilla ev ON e.ID_Empleado = ev.ID_Empleado
                AND ev.Fecha_Termino IS NULL
            LEFT JOIN Ventanillas v ON ev.ID_Ventanilla = v.ID_Ventanilla
        """
        params = []

        if jefe_sector_id is not None:
            query += """
                WHERE (
                    e.ID_Sector = %s
                    OR v.ID_Sector = %s
                    OR EXISTS (
                        SELECT 1 FROM Rol_Ventanilla rv
                        JOIN Ventanillas vr ON rv.ID_Ventanilla = vr.ID_Ventanilla
                        WHERE rv.ID_Rol = e.ID_ROL AND vr.ID_Sector = %s
                    )
                )
            """
            params.extend([jefe_sector_id, jefe_sector_id, jefe_sector_id])

        cursor.execute(query, params)

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
        jefe_sector_id = _get_jefe_sector_filter(cursor)

        query = """
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
                eev.Nombre as Nombre_Estado_Ventanilla,
                e.ID_Sector as ID_Sector_Jefe,
                sj.Sector as Nombre_Sector_Jefe
            FROM Empleado e
            LEFT JOIN Rol r ON e.ID_ROL = r.ID_Rol
            LEFT JOIN Estado_Empleado ee ON e.ID_Estado = ee.ID_Estado
            LEFT JOIN Empleado_Ventanilla ev ON e.ID_Empleado = ev.ID_Empleado 
                AND ev.Fecha_Termino IS NULL
            LEFT JOIN Ventanillas v ON ev.ID_Ventanilla = v.ID_Ventanilla
            LEFT JOIN Sectores s ON v.ID_Sector = s.ID_Sector
            LEFT JOIN Sectores sj ON e.ID_Sector = sj.ID_Sector
            LEFT JOIN Estado_empleado_ventanilla eev ON ev.ID_Estado = eev.ID_Estado
        """
        params = []

        if jefe_sector_id is not None:
            query += """
                WHERE (
                    e.ID_Sector = %s
                    OR s.ID_Sector = %s
                    OR EXISTS (
                        SELECT 1 FROM Rol_Ventanilla rv
                        JOIN Ventanillas vr ON rv.ID_Ventanilla = vr.ID_Ventanilla
                        WHERE rv.ID_Rol = e.ID_ROL AND vr.ID_Sector = %s
                    )
                )
            """
            params.extend([jefe_sector_id, jefe_sector_id, jefe_sector_id])

        query += " ORDER BY e.ID_Empleado"

        cursor.execute(query, params)
        
        empleados = cursor.fetchall()
        return jsonify(empleados), 200
        
    except Exception as e:
        print(f"Error en get_employees_full: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# --------------------------------------------------------
# EMPLEADOS ACTIVOS EN VENTANILLA
# --------------------------------------------------------
@bp.route("/employees/activos", methods=["GET"])
def get_active_employees():
    """Devuelve la lista de IDs de empleados activos en ventanilla."""
    return jsonify(list(active_ventanilla_employees)), 200

# --------------------------------------------------------
# 4️⃣ CAMBIAR ESTADO MANUAL DE UN EMPLEADO
# --------------------------------------------------------
@bp.route("/employees/<int:id_empleado>/estado", methods=["PUT"])
def update_employee_status(id_empleado):
    if id_empleado in active_ventanilla_employees:
        return jsonify({"error": "No se puede modificar, el empleado está activo en ventanilla"}), 409

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

        # Si el usuario autenticado es Jefe (rol 6), forzar sector al suyo
        id_sector = data.get('id_sector')
        if session.get("rol") == 6:
            jefe_id = session.get("user_id")
            if jefe_id:
                cursor.execute("SELECT ID_Sector FROM Empleado WHERE ID_Empleado = %s", (jefe_id,))
                jefe_row = cursor.fetchone()
                if jefe_row:
                    id_sector = jefe_row.get("ID_Sector") if isinstance(jefe_row, dict) else jefe_row[0]

        # Validar: solo un Jefe de Departamento por sector
        if int(data['id_rol']) == 6 and id_sector:
            cursor.execute(
                "SELECT 1 FROM Empleado WHERE ID_ROL = 6 AND ID_Sector = %s LIMIT 1",
                (id_sector,)
            )
            if cursor.fetchone():
                return jsonify({"error": "Ya existe un Jefe de Departamento en este sector"}), 409

        cursor.execute("""
            INSERT INTO Empleado
            (ID_ROL, nombre1, nombre2, Apellido1, Apellido2, Usuario, Passwd, ID_Estado, ID_Sector)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            data['id_rol'], data['nombre1'], data['nombre2'], data['apellido1'],
            data['apellido2'], data['usuario'], passwd_hash, 1, id_sector
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
    if id_empleado in active_ventanilla_employees:
        return jsonify({"error": "No se puede modificar, el empleado está activo en ventanilla"}), 409

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
    if id_empleado in active_ventanilla_employees:
        return jsonify({"error": "No se puede modificar, el empleado está activo en ventanilla"}), 409

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
        cursor.execute("SELECT ID_ROL, ID_Sector FROM Empleado WHERE ID_Empleado = %s", (id_empleado,))
        emp = cursor.fetchone()
        if not emp:
            return jsonify({"error": "Empleado no encontrado"}), 404
        if emp["ID_ROL"] == 1:
            return jsonify({"error": "No se puede editar al administrador"}), 403

        # Si el usuario autenticado es Jefe (rol 6), verificar que el empleado pertenece a su sector
        if session.get("rol") == 6:
            jefe_sector_id = _get_jefe_sector_filter(cursor)
            if jefe_sector_id is not None and emp.get("ID_Sector") != jefe_sector_id:
                return jsonify({"error": "No tiene permisos para editar este empleado"}), 403

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
# --------------------------------------------------------
# LISTA DE SECTORES
# --------------------------------------------------------
@bp.route("/sectores", methods=["GET"])
def get_sectores():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT s.ID_Sector, s.Sector,
                   COUNT(v.ID_Ventanilla) AS Ventanillas
            FROM Sectores s
            LEFT JOIN Ventanillas v ON s.ID_Sector = v.ID_Sector
            GROUP BY s.ID_Sector, s.Sector
            ORDER BY s.Sector
        """)
        sectores = cursor.fetchall()
        return jsonify(sectores), 200
    except Exception as e:
        print(f"Error en get_sectores: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# --------------------------------------------------------
# AGREGAR NUEVO SECTOR
# --------------------------------------------------------
@bp.route("/sectores", methods=["POST"])
def add_sector():
    data = request.get_json()
    sector_nombre = (data.get("sector") or "").strip()

    if not sector_nombre:
        return jsonify({"error": "El nombre del sector es obligatorio"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    num_ventanillas = data.get("ventanillas", 0)
    try:
        num_ventanillas = int(num_ventanillas)
    except (TypeError, ValueError):
        num_ventanillas = 0

    try:
        # Verificar duplicado
        cursor.execute("SELECT 1 FROM Sectores WHERE Sector = %s LIMIT 1", (sector_nombre,))
        if cursor.fetchone():
            return jsonify({"error": "Ya existe un sector con ese nombre"}), 409

        cursor.execute("INSERT INTO Sectores (Sector) VALUES (%s)", (sector_nombre,))
        sector_id = cursor.lastrowid

        # Crear también un rol con el mismo nombre del sector
        cursor.execute("INSERT INTO Rol (Rol) VALUES (%s)", (f"Operador {sector_nombre}",))
        rol_id = cursor.lastrowid

        # Crear ventanillas y asignarlas al rol
        for i in range(1, num_ventanillas + 1):
            nombre_v = f"{sector_nombre}{i}"
            cursor.execute("INSERT INTO Ventanillas (Ventanilla, ID_Sector) VALUES (%s, %s)", (nombre_v, sector_id))
            v_id = cursor.lastrowid
            cursor.execute("INSERT INTO Rol_Ventanilla (ID_Rol, ID_Ventanilla) VALUES (%s, %s)", (rol_id, v_id))

        conn.commit()

        # Emitir evento para actualizar sectores en tiempo real
        socketio.emit('sectores_updated', namespace='/')

        return jsonify({"message": "Sector agregado correctamente", "id": sector_id}), 201
    except Exception as e:
        conn.rollback()
        print(f"Error en add_sector: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        cursor.close()
        conn.close()

# --------------------------------------------------------
# EDITAR SECTOR (nombre + ventanillas)
# --------------------------------------------------------
@bp.route("/sectores/<int:id_sector>", methods=["PUT"])
def update_sector(id_sector):
    data = request.get_json()
    nuevo_nombre = (data.get("sector") or "").strip()
    nuevas_ventanillas = data.get("ventanillas", None)

    if not nuevo_nombre:
        return jsonify({"error": "El nombre del sector es obligatorio"}), 400

    try:
        nuevas_ventanillas = int(nuevas_ventanillas) if nuevas_ventanillas is not None else None
    except (TypeError, ValueError):
        nuevas_ventanillas = None

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Verificar que el sector existe
        cursor.execute("SELECT * FROM Sectores WHERE ID_Sector = %s", (id_sector,))
        sector = cursor.fetchone()
        if not sector:
            return jsonify({"error": "Sector no encontrado"}), 404

        nombre_anterior = sector["Sector"]

        # Verificar nombre duplicado (excluyendo el actual)
        cursor.execute(
            "SELECT 1 FROM Sectores WHERE Sector = %s AND ID_Sector != %s LIMIT 1",
            (nuevo_nombre, id_sector)
        )
        if cursor.fetchone():
            return jsonify({"error": "Ya existe otro sector con ese nombre"}), 409

        # Actualizar nombre del sector
        cursor.execute("UPDATE Sectores SET Sector = %s WHERE ID_Sector = %s", (nuevo_nombre, id_sector))

        # Actualizar nombre del rol asociado
        cursor.execute(
            "UPDATE Rol SET Rol = %s WHERE Rol = %s",
            (f"Operador {nuevo_nombre}", f"Operador {nombre_anterior}")
        )

        # Obtener ventanillas actuales del sector
        cursor.execute(
            "SELECT ID_Ventanilla, Ventanilla FROM Ventanillas WHERE ID_Sector = %s ORDER BY ID_Ventanilla",
            (id_sector,)
        )
        ventanillas_actuales = cursor.fetchall()
        count_actual = len(ventanillas_actuales)

        # Ajustar cantidad de ventanillas si se especificó
        if nuevas_ventanillas is not None and nuevas_ventanillas != count_actual:
            # Obtener el rol para asignar ventanillas nuevas
            cursor.execute(
                "SELECT ID_Rol FROM Rol WHERE Rol = %s LIMIT 1",
                (f"Operador {nuevo_nombre}",)
            )
            rol_row = cursor.fetchone()
            rol_id = rol_row["ID_Rol"] if rol_row else None

            if nuevas_ventanillas > count_actual:
                # Agregar ventanillas
                for i in range(count_actual + 1, nuevas_ventanillas + 1):
                    nombre_v = f"{nuevo_nombre}{i}"
                    cursor.execute(
                        "INSERT INTO Ventanillas (Ventanilla, ID_Sector) VALUES (%s, %s)",
                        (nombre_v, id_sector)
                    )
                    v_id = cursor.lastrowid
                    if rol_id:
                        cursor.execute(
                            "INSERT INTO Rol_Ventanilla (ID_Rol, ID_Ventanilla) VALUES (%s, %s)",
                            (rol_id, v_id)
                        )

            elif nuevas_ventanillas < count_actual:
                # Eliminar ventanillas sobrantes (desde la última)
                ventanillas_a_eliminar = ventanillas_actuales[nuevas_ventanillas:]
                no_eliminadas = []

                for v in reversed(ventanillas_a_eliminar):
                    vid = v["ID_Ventanilla"]
                    # Verificar si tiene asignaciones activas
                    cursor.execute(
                        "SELECT 1 FROM Empleado_Ventanilla WHERE ID_Ventanilla = %s AND Fecha_Termino IS NULL LIMIT 1",
                        (vid,)
                    )
                    if cursor.fetchone():
                        no_eliminadas.append(v["Ventanilla"])
                        continue

                    # Verificar si tiene turnos pendientes/atendiendo
                    cursor.execute(
                        "SELECT 1 FROM Turno WHERE ID_Ventanilla = %s AND ID_Estados IN (1, 3) LIMIT 1",
                        (vid,)
                    )
                    if cursor.fetchone():
                        no_eliminadas.append(v["Ventanilla"])
                        continue

                    # Eliminar de Rol_Ventanilla y luego de Ventanillas
                    cursor.execute("DELETE FROM Rol_Ventanilla WHERE ID_Ventanilla = %s", (vid,))
                    cursor.execute("DELETE FROM Ventanillas WHERE ID_Ventanilla = %s", (vid,))

                if no_eliminadas:
                    conn.commit()
                    socketio.emit('sectores_updated', namespace='/')
                    return jsonify({
                        "message": "Sector actualizado, pero algunas ventanillas no se eliminaron porque están en uso",
                        "ventanillas_en_uso": no_eliminadas
                    }), 200

        conn.commit()
        socketio.emit('sectores_updated', namespace='/')
        return jsonify({"message": "Sector actualizado correctamente"}), 200

    except Exception as e:
        conn.rollback()
        print(f"Error en update_sector: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        cursor.close()
        conn.close()

# --------------------------------------------------------
# LISTAR VENTANILLAS DE UN SECTOR (con estado y empleado)
# --------------------------------------------------------
@bp.route("/sectores/<int:id_sector>/ventanillas", methods=["GET"])
def get_ventanillas_sector(id_sector):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT 1 FROM Sectores WHERE ID_Sector = %s", (id_sector,))
        if not cursor.fetchone():
            return jsonify({"error": "Sector no encontrado"}), 404

        cursor.execute("""
            SELECT 
                v.ID_Ventanilla,
                v.Ventanilla,
                v.Activa,
                CASE 
                    WHEN ev.ID_Empleado IS NOT NULL THEN CONCAT(e.nombre1, ' ', e.Apellido1)
                    ELSE NULL
                END AS empleado_asignado
            FROM Ventanillas v
            LEFT JOIN Empleado_Ventanilla ev 
                ON v.ID_Ventanilla = ev.ID_Ventanilla 
                AND ev.Fecha_Termino IS NULL 
                AND ev.ID_Estado = 1
            LEFT JOIN Empleado e ON ev.ID_Empleado = e.ID_Empleado
            WHERE v.ID_Sector = %s
            ORDER BY v.ID_Ventanilla
        """, (id_sector,))

        ventanillas = cursor.fetchall()
        return jsonify(ventanillas), 200

    except Exception as e:
        print(f"Error en get_ventanillas_sector: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        cursor.close()
        conn.close()


# --------------------------------------------------------
# EDITAR VENTANILLA INDIVIDUAL (nombre y/o estado)
# --------------------------------------------------------
@bp.route("/ventanillas/<int:id_ventanilla>", methods=["PUT"])
def update_ventanilla(id_ventanilla):
    data = request.get_json()
    nuevo_nombre = (data.get("nombre") or "").strip() if data.get("nombre") is not None else None
    nueva_activa = data.get("activa")  # 0 o 1

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT ID_Ventanilla, Ventanilla, Activa, ID_Sector FROM Ventanillas WHERE ID_Ventanilla = %s",
            (id_ventanilla,)
        )
        ventanilla = cursor.fetchone()
        if not ventanilla:
            return jsonify({"error": "Ventanilla no encontrada"}), 404

        # Actualizar nombre si se proporcionó
        if nuevo_nombre is not None and nuevo_nombre != ventanilla["Ventanilla"]:
            if not nuevo_nombre:
                return jsonify({"error": "El nombre de la ventanilla no puede estar vacío"}), 400
            cursor.execute(
                "UPDATE Ventanillas SET Ventanilla = %s WHERE ID_Ventanilla = %s",
                (nuevo_nombre, id_ventanilla)
            )

        # Actualizar estado activa si se proporcionó
        if nueva_activa is not None:
            nueva_activa = int(nueva_activa)
            if nueva_activa not in (0, 1):
                return jsonify({"error": "El estado debe ser 0 (inactiva) o 1 (activa)"}), 400

            if nueva_activa != ventanilla["Activa"]:
                # Si se va a deshabilitar, verificar que no tenga empleado asignado
                if nueva_activa == 0:
                    cursor.execute(
                        "SELECT 1 FROM Empleado_Ventanilla WHERE ID_Ventanilla = %s AND Fecha_Termino IS NULL AND ID_Estado = 1 LIMIT 1",
                        (id_ventanilla,)
                    )
                    if cursor.fetchone():
                        return jsonify({"error": "La ventanilla tiene un empleado asignado, no se puede deshabilitar"}), 409

                cursor.execute(
                    "UPDATE Ventanillas SET Activa = %s WHERE ID_Ventanilla = %s",
                    (nueva_activa, id_ventanilla)
                )

        conn.commit()
        socketio.emit('sectores_updated', namespace='/')
        socketio.emit('ventanilla_status_changed', namespace='/')

        return jsonify({"message": "Ventanilla actualizada correctamente"}), 200

    except Exception as e:
        conn.rollback()
        print(f"Error en update_ventanilla: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        cursor.close()
        conn.close()

# --------------------------------------------------------
# ASIGNAR SECTOR A UN EMPLEADO (PARA JEFES)
# --------------------------------------------------------
@bp.route("/employees/<int:id_empleado>/sector", methods=["PUT"])
def update_employee_sector(id_empleado):
    data = request.get_json()
    id_sector = data.get("id_sector")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Verificar que el empleado sea Jefe de Departamento
        cursor.execute("SELECT ID_ROL FROM Empleado WHERE ID_Empleado = %s", (id_empleado,))
        emp = cursor.fetchone()
        if not emp:
            return jsonify({"error": "Empleado no encontrado"}), 404

        # Validar: solo un Jefe de Departamento por sector
        if emp["ID_ROL"] == 6 and id_sector:
            cursor.execute(
                "SELECT 1 FROM Empleado WHERE ID_ROL = 6 AND ID_Sector = %s AND ID_Empleado != %s LIMIT 1",
                (id_sector, id_empleado)
            )
            if cursor.fetchone():
                return jsonify({"error": "Ya existe un Jefe de Departamento en este sector"}), 409

        cursor.execute("""
            UPDATE Empleado
            SET ID_Sector = %s
            WHERE ID_Empleado = %s
        """, (id_sector, id_empleado))
        conn.commit()
        return jsonify({"message": "Sector actualizado correctamente"}), 200
    except Exception as e:
        print(f"Error en update_employee_sector: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# --------------------------------------------------------
# SECTORES OCUPADOS POR JEFES DE DEPARTAMENTO
# --------------------------------------------------------
@bp.route("/sectores/ocupados", methods=["GET"])
def get_sectores_ocupados():
    """Retorna la lista de ID_Sector que ya tienen un Jefe de Departamento asignado."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT ID_Sector FROM Empleado
            WHERE ID_ROL = 6 AND ID_Sector IS NOT NULL AND ID_Estado != 3
        """)
        rows = cursor.fetchall()
        ocupados = [r["ID_Sector"] for r in rows]
        return jsonify(ocupados), 200
    except Exception as e:
        print(f"Error en get_sectores_ocupados: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
