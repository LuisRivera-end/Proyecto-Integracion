# backend/app.py
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import mysql.connector
import os
from datetime import datetime
import random
import string
from hashlib import sha256

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

@app.after_request
def apply_cors(response):
    """
    Añade encabezados CORS a todas las respuestas (incluidas las de error).
    """
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

# ✅ Manejador universal para preflight (OPTIONS)
@app.route('/api/<path:path>', methods=['OPTIONS'])
def handle_preflight(path):
    response = make_response(jsonify({"status": "OK"}), 200)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "mariadb"),
        user=os.getenv("DB_USER", "turnoadmin"),
        password=os.getenv("DB_PASSWORD", "13Demayo!"),
        database=os.getenv("DB_NAME", "TurnosUal")
    )

def generar_folio_unico(cursor):
    estados_activos = (1, 3)  # ID_Estados: 1 = Pendiente, 3 = Activo/Atendiendo
    while True:
        folio = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        cursor.execute("""
            SELECT 1 FROM Turno 
            WHERE Folio = %s AND ID_Estados IN (%s, %s)
        """, (folio, *estados_activos))
        if not cursor.fetchone():
            return folio
        
@app.route('/v1/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"}), 200

@app.route('/api/ticket', methods=['POST'])
def generar_ticket():
    data = request.get_json()
    matricula = data.get('matricula')
    sector = data.get('sector')

    if not matricula or not sector:
        return jsonify({"error": "matrícula y sector son requeridos"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 1️⃣ Buscar ID_Alumno a partir de la matrícula
    cursor.execute("SELECT ID_Alumno, nombre1, Apellido1 FROM Alumnos WHERE Matricula = %s", (matricula,))
    alumno = cursor.fetchone()

    if not alumno:
        return jsonify({"error": "No se encontró alumno con esa matrícula"}), 404

    ID_Alumno = alumno["ID_Alumno"]
    
    # 3️⃣ Generar folio aleatorio
    Folio = generar_folio_unico(cursor)
    Fecha_Ticket_publico = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    Fecha_Ticket = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    # 4️⃣ Insertar el turno con estado "Pendiente" (ID_Estado = 1)
    cursor.execute("""
        INSERT INTO Turno (ID_Alumno, ID_Ventanilla, Fecha_Ticket, Folio, ID_Estados, Fecha_Ultimo_Estado)
        VALUES (%s, NULL, %s, %s, 1)
    """, (ID_Alumno, Fecha_Ticket, Folio, Fecha_Ticket))

    
    conn.commit()

    # 5️⃣ Responder al frontend
    return jsonify({
        "mensaje": "Ticket generado exitosamente",
        "folio": Folio,
        "fecha": Fecha_Ticket_publico,
        "alumno": matricula,
        "sector": sector
    }), 201
    
@app.route('/api/turno/<int:id_turno>/estado', methods=['PUT'])
def actualizar_estado_turno(id_turno):
    data = request.get_json()
    nuevo_estado = data.get("estado")

    if not nuevo_estado:
        return jsonify({"error": "Estado requerido"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fecha actual con milisegundos
    nueva_fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    # Actualizar el estado y la fecha del último cambio
    cursor.execute("""
        UPDATE Turno
        SET ID_Estados = %s, Fecha_Ultimo_Estado = %s
        WHERE ID_Turno = %s
    """, (nuevo_estado, nueva_fecha, id_turno))

    conn.commit()
    return jsonify({"mensaje": "Estado actualizado correctamente"}), 200

# -------------------
# EMPLEADOS
# -------------------
@app.route("/api/employees", methods=["GET"])
def get_employees():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT ID_Empleado AS id, nombre1 AS name, ID_ROL AS sector FROM Empleado")
    empleados = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(empleados), 200

# -------------------
# AGENDA / DESCANSOS
# -------------------
@app.route("/api/agenda", methods=["POST"])
def save_agenda():
    data = request.get_json()
    employee_id = data.get("employeeId")
    descansos = data.get("descansos", [])

    if not employee_id or not isinstance(descansos, list):
        return jsonify({"error": "Datos inválidos"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    # borrar descansos antiguos del empleado
    cursor.execute("DELETE FROM Descansos WHERE ID_Empleado = %s", (employee_id,))
    # insertar descansos nuevos
    for d in descansos:
        cursor.execute(
            "INSERT INTO Descansos (ID_Empleado, Fecha_Inicio, Fecha_Fin) VALUES (%s, %s, %s)",
            (employee_id, d.get("inicio"), d.get("fin"))
        )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Agenda guardada correctamente"}), 201

# -------------------
# TICKETS
# -------------------
@app.route("/api/tickets", methods=["GET"])
def get_tickets():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT t.Folio, a.Matricula, e.Sector 
        FROM Turno t
        JOIN Alumnos a ON t.ID_Alumno = a.ID_Alumno
        JOIN Empleado e ON e.Sector = %s
        WHERE t.ID_Estados = 1
    """, (request.args.get("sector", ""),))
    tickets = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(tickets), 200

# -------------------
# ATENDER TICKET
# -------------------
@app.route('/api/tickets/<folio>/attend', methods=['PUT'])
def attend_ticket(folio):
    data = request.get_json()
    id_ventanilla = data.get("id_ventanilla")

    if not id_ventanilla:
        return jsonify({"error": "ID de ventanilla requerido"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    nueva_fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    cursor.execute("""
        UPDATE Turno
        SET ID_Estados = %s, Fecha_Ultimo_Estado = %s, ID_Ventanilla = %s
        WHERE Folio = %s
    """, (3, nueva_fecha, id_ventanilla, folio))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": f"Ticket {folio} en estado 'Atendiendo' por ventanilla {id_ventanilla}"}), 200

@app.route('/api/tickets/<folio>/complete', methods=['PUT'])
def complete_ticket(folio):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fecha actual con milisegundos
    nueva_fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    cursor.execute("""
        UPDATE Turno
        SET ID_Estados = %s, Fecha_Ultimo_Estado = %s
        WHERE Folio = %s
    """, (4, nueva_fecha, folio))

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": f"Ticket {folio} marcado como 'Completado'"}), 200


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Empleado WHERE Usuario = %s AND ID_Estado = 1", (username,))
    user = cursor.fetchone()

    if not user:
        return jsonify({"error": "Usuario no existe"}), 404

    hashed_pw = sha256(password.encode()).hexdigest()
    if user["Passwd"] != hashed_pw:
        return jsonify({"error": "Contraseña incorrecta"}), 401

    return jsonify({
        "id": user["ID_Empleado"],
        "nombre": f"{user['nombre1']} {user['Apellido1']}",
        "rol": user["ID_ROL"]
    })
    
@app.route("/api/employees", methods=["POST"])
def add_employee():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Hash de la contraseña
    passwd_hash = sha256(data['passwd'].encode()).hexdigest()

    cursor.execute("""
        INSERT INTO Empleado
        (ID_ROL, nombre1, nombre2, Apellido1, Apellido2, Usuario, Passwd, ID_Estado)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        data['id_rol'], data['nombre1'], data['nombre2'], data['apellido1'],
        data['apellido2'], data['usuario'], passwd_hash, data['id_estado']
    ))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Empleado agregado"}), 201

@app.route('/api/roles', methods=['GET'])
def get_roles():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT ID_Rol, Rol FROM Rol WHERE ID_Rol != 1")
    roles = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(roles), 200

@app.route('/api/estados_empleado', methods=['GET'])
def get_estados_empleado():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT ID_Estado, Nombre FROM Estado_Empleado")
    estados = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(estados), 200

@app.route("/api/ventanillas/libres/<int:id_rol>", methods=["GET"])
def ventanillas_libres(id_rol):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Seleccionamos ventanillas libres que pertenezcan al rol
    cursor.execute("""
        SELECT V.ID_Ventanilla, V.Ventanilla
        FROM Ventanillas V
        JOIN Rol_Ventanilla RV ON V.ID_Ventanilla = RV.ID_Ventanilla
        LEFT JOIN Empleado_Ventanilla EV 
            ON V.ID_Ventanilla = EV.ID_Ventanilla AND EV.ID_Estado = 1
        WHERE EV.ID_Ventanilla IS NULL
            AND RV.ID_Rol = %s
    """, (id_rol,))

    ventanillas = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(ventanillas), 200


@app.route("/api/ventanilla/iniciar", methods=["POST"])
def iniciar_ventanilla():
    data = request.get_json()
    id_empleado = data.get("id_empleado")
    id_ventanilla = data.get("id_ventanilla")
    
    if not id_empleado or not id_ventanilla:
        return jsonify({"error": "Empleado y ventanilla requeridos"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar si la ventanilla está libre
    cursor.execute("""
        SELECT 1 FROM Empleado_Ventanilla
        WHERE ID_Ventanilla = %s AND ID_Estado = 1
    """, (id_ventanilla,))
    
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"error": "Ventanilla ocupada"}), 400

    # Registrar asignación
    cursor.execute("""
        INSERT INTO Empleado_Ventanilla (ID_Empleado, ID_Ventanilla, Fecha_Inicio, ID_Estado)
        VALUES (%s, %s, NOW(), 1)
    """, (id_empleado, id_ventanilla))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({"message": "Ventanilla iniciada correctamente"}), 201

@app.route("/api/ventanilla/cerrar", methods=["PUT"])
def cerrar_ventanilla():
    data = request.get_json()
    id_empleado = data.get("id_empleado")
    
    if not id_empleado:
        return jsonify({"error": "Empleado requerido"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Terminar la asignación activa
    cursor.execute("""
        UPDATE Empleado_Ventanilla
        SET Fecha_Termino = NOW(), ID_Estado = 0
        WHERE ID_Empleado = %s AND ID_Estado = 1
    """, (id_empleado,))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({"message": "Ventanilla liberada"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)