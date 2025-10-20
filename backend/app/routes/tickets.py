from flask import Blueprint, request, jsonify, make_response
from app.models.database import get_db_connection
from app.utils.helpers import generar_folio_unico, obtener_fecha_actual, obtener_fecha_publico
from app.models.pdf_generator import generar_ticket_PDF
from datetime import datetime  

bp = Blueprint('tickets', __name__, url_prefix='/api')

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

        Folio = generar_folio_unico()
        Fecha_Ticket = obtener_fecha_actual()
        Fecha_Ticket_publico = obtener_fecha_publico()

        cursor.execute("""
            INSERT INTO Turno (ID_Alumno, ID_Sector, ID_Ventanilla, Fecha_Ticket, Folio, ID_Estados, Fecha_Ultimo_Estado)
            VALUES (%s, %s, NULL, %s, %s, 1, %s)
        """, (ID_Alumno, ID_Sector, Fecha_Ticket, Folio, Fecha_Ticket))

        conn.commit()

        return jsonify({
            "mensaje": "Ticket generado exitosamente",
            "folio": Folio,
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
        cursor.execute("SELECT COUNT(ID_Turno) AS cantidad FROM Turno")
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
        # Buscar ID del sector
        cursor.execute("SELECT ID_Sector FROM Sectores WHERE Sector = %s", (sector_nombre,))
        sector_data = cursor.fetchone()
        
        if not sector_data:
            # Si no encuentra el sector, usar valor por defecto
            return jsonify({"tiempo_estimado": 5}), 200
            
        id_sector = sector_data["ID_Sector"]
        
        # Calcular el tiempo promedio de atención para tickets completados del mismo sector
        # Consideramos solo los tickets de las últimas 4 horas para mayor precisión
        cursor.execute("""
            SELECT 
                AVG(TIMESTAMPDIFF(MINUTE, t.Fecha_Ticket, t.Fecha_Ultimo_Estado)) as promedio_minutos,
                COUNT(*) as total_tickets
            FROM Turno t
            WHERE t.ID_Estados = 4  -- Tickets completados
            AND t.ID_Sector = %s
            AND t.Fecha_Ticket >= DATE_SUB(NOW(), INTERVAL 4 HOUR)
            AND TIMESTAMPDIFF(MINUTE, t.Fecha_Ticket, t.Fecha_Ultimo_Estado) > 0  -- Excluir tiempos negativos/erróneos
            AND TIMESTAMPDIFF(MINUTE, t.Fecha_Ticket, t.Fecha_Ultimo_Estado) < 120  -- Excluir tiempos muy largos (más de 2 horas)
        """, (id_sector,))
        
        resultado = cursor.fetchone()
        
        # Si no hay datos suficientes, ampliar el rango de tiempo
        if not resultado or resultado["total_tickets"] < 3:
            cursor.execute("""
                SELECT 
                    AVG(TIMESTAMPDIFF(MINUTE, t.Fecha_Ticket, t.Fecha_Ultimo_Estado)) as promedio_minutos
                FROM Turno t
                WHERE t.ID_Estados = 4  -- Tickets completados
                AND t.ID_Sector = %s
                AND t.Fecha_Ticket >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                AND TIMESTAMPDIFF(MINUTE, t.Fecha_Ticket, t.Fecha_Ultimo_Estado) > 0
                AND TIMESTAMPDIFF(MINUTE, t.Fecha_Ticket, t.Fecha_Ultimo_Estado) < 120
            """, (id_sector,))
            
            resultado = cursor.fetchone()
        
        # Determinar el tiempo estimado
        if resultado and resultado["promedio_minutos"]:
            promedio = resultado["promedio_minutos"]
            # Aplicar factores de ajuste según la hora del día
            hora_actual = datetime.now().hour
            if 11 <= hora_actual <= 14:  # Hora pico
                promedio = promedio * 1.3  # 30% más de tiempo en horas pico
            elif hora_actual >= 15:  # Tarde
                promedio = promedio * 0.8  # 20% menos en la tarde
            
            tiempo_estimado = max(5, min(60, round(promedio)))  # Entre 5 y 60 minutos
        else:
            # Valores por defecto según el sector si no hay datos históricos
            tiempos_por_defecto = {
                "Cajas": 5,
                "Becas": 10,
                "Servicios Escolares": 5
            }
            tiempo_estimado = tiempos_por_defecto.get(sector_nombre, 5)
        
        return jsonify({"tiempo_estimado": int(tiempo_estimado)}), 200
        
    except Exception as e:
        print(f"Error en tiempo_espera_promedio_por_sector: {e}")
        # Valores por defecto en caso de error
        tiempos_por_defecto = {
            "Cajas": 5,
            "Becas": 10,
            "Servicios Escolares": 5
        }
        return jsonify({"tiempo_estimado": tiempos_por_defecto.get(sector_nombre, 5)}), 200
    finally:
        cursor.close()
        conn.close()