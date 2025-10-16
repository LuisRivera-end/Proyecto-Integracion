from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import mysql.connector
import os
from datetime import datetime
import random
import string
from hashlib import sha256
from fpdf import FPDF

app = Flask(__name__)
CORS(app, 
    resources={r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }}
) 

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
        cursor.execute(f"""
            SELECT 1 FROM Turno 
            WHERE Folio = %s AND ID_Estados IN ({','.join(['%s']*len(estados_activos))})
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
    sector_nombre = data.get('sector')

    if not matricula or not sector_nombre:
        return jsonify({"error": "matrícula y sector son requeridos"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Buscar ID del alumno
    cursor.execute("SELECT ID_Alumno FROM Alumnos WHERE Matricula = %s", (matricula,))
    alumno = cursor.fetchone()
    if not alumno:
        cursor.close()
        conn.close()
        return jsonify({"error": "No se encontró alumno con esa matrícula"}), 404
    ID_Alumno = alumno["ID_Alumno"]

    # Buscar ID del sector
    cursor.execute("SELECT ID_Sector FROM Sectores WHERE Sector = %s", (sector_nombre,))
    sector = cursor.fetchone()
    if not sector:
        cursor.close()
        conn.close()
        return jsonify({"error": "No se encontró el sector especificado"}), 404
    ID_Sector = sector["ID_Sector"]

    # Generar folio y guardar
    Folio = generar_folio_unico(cursor)
    Fecha_Ticket = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    Fecha_Ticket_publico = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO Turno (ID_Alumno, ID_Sector, ID_Ventanilla, Fecha_Ticket, Folio, ID_Estados, Fecha_Ultimo_Estado)
        VALUES (%s, %s, NULL, %s, %s, 1, %s)
    """, (ID_Alumno, ID_Sector, Fecha_Ticket, Folio, Fecha_Ticket))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({
        "mensaje": "Ticket generado exitosamente",
        "folio": Folio,
        "fecha": Fecha_Ticket_publico,
        "alumno": matricula,
        "sector": sector_nombre
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
# TICKETS - CORREGIDO
# -------------------
@app.route("/api/tickets", methods=["GET"])
def get_tickets():
    sector = request.args.get("sector")
    print(f"Solicitando tickets para sector: {sector}")  # Debug
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT 
                t.Folio AS folio,
                t.ID_Turno AS id_turno,
                a.Matricula AS matricula,
                s.Sector AS sector,
                et.Nombre AS estado,
                t.Fecha_Ticket AS fecha_ticket
            FROM Turno t
            JOIN Alumnos a ON t.ID_Alumno = a.ID_Alumno
            JOIN Sectores s ON t.ID_Sector = s.ID_Sector
            JOIN Estados_Turno et ON t.ID_Estados = et.ID_Estado
            WHERE t.ID_Estados = 1  -- Solo tickets pendientes
            ORDER BY t.Fecha_Ticket ASC
        """)
        
        tickets = cursor.fetchall()
        print(f"Tickets encontrados: {len(tickets)}")
        print(f"Tickets: {tickets}")
        
        return jsonify(tickets), 200
        
    except Exception as e:
        print(f"Error en get_tickets: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()


# -------------------
# ATENDER TICKET - CORREGIDO
# -------------------
@app.route('/api/tickets/<folio>/attend', methods=['PUT'])
def attend_ticket(folio):
    try:
        data = request.get_json()
        id_ventanilla = data.get("id_ventanilla")
        print(f"Atendiendo ticket {folio} en ventanilla {id_ventanilla}")

        if not id_ventanilla:
            return jsonify({"error": "ID de ventanilla requerido"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        
        nueva_fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        # Actualizar el ticket - estado 3 = "Atendiendo"
        cursor.execute("""
            UPDATE Turno
            SET ID_Estados = 3, 
                Fecha_Ultimo_Estado = %s, 
                ID_Ventanilla = %s
            WHERE Folio = %s AND ID_Estados = 1
        """, (nueva_fecha, id_ventanilla, folio))

        if cursor.rowcount == 0:
            return jsonify({"error": "Ticket no encontrado o ya atendido"}), 404

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "message": f"Ticket {folio} en estado 'Atendiendo' por ventanilla {id_ventanilla}"
        }), 200

    except Exception as e:
        print(f"Error en attend_ticket: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500
        
@app.route("/api/tickets_count", methods=["GET"])
def get_tickets_count():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                s.Sector AS nombre_sector,
                COUNT(t.ID_Turno) AS cantidad
            FROM Turno t
            JOIN Sectores s ON t.ID_Sector = s.ID_Sector
            WHERE t.ID_Estados = 1  -- Solo tickets pendientes
            GROUP BY s.Sector
        """)
        resultados = cursor.fetchall()

        # Convertir a formato { 'Cajas': 3, 'Becas': 5, 'Servicios Escolares': 2 }
        conteos = {r["nombre_sector"]: r["cantidad"] for r in resultados}

        return jsonify(conteos), 200
    except Exception as e:
        import traceback
        print(f"Error en get_tickets_count: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/tickets/<folio>/complete', methods=['PUT'])
def complete_ticket(folio):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Fecha actual con milisegundos
        nueva_fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        cursor.execute("""
            UPDATE Turno
            SET ID_Estados = %s, Fecha_Ultimo_Estado = %s
            WHERE Folio = %s
        """, (4, nueva_fecha, folio))

        conn.commit()
        return jsonify({"message": f"Ticket {folio} marcado como 'Completado'"}), 200
    except Exception as e:
        print(f"Error en complete_ticket: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        cursor.close()
        conn.close()

# -------------------
# LOGIN - CORREGIDO (agregar sector)
# -------------------
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Consulta mejorada para incluir información del estado del empleado
        cursor.execute("""
            SELECT e.*, r.Rol, ee.Nombre as Estado_Empleado, s.Sector
            FROM Empleado e 
            LEFT JOIN Rol r ON e.ID_ROL = r.ID_Rol 
            LEFT JOIN Estado_Empleado ee ON e.ID_Estado = ee.ID_Estado
            LEFT JOIN Sectores s ON e.ID_Sector = s.ID_Sector
            WHERE e.Usuario = %s
        """, (username,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "Usuario no existe"}), 404

        # Verificar si el empleado está activo
        if user["ID_Estado"] != 1:  # 1 = Activo según tu estructura
            estado_empleado = user["Estado_Empleado"] or "Inactivo"
            return jsonify({"error": f"Usuario no activo. Estado actual: {estado_empleado}"}), 403

        # Hash de la contraseña para comparar
        hashed_pw = sha256(password.encode()).hexdigest()
        if user["Passwd"] != hashed_pw:
            return jsonify({"error": "Contraseña incorrecta"}), 401

        # Retornar información completa solo si está activo
        return jsonify({
            "id": user["ID_Empleado"],
            "nombre": f"{user['nombre1']} {user['Apellido1']}",
            "rol": user["ID_ROL"],
            "sector": user["Sector"],
            "estado": user["Estado_Empleado"]
        })
        
    except Exception as e:
        print(f"Error en login: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        cursor.close()
        conn.close()
    
@app.route("/api/employees", methods=["POST"])
def add_employee():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Hash de la contraseña
        passwd_hash = sha256(data['passwd'].encode()).hexdigest()

        # Mapear rol a sector automáticamente
        rol_a_sector = {
            1: 1, 
            2: 2,
            3: 3,  
            4: 4,  
        }

        id_rol = data['id_rol']
        id_sector = rol_a_sector.get(id_rol, None)
        if id_sector is None:
            return jsonify({"error": "Rol inválido"}), 400

        cursor.execute("""
            INSERT INTO Empleado
            (ID_ROL, ID_Sector, nombre1, nombre2, Apellido1, Apellido2, Usuario, Passwd, ID_Estado)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            id_rol, id_sector, data['nombre1'], data['nombre2'], data['apellido1'],
            data['apellido2'], data['usuario'], passwd_hash, data['id_estado']
        ))
        conn.commit()
        return jsonify({"message": "Empleado agregado"}), 201
    except Exception as e:
        print(f"Error en add_employee: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        cursor.close()
        conn.close()


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

# -------------------
# VENTANILLAS LIBRES 
# -------------------
@app.route("/api/ventanillas/libres/<int:id_empleado>", methods=["GET"])
def ventanillas_libres(id_empleado):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Primero obtener el rol del empleado
        cursor.execute("SELECT ID_ROL FROM Empleado WHERE ID_Empleado = %s", (id_empleado,))
        empleado = cursor.fetchone()
        
        if not empleado:
            return jsonify({"error": "Empleado no encontrado"}), 404
            
        id_rol = empleado["ID_ROL"]

        # Seleccionar ventanillas libres para ese rol
        cursor.execute("""
            SELECT 
                V.ID_Ventanilla,
                V.Ventanilla,
                S.ID_Sector, S.Sector
            FROM Ventanillas V
            JOIN Rol_Ventanilla RV ON V.ID_Ventanilla = RV.ID_Ventanilla
            JOIN Sectores S ON V.ID_Sector = S.ID_Sector
            LEFT JOIN Empleado_Ventanilla EV 
                ON V.ID_Ventanilla = EV.ID_Ventanilla AND EV.ID_Estado = 1
            WHERE EV.ID_Ventanilla IS NULL
                AND RV.ID_Rol = %s
        """, (id_rol,))

        ventanillas = cursor.fetchall()
        print(f"Ventanillas libres: {ventanillas}")
        return jsonify(ventanillas), 200
        
    except Exception as e:
        print(f"Error en ventanillas_libres: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        cursor.close()
        conn.close()
        
@app.route("/api/ventanilla/iniciar", methods=["POST", "OPTIONS"])
def iniciar_ventanilla():
    if request.method == "OPTIONS":
        response = jsonify({"message": "Preflight OK"})
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        return response, 200
    
    data = request.get_json()
    id_empleado = data.get("id_empleado")
    id_ventanilla = data.get("id_ventanilla")
    
    print(f"Iniciando ventanilla - Empleado: {id_empleado}, Ventanilla: {id_ventanilla}")

    if not id_empleado:
        # Solo se requiere el empleado, la ventanilla puede ser 0 para asignación automática
        return jsonify({"error": "Empleado requerido"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # --- LÓGICA DE ASIGNACIÓN AUTOMÁTICA ---
        if id_ventanilla == 0:
            # 1. Obtener el rol del empleado
            cursor.execute("SELECT ID_ROL FROM Empleado WHERE ID_Empleado = %s", (id_empleado,))
            empleado = cursor.fetchone()
            if not empleado:
                return jsonify({"error": "Empleado no encontrado"}), 404
            id_rol = empleado["ID_ROL"]
            
            # 2. Buscar la primera ventanilla libre para ese rol
            cursor.execute("""
                SELECT 
                    V.ID_Ventanilla,
                    V.Ventanilla
                FROM Ventanillas V
                JOIN Rol_Ventanilla RV ON V.ID_Ventanilla = RV.ID_Ventanilla
                LEFT JOIN Empleado_Ventanilla EV 
                    ON V.ID_Ventanilla = EV.ID_Ventanilla AND EV.ID_Estado = 1
                WHERE EV.ID_Ventanilla IS NULL
                    AND RV.ID_Rol = %s
                LIMIT 1
            """, (id_rol,))
            
            ventanilla_libre = cursor.fetchone()
            
            if not ventanilla_libre:
                return jsonify({"error": "No hay ventanillas libres disponibles para tu rol"}), 400
                
            id_ventanilla = ventanilla_libre["ID_Ventanilla"]
            nombre_ventanilla = ventanilla_libre["Ventanilla"]
            
        else:
            # Lógica para asignar un ID específico (si el frontend lo enviara)
            cursor.execute("SELECT Ventanilla FROM Ventanillas WHERE ID_Ventanilla = %s", (id_ventanilla,))
            ventanilla_data = cursor.fetchone()
            if not ventanilla_data:
                return jsonify({"error": "ID de ventanilla inválido"}), 400
            nombre_ventanilla = ventanilla_data["Ventanilla"]
            
            # Verificar si la ventanilla está libre
            cursor.execute("""
                SELECT 1 FROM Empleado_Ventanilla
                WHERE ID_Ventanilla = %s AND ID_Estado = 1
            """, (id_ventanilla,))
            
            if cursor.fetchone():
                return jsonify({"error": "Ventanilla ocupada"}), 400


        # --- LÓGICA DE ASIGNACIÓN (Común) ---
        # Registrar asignación (usar estado 1 = Activo)
        cursor.execute("""
            INSERT INTO Empleado_Ventanilla (ID_Empleado, ID_Ventanilla, Fecha_Inicio, ID_Estado)
            VALUES (%s, %s, NOW(), 1)
        """, (id_empleado, id_ventanilla))
        
        conn.commit()
        print(f"Ventanilla {id_ventanilla} iniciada para empleado {id_empleado}")
        
        # Devolver el ID y Nombre de la ventanilla asignada
        return jsonify({
            "message": "Ventanilla iniciada correctamente",
            "ID_Ventanilla": id_ventanilla,
            "Nombre_Ventanilla": nombre_ventanilla
        }), 201
        
    except Exception as e:
        print(f"Error en iniciar_ventanilla: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/api/ventanilla/cerrar", methods=["PUT"])
def cerrar_ventanilla():
    if request.method == "OPTIONS":
        response = jsonify({"message": "Preflight OK"})
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
        response.headers["Access-Control-Allow-Methods"] = "PUT, OPTIONS"
        return response, 200
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No se recibió JSON"}), 400

        id_empleado = data.get("id_empleado")
        if not id_empleado:
            return jsonify({"error": "Empleado requerido"}), 400

        print(f"Cerrando ventanilla para empleado: {id_empleado}")

        # PRIMERA CONEXIÓN: Solo para verificar
        conn_check = get_db_connection()
        cursor_check = conn_check.cursor(dictionary=True, buffered=True)  # BUFFERED=True
        
        cursor_check.execute("""
            SELECT ID_Asignacion 
            FROM Empleado_Ventanilla 
            WHERE ID_Empleado = %s AND ID_Estado = 1
        """, (id_empleado,))
        
        asignacion = cursor_check.fetchone()
        cursor_check.close()
        conn_check.close()
        
        if not asignacion:
            print(f"No se encontró ventanilla activa para el empleado {id_empleado}")
            return jsonify({"error": "No hay ventanilla activa para este empleado"}), 404

        # SEGUNDA CONEXIÓN: Solo para actualizar
        conn_update = get_db_connection()
        cursor_update = conn_update.cursor()
        
        cursor_update.execute("""
            UPDATE Empleado_Ventanilla
            SET Fecha_Termino = NOW(), 
                ID_Estado = 2
            WHERE ID_Empleado = %s AND ID_Estado = 1
        """, (id_empleado,))

        filas_afectadas = cursor_update.rowcount
        conn_update.commit()
        cursor_update.close()
        conn_update.close()

        print(f"Ventanilla cerrada. Filas afectadas: {filas_afectadas}")

        return jsonify({"message": "Ventanilla liberada correctamente"}), 200

    except Exception as e:
        print(f"Error en cerrar_ventanilla: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500
# -------------------
# LLAMAR SIGUIENTE TICKET - NUEVO ENDPOINT
# -------------------
@app.route('/api/tickets/llamar-siguiente', methods=['POST'])
def llamar_siguiente_ticket():
    try:
        data = request.get_json()
        id_ventanilla = data.get("id_ventanilla")
        id_empleado = data.get("id_empleado")
        
        print(f"Llamando siguiente ticket para ventanilla {id_ventanilla}")

        if not id_ventanilla or not id_empleado:
            return jsonify({"error": "Ventanilla y empleado requeridos"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Obtener el siguiente ticket pendiente (más antiguo)
        cursor.execute("""
            SELECT Folio, ID_Turno 
            FROM Turno 
            WHERE ID_Estados = 1 
            ORDER BY Fecha_Ticket ASC 
            LIMIT 1
        """)
        
        siguiente_ticket = cursor.fetchone()
        
        if not siguiente_ticket:
            return jsonify({"message": "No hay tickets pendientes"}), 404
        
        folio = siguiente_ticket["Folio"]
        
        # Atender el ticket - estado 3 = "Atendiendo"
        nueva_fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        cursor.execute("""
            UPDATE Turno
            SET ID_Estados = 3, 
                Fecha_Ultimo_Estado = %s, 
                ID_Ventanilla = %s
            WHERE Folio = %s
        """, (nueva_fecha, id_ventanilla, folio))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "message": f"Ticket {folio} llamado para atención",
            "folio": folio
        }), 200

    except Exception as e:
        print(f"Error en llamar_siguiente_ticket: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

    
class TicketPDF(FPDF):
    def header(self):
        # Imagen (logo superior)
        # Asegúrate de tener un archivo 'logo.png' en la misma carpeta
        script_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(script_dir, "ual.png")
        try:
            self.image(image_path, x=14, y=5, w=30)  # centrado aprox. en 58mm
        except Exception as e:
            print(f"Error al cargar la imagen en Docker: {e}")
            pass  # Evita error si no se encuentra la imagen
        self.ln(20)  # Espacio después del logo

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, "Esfuerzo que trasciende", 0, 0, "C")

def generar_ticket(matricula, numero_ticket, sector ,fecha):
    pdf = TicketPDF("P", "mm", (58, 100))  # 58mm de ancho (ticket estándar)
    pdf.add_page()

    # Encabezado
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, "TICKET", ln=True, align="C")
    pdf.ln(2)

    # Datos generales
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, f"N° Ticket: {numero_ticket}", ln=True)
    pdf.cell(0, 6, f"Matricula: {matricula}", ln=True)
    pdf.cell(0, 6, f"Sector: {sector}", ln=True)
    pdf.cell(0, 6, f"Fecha: {fecha}", ln=True)
    pdf.ln(3)

    # Separador
    pdf.cell(0, 0, "-" * 40, ln=True, align="C")
    pdf.ln(3)

    return pdf.output(dest='S').encode('latin-1')

@app.route('/api/ticket/download', methods=['POST'])
def download_ticket_pdf():
    # Asume que el frontend envía la matrícula, folio y sector después de crear el ticket
    data = request.get_json()
    matricula = data.get('matricula', 'N/A')
    numero_ticket = data.get('numero_ticket', 'N/A')
    sector = data.get('sector', 'N/A')
    fecha = data.get('fecha', 'N/A')
    
    try:
        # Generar el PDF en bytes
        pdf_bytes = generar_ticket(matricula, numero_ticket, sector,fecha)
        
        # Usar make_response para crear una respuesta HTTP con los bytes
        response = make_response(pdf_bytes)
        
        # Configurar las cabeceras
        response.headers['Content-Type'] = 'application/pdf'
        # 'inline' para que se muestre en el navegador; 'attachment' para que se descargue
        response.headers['Content-Disposition'] = f'inline; filename=ticket_{numero_ticket}.pdf'
        
        return response, 200
    except Exception as e:
        print(f"Error al generar PDF: {e}")
        return jsonify({"error": "Error interno al generar el PDF"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)