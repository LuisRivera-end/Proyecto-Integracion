from flask import Blueprint, request, jsonify, make_response, current_app
from app.models.database import get_db_connection
from app.utils.helpers import generar_folio_unico, obtener_fecha_actual, obtener_fecha_publico
from app.models.pdf_generator import generar_ticket_PDF
from datetime import datetime
import requests
import base64

bp = Blueprint('tickets', __name__, url_prefix='/api')

@bp.route('/ticket/print', methods=['POST'])
def request_ticket_print():
    data = request.get_json()
    
    try:
        # Generar PDF
        pdf_bytes = generar_ticket_PDF(
            data['matricula'],
            data['numero_ticket'], 
            data['sector'],
            data['fecha'],
            data['tiempo_estimado']
        )
        
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
        # Obtener la función de impresión desde la configuración de la app
        send_print_job = current_app.config.get('SEND_PRINT_JOB')
        
        if not send_print_job:
            return jsonify({"error": "Servicio de impresión no disponible"}), 500
        
        # Enviar trabajo de impresión via WebSocket
        success, message = send_print_job(
            pdf_content=pdf_base64,
            ticket_number=data['numero_ticket'],
            sector=data['sector']
        )
        
        if success:
            return jsonify({
                "message": message,
                "ticket_number": data['numero_ticket']
            }), 200
        else:
            return jsonify({"error": message}), 500
        
    except Exception as e:
        print(f"Error en impresión WebSocket: {e}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@bp.route('/ticket', methods=['POST'])
def generar_ticket():
    data = request.get_json()
    matricula = data.get('matricula')
    sector_nombre = data.get('sector')

    if not matricula or not sector_nombre:
        return jsonify({"error": "matrícula y sector son requeridos"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT ID_Alumno FROM Alumnos WHERE Matricula = %s", (matricula,))
        alumno = cursor.fetchone()
        if not alumno:
            return jsonify({"error": "No se encontró alumno con esa matrícula"}), 404
        ID_Alumno = alumno["ID_Alumno"]

        cursor.execute("SELECT ID_Sector FROM Sectores WHERE Sector = %s", (sector_nombre,))
        sector = cursor.fetchone()
        if not sector:
            return jsonify({"error": "No se encontró el sector especificado"}), 404
        ID_Sector = sector["ID_Sector"]

        Folio = generar_folio_unico(sector_nombre) 
        Fecha_Ticket = obtener_fecha_actual()
        Fecha_Ticket_publico = obtener_fecha_publico()

        cursor.execute("""
            INSERT INTO Turno (ID_Alumno, ID_Sector, ID_Ventanilla, Fecha_Ticket, Folio, ID_Estados, Fecha_Ultimo_Estado)
            VALUES (%s, %s, NULL, %s, %s, 1, %s)
        """, (ID_Alumno, ID_Sector, Fecha_Ticket, Folio, Fecha_Ticket))

        conn.commit()

        return jsonify({
            "mensaje": "Ticket generado exitosamente",
            "folio": Folio, # Este 'folio' ya es el folio completo de 6 caracteres (ej. C6H2S9)
            "fecha": Fecha_Ticket_publico,
            "alumno": matricula,
            "sector": sector_nombre
        }), 201

    except Exception as e:
        print(f"Error en generar_ticket: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        cursor.close()
        conn.close()

@bp.route("/tickets", methods=["GET"])
def get_tickets():
    sector = request.args.get("sector")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Si no se envía sector, mostrar TODOS los tickets en espera
        if not sector:
            cursor.execute("""
                SELECT 
                    t.Folio AS folio,
                    t.ID_Turno AS id_turno,
                    a.Matricula AS matricula,
                    CONCAT(a.nombre1, ' ', a.Apellido1) AS nombre_alumno,  -- AÑADIR ESTA LÍNEA
                    s.Sector AS sector,
                    et.Nombre AS estado,
                    t.Fecha_Ticket AS fecha_ticket
                FROM Turno t
                JOIN Alumnos a ON t.ID_Alumno = a.ID_Alumno
                JOIN Sectores s ON t.ID_Sector = s.ID_Sector
                JOIN Estados_Turno et ON t.ID_Estados = et.ID_Estado
                WHERE t.ID_Estados = 1
                ORDER BY t.Fecha_Ticket ASC
            """)
        else:
            # Si se envía sector, filtrar por ese sector
            cursor.execute("""
                SELECT 
                    t.Folio AS folio,
                    t.ID_Turno AS id_turno,
                    a.Matricula AS matricula,
                    CONCAT(a.nombre1, ' ', a.Apellido1) AS nombre_alumno,  -- AÑADIR ESTA LÍNEA
                    s.Sector AS sector,
                    et.Nombre AS estado,
                    t.Fecha_Ticket AS fecha_ticket
                FROM Turno t
                JOIN Alumnos a ON t.ID_Alumno = a.ID_Alumno
                JOIN Sectores s ON t.ID_Sector = s.ID_Sector
                JOIN Estados_Turno et ON t.ID_Estados = et.ID_Estado
                WHERE t.ID_Estados = 1 AND s.Sector = %s
                ORDER BY t.Fecha_Ticket ASC
            """, (sector,))
        
        tickets = cursor.fetchall()
        return jsonify(tickets), 200
        
    except Exception as e:
        print(f"Error en get_tickets: {e}")
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

@bp.route('/tickets/<folio>/attend', methods=['PUT'])
def attend_ticket(folio):
    try:
        data = request.get_json()
        id_ventanilla = data.get("id_ventanilla")

        if not id_ventanilla:
            return jsonify({"error": "ID de ventanilla requerido"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        
        nueva_fecha = obtener_fecha_actual()
        
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
        return jsonify({
            "message": f"Ticket {folio} en estado 'Atendiendo' por ventanilla {id_ventanilla}"
        }), 200

    except Exception as e:
        print(f"Error en attend_ticket: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        cursor.close()
        conn.close()

@bp.route('/tickets/<folio>/complete', methods=['PUT'])
def complete_ticket(folio):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        nueva_fecha = obtener_fecha_actual()
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

@bp.route('/tickets/<folio>/cancel', methods=['PUT'])
def cancel_ticket(folio):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        nueva_fecha = obtener_fecha_actual()
        cursor.execute("""
            UPDATE Turno
            SET ID_Estados = %s, Fecha_Ultimo_Estado = %s
            WHERE Folio = %s AND ID_Estados = 3
        """, (2, nueva_fecha, folio))

        if cursor.rowcount == 0:
            return jsonify({"error": "Ticket no encontrado o no está siendo atendido"}), 404

        conn.commit()
        return jsonify({"message": f"Ticket {folio} cancelado exitosamente"}), 200
        
    except Exception as e:
        print(f"Error en cancel_ticket: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        cursor.close()
        conn.close()
        
@bp.route("/tickets_count", methods=["GET"])
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
            WHERE t.ID_Estados = 1
            GROUP BY s.Sector
        """)
        resultados = cursor.fetchall()

        conteos = {r["nombre_sector"]: r["cantidad"] for r in resultados}
        return jsonify(conteos), 200
    except Exception as e:
        print(f"Error en get_tickets_count: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@bp.route("/total_tickets", methods=["GET"])
def total_tickets():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT COUNT(ID_Turno) AS cantidad FROM Turno WHERE DATE(Fecha_Ticket) = CURDATE()")
        Total = cursor.fetchall()
        return jsonify(Total), 200
    except Exception as e:
        print(f"Error en total_tickets: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
        
@bp.route('/tickets/llamar-siguiente', methods=['POST'])
def llamar_siguiente_ticket():
    try:
        data = request.get_json()
        id_ventanilla = data.get("id_ventanilla")
        id_empleado = data.get("id_empleado")
        
        if not id_ventanilla or not id_empleado:
            return jsonify({"error": "Ventanilla y empleado requeridos"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
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
        
        nueva_fecha = obtener_fecha_actual()
        cursor.execute("""
            UPDATE Turno
            SET ID_Estados = 3, 
                Fecha_Ultimo_Estado = %s, 
                ID_Ventanilla = %s
            WHERE Folio = %s
        """, (nueva_fecha, id_ventanilla, folio))

        conn.commit()
        return jsonify({
            "message": f"Ticket {folio} llamado para atención",
            "folio": folio
        }), 200

    except Exception as e:
        print(f"Error en llamar_siguiente_ticket: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        cursor.close()
        conn.close()

@bp.route('/ticket/download', methods=['POST'])
def download_ticket_pdf():
    data = request.get_json()
    matricula = data.get('matricula', 'N/A')
    numero_ticket = data.get('numero_ticket', 'N/A')
    sector = data.get('sector', 'N/A')
    fecha = data.get('fecha', 'N/A')
    tiempo_estimado = data.get('tiempo_estimado', 'N/A')
    
    try:
        pdf_bytes = generar_ticket_PDF(matricula, numero_ticket, sector, fecha, tiempo_estimado)
        
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=ticket_{numero_ticket}.pdf'
        
        return response, 200
    except Exception as e:
        print(f"Error al generar PDF: {e}")
        return jsonify({"error": "Error interno al generar el PDF"}), 500

@bp.route('/turno/<int:id_turno>/estado', methods=['PUT'])
def actualizar_estado_turno(id_turno):
    data = request.get_json()
    nuevo_estado = data.get("estado")

    if not nuevo_estado:
        return jsonify({"error": "Estado requerido"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        nueva_fecha = obtener_fecha_actual()
        cursor.execute("""
            UPDATE Turno
            SET ID_Estados = %s, Fecha_Ultimo_Estado = %s
            WHERE ID_Turno = %s
        """, (nuevo_estado, nueva_fecha, id_turno))

        conn.commit()
        return jsonify({"mensaje": "Estado actualizado correctamente"}), 200
    except Exception as e:
        print(f"Error en actualizar_estado_turno: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        cursor.close()
        conn.close()

@bp.route("/tiempo_espera_promedio/<sector_nombre>", methods=["GET"])
def tiempo_espera_promedio_por_sector(sector_nombre):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        print(f"🔍 Buscando tiempo estimado para sector: {sector_nombre}")
        
        # Buscar ID del sector
        cursor.execute("SELECT ID_Sector FROM Sectores WHERE Sector = %s", (sector_nombre,))
        sector_data = cursor.fetchone()
        
        if not sector_data:
            print(f"❌ Sector '{sector_nombre}' no encontrado en la base de datos")
            return jsonify({"tiempo_estimado": 5}), 200
            
        id_sector = sector_data["ID_Sector"]
        print(f"✅ Sector encontrado - ID: {id_sector}")
        
        # PRIMERO: Verificar si hay datos en la tabla Turno
        cursor.execute("""
            SELECT COUNT(*) as total_tickets 
            FROM Turno 
            WHERE ID_Sector = %s AND ID_Estados = 3
        """, (id_sector,))
        
        total_tickets = cursor.fetchone()["total_tickets"]
        print(f"📊 Total de tickets completados en sector {sector_nombre}: {total_tickets}")
        
        # 1. Calcular el tiempo promedio con consulta más flexible
        print("📊 Consultando tiempos históricos...")
        cursor.execute("""
            SELECT 
                AVG(TIMESTAMPDIFF(SECOND, t.Fecha_Ticket, t.Fecha_Ultimo_Estado)) as promedio_segundos,
                COUNT(*) as total_tickets
            FROM Turno t
            WHERE t.ID_Estados = 3  -- Tickets completados
            AND t.ID_Sector = %s
            AND t.Fecha_Ticket >= DATE_SUB(NOW(), INTERVAL 2 HOUR)  -- 2 horas
            AND t.Fecha_Ultimo_Estado > t.Fecha_Ticket  -- Asegurar que la fecha final sea mayor
            AND TIMESTAMPDIFF(SECOND, t.Fecha_Ticket, t.Fecha_Ultimo_Estado) 
        """, (id_sector,))
        
        resultado = cursor.fetchone()
        print(f"📈 Resultado consulta 2 horas: {resultado}")
        
        # Si no hay datos, intentar con rango aún más amplio
        if not resultado or resultado["total_tickets"] == 0:
            print("🕐 Consultando todos los tickets completados...")
            cursor.execute("""
                SELECT 
                    AVG(TIMESTAMPDIFF(SECOND, t.Fecha_Ticket, t.Fecha_Ultimo_Estado)) as promedio_segundos,
                    COUNT(*) as total_tickets
                FROM Turno t
                WHERE t.ID_Estados = 3
                AND t.ID_Sector = %s
                AND t.Fecha_Ultimo_Estado > t.Fecha_Ticket
                AND TIMESTAMPDIFF(SECOND, t.Fecha_Ticket, t.Fecha_Ultimo_Estado)
            """, (id_sector,))
            
            resultado = cursor.fetchone()
            print(f"📈 Resultado consulta completa: {resultado}")
        
        # 2. Contar tickets pendientes por delante en el mismo sector
        cursor.execute("""
            SELECT COUNT(*) as tickets_pendientes
            FROM Turno t
            WHERE t.ID_Sector = %s 
            AND t.ID_Estados = 1  -- Tickets pendientes
        """, (id_sector,))
        
        pendientes_result = cursor.fetchone()
        tickets_pendientes = pendientes_result["tickets_pendientes"] if pendientes_result else 0
        print(f"🎫 Tickets pendientes en sector {sector_nombre}: {tickets_pendientes}")
        
        # 3. Determinar el tiempo estimado base
        if resultado and resultado["promedio_segundos"] and resultado["total_tickets"] > 0:
            promedio_segundos = float(resultado["promedio_segundos"])
            tiempo_base = promedio_segundos / 60  # Convertir a minutos
            print(f"⏱️  Tiempo base calculado: {tiempo_base:.1f} minutos (de {resultado['total_tickets']} tickets)")
        else:
            # Valores por defecto según el sector
            tiempos_por_defecto = {
                "Cajas": 5,
                "Becas": 5,
                "Servicios Escolares": 5
            }
            tiempo_base = tiempos_por_defecto.get(sector_nombre, 5)
            print(f"⚙️  Usando tiempo por defecto: {tiempo_base} minutos (sin datos históricos)")
        
        # 4. Calcular tiempo total considerando tickets pendientes
        factor_por_ticket = 0.85
        tiempo_adicional = tickets_pendientes * (tiempo_base * factor_por_ticket)
        tiempo_total = tiempo_base + tiempo_adicional
        
        print(f"📐 Cálculo: Base={tiempo_base:.1f} + Pendientes={tickets_pendientes}×({tiempo_base:.1f}×{factor_por_ticket}) = {tiempo_total:.1f}")
        
        # 5. Aplicar factores de ajuste según la hora del día
        hora_actual = datetime.now().hour
        print(f"🕒 Hora actual: {hora_actual}")
        
        if 11 <= hora_actual <= 14:  # Hora pico (medio día)
            tiempo_total = tiempo_total * 1.4
            print("⚡ Aplicando ajuste por hora pico (+40%)")
        elif 15 <= hora_actual <= 17:  # Tarde
            tiempo_total = tiempo_total * 1.2
            print("🌅 Aplicando ajuste por tarde (+20%)")
        
        # Redondear y asegurar mínimo de 1 minuto
        tiempo_estimado = max(1, int(tiempo_total))
        
        print(f"✅ Tiempo estimado final: {tiempo_estimado} minutos")
        
        return jsonify({"tiempo_estimado": tiempo_estimado}), 200
        
    except Exception as e:
        print(f"❌ Error en tiempo_espera_promedio_por_sector: {e}")
        import traceback
        traceback.print_exc()
        
        # Valores por defecto en caso de error
        tiempos_por_defecto = {
            "Cajas": 5,
            "Becas": 5,
            "Servicios Escolares": 5
        }
        return jsonify({"tiempo_estimado": tiempos_por_defecto.get(sector_nombre, 5)}), 200
    finally:
        cursor.close()
        conn.close()


#Funcion Historial de Tickets 
@bp.route('/tickets/historial', methods=['GET'])
def get_historial_tickets():
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
                t.Fecha_Ticket AS fecha_ticket,
                t.Fecha_Ultimo_Estado AS fecha_ultimo_estado
            FROM Turno t
            JOIN Alumnos a ON t.ID_Alumno = a.ID_Alumno
            JOIN Sectores s ON t.ID_Sector = s.ID_Sector
            JOIN Estados_Turno et ON t.ID_Estados = et.ID_Estado
            ORDER BY t.Fecha_Ticket DESC
            LIMIT 100
        """)
        
        tickets = cursor.fetchall()
        return jsonify(tickets), 200
        
    except Exception as e:
        print(f"Error en get_historial_tickets: {e}")
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

@bp.route("/tickets/publico", methods=["GET"])
def get_tickets_publico():
    """Endpoint específico para la pantalla pública que muestra pendientes + atendiendo"""
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT 
                t.Folio AS folio,
                t.ID_Turno AS id_turno,
                t.ID_Ventanilla AS id_ventanilla,
                v.Ventanilla AS ventanilla,
                a.Matricula AS matricula,
                CONCAT(a.nombre1, ' ', a.Apellido1) AS nombre_alumno,
                s.Sector AS sector,
                et.Nombre AS estado,
                et.ID_Estado AS estado_id,
                t.Fecha_Ticket AS fecha_ticket
            FROM Turno t
            JOIN Alumnos a ON t.ID_Alumno = a.ID_Alumno
            JOIN Sectores s ON t.ID_Sector = s.ID_Sector
            JOIN Estados_Turno et ON t.ID_Estados = et.ID_Estado
            LEFT JOIN Ventanillas v ON t.ID_Ventanilla = v.ID_Ventanilla
            WHERE t.ID_Estados IN (1, 3)  -- Solo pendientes y atendiendo
            ORDER BY 
                CASE WHEN t.ID_Estados = 3 THEN 0 ELSE 1 END,  -- Atendiendo primero
                t.Fecha_Ticket ASC  -- Luego pendientes por antigüedad
        """)
        
        tickets = cursor.fetchall()
        return jsonify(tickets), 200
        
    except Exception as e:
        print(f"Error en get_tickets_publico: {e}")
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()