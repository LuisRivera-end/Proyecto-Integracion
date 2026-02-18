from flask import Blueprint, request, session, redirect, jsonify, make_response, current_app
from app.models.database import get_db_connection
from app.utils.helpers import generar_folio_unico, obtener_fecha_actual, obtener_fecha_publico
from app.models.pdf_generator import generar_ticket_PDF
from datetime import datetime
import base64
import json

bp = Blueprint('tickets', __name__, url_prefix='/api')

@bp.route('/ticket/print', methods=['POST'])
def request_ticket_print():
    data = request.get_json()
    
    # ✅ Agregar logs de depuración
    print(f"🔍 DEBUG /ticket/print - Datos recibidos: {data}")
    
    try:
        # ✅ Verificar que los datos necesarios estén presentes
        if not data or 'numero_ticket' not in data:
            return jsonify({"error": "Datos incompletos: numero_ticket es requerido"}), 400
            
        numero_ticket = data['numero_ticket']
        print(f"🔍 DEBUG - Número de ticket: {numero_ticket}")
        
        # Generar PDF según el tipo
        try:
            print("🖨️ Generando PDF para ticket NORMAL")
            # Verificar datos requeridos para tickets normales
            required_fields = ['numero_ticket', 'sector', 'fecha']
            for field in required_fields:
                if field not in data:
                    return jsonify({"error": f"Campo requerido faltante: {field}"}), 400
                
            pdf_bytes = generar_ticket_PDF(
                data['numero_ticket'], 
                data['sector'],
                data['fecha']
            )
                
            print("✅ PDF generado exitosamente")
            
        except Exception as pdf_error:
            print(f"❌ Error al generar PDF: {pdf_error}")
            return jsonify({"error": f"Error al generar el PDF: {str(pdf_error)}"}), 500
        
        # Convertir a base64
        try:
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
            print("✅ PDF convertido a base64")
        except Exception as base64_error:
            print(f"❌ Error al convertir PDF a base64: {base64_error}")
            return jsonify({"error": "Error al procesar el PDF"}), 500
        
        # Obtener función de impresión
        send_print_job = current_app.config.get('SEND_PRINT_JOB')
        
        if not send_print_job:
            print("❌ Servicio de impresión no disponible")
            return jsonify({"error": "Servicio de impresión no disponible"}), 500
        
        # Enviar trabajo de impresión
        try:
            print("📤 Enviando trabajo de impresión...")
            success, message = send_print_job(
                pdf_content=pdf_base64,
                ticket_number=data['numero_ticket'],
                sector=data['sector']
            )
            
            if success:
                print(f"✅ Impresión exitosa: {message}")
                return jsonify({
                    "message": message,
                    "ticket_number": data['numero_ticket']
                }), 200
            else:
                print(f"❌ Error en impresión: {message}")
                return jsonify({"error": message}), 500
                
        except Exception as print_error:
            print(f"❌ Error al enviar a impresión: {print_error}")
            return jsonify({"error": f"Error de comunicación con la impresora: {str(print_error)}"}), 500
        
    except Exception as e:
        print(f"❌ Error general en impresión WebSocket: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500 


@bp.route('/ticket', methods=['POST'])
def generar_ticket():
    data = request.get_json()
    sector_nombre = data.get('sector')

    if not sector_nombre:
        return jsonify({"error": "sector es requerido"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT ID_Sector FROM Sectores WHERE Sector = %s", (sector_nombre,))
        sector = cursor.fetchone()
        if not sector:
            return jsonify({"error": "No se encontró el sector especificado"}), 404
        ID_Sector = sector["ID_Sector"]

        Folio = generar_folio_unico(sector_nombre) 
        Fecha_Ticket = obtener_fecha_actual()
        Fecha_Ticket_publico = obtener_fecha_publico()

        cursor.execute("""
            INSERT INTO Turno (ID_Sector, ID_Ventanilla, Fecha_Ticket, Folio, ID_Estados, Fecha_Ultimo_Estado)
            VALUES (%s, %s, NULL, %s, %s, 1, %s)
        """, (ID_Sector, Fecha_Ticket, Folio, Fecha_Ticket))

        conn.commit()

        return jsonify({
            "mensaje": "Ticket generado exitosamente",
            "folio": Folio,
            "fecha": Fecha_Ticket_publico,
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
    id_empleado = request.args.get("id_empleado")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Si se proporciona id_empleado, validar que solo vea tickets de su sector
        if id_empleado:
            cursor.execute("""
                SELECT DISTINCT s.Sector 
                FROM Empleado e
                JOIN Rol_Ventanilla rv ON e.ID_ROL = rv.ID_Rol
                JOIN Ventanillas v ON rv.ID_Ventanilla = v.ID_Ventanilla
                JOIN Sectores s ON v.ID_Sector = s.ID_Sector
                WHERE e.ID_Empleado = %s
            """, (id_empleado,))
            
            sector_empleado = cursor.fetchone()
            if sector_empleado:
                sector = sector_empleado["Sector"]
        if not sector:
            # Turnos normales
            cursor.execute("""
                SELECT 
                    t.Folio AS folio,
                    t.ID_Turno AS id_turno,
                    s.Sector AS sector,
                    et.Nombre AS estado,
                    t.Fecha_Ticket AS fecha_ticket,
                    'normal' AS tipo
                FROM Turno t
                JOIN Sectores s ON t.ID_Sector = s.ID_Sector
                JOIN Estados_Turno et ON t.ID_Estados = et.ID_Estado
                WHERE t.ID_Estados = 1
            """)
            tickets_normales = cursor.fetchall()
        else:
            # Turnos normales filtrados por sector
            cursor.execute("""
                SELECT 
                    t.Folio AS folio,
                    t.ID_Turno AS id_turno,
                    s.Sector AS sector,
                    et.Nombre AS estado,
                    t.Fecha_Ticket AS fecha_ticket,
                    'normal' AS tipo
                FROM Turno t
                JOIN Sectores s ON t.ID_Sector = s.ID_Sector
                JOIN Estados_Turno et ON t.ID_Estados = et.ID_Estado
                WHERE t.ID_Estados = 1 AND s.Sector = %s
            """, (sector,))
            tickets_normales = cursor.fetchall()
            
        #Combinar todos los tickets
        todos_tickets = tickets_normales
        todos_tickets.sort(key=lambda x: x['fecha_ticket'])
        return jsonify(todos_tickets), 200
    
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
        
        # Atender turno normal
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
        # Contar turnos normales
        cursor.execute("""
            SELECT 
                s.Sector AS nombre_sector,
                COUNT(t.ID_Turno) AS cantidad
            FROM Turno t
            JOIN Sectores s ON t.ID_Sector = s.ID_Sector
            WHERE t.ID_Estados = 1
            GROUP BY s.Sector
        """)
        normales = cursor.fetchall()

        conteos = {}
        for r in normales:
            conteos[r["nombre_sector"]] = conteos.get(r["nombre_sector"], 0) + r["cantidad"]
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
        normales = cursor.fetchone()
        Total = (normales["cantidad"] if normales else 0)
        return jsonify({"cantidad": Total}), 200
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
        
        #Obtener sector del empleado usando Rol_Ventanilla
        cursor.execute("""
            SELECT DISTINCT s.ID_Sector, s.Sector
            FROM Empleado e
            JOIN Rol_Ventanilla rv ON e.ID_ROL = rv.ID_Rol
            JOIN Ventanillas v ON rv.ID_Ventanilla = v.ID_Ventanilla
            JOIN Sectores s ON v.ID_Sector = s.ID_Sector
            WHERE e.ID_Empleado = %s
        """, (id_empleado,))
        
        sector_empleado = cursor.fetchone()
        if not sector_empleado:
            return jsonify({"error": "Empleado no tiene ventanillas/sectores asignados"}), 400
        
        id_sector = sector_empleado["ID_Sector"]
        nombre_sector = sector_empleado["Sector"]
        
        print(f"🔍 Empleado {id_empleado} puede atender sector: {nombre_sector} (ID: {id_sector})")
        
        # Buscar el siguiente ticket PENDIENTE del MISMO SECTOR
        cursor.execute("""
            (
                SELECT 
                    t.Folio, 
                    t.ID_Turno as id,
                    t.Fecha_Ticket
                FROM Turno t
                JOIN Alumnos a ON t.ID_Alumno = a.ID_Alumno
                WHERE t.ID_Estados = 1  -- Pendiente
                AND t.ID_Sector = %s    -- Mismo sector que el empleado
            )
            ORDER BY Fecha_Ticket ASC 
            LIMIT 1
        """, (id_sector,))
        
        siguiente_ticket = cursor.fetchone()
        
        if not siguiente_ticket:
            return jsonify({"message": "No hay tickets pendientes en tu sector"}), 404
        
        folio = siguiente_ticket["Folio"]
        
        print(f"🎯 Llamando ticket: {folio}")
        
        # Actualizar el ticket a "Atendiendo"
        nueva_fecha = obtener_fecha_actual()
        
        # Actualizar turno normal
        cursor.execute("""
            UPDATE Turno
            SET ID_Estados = 3, 
                Fecha_Ultimo_Estado = %s, 
                ID_Ventanilla = %s
            WHERE Folio = %s AND ID_Estados = 1
        """, (nueva_fecha, id_ventanilla, folio))
        if cursor.rowcount == 0:
            return jsonify({"error": "El ticket ya fue tomado por otro operador"}), 409

        conn.commit()
        
        return jsonify({
            "message": f"Ticket {folio} llamado para atención",
            "folio": folio,
        }), 200

    except Exception as e:
        print(f"❌ Error en llamar_siguiente_ticket: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        cursor.close()
        conn.close()

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
        # Actualizar turno normal
        cursor.execute("""
            UPDATE Turno
            SET ID_Estados = %s, Fecha_Ultimo_Estado = %s
            WHERE ID_Turno = %s
            """, (nuevo_estado, nueva_fecha, id_turno))
            
        if cursor.rowcount == 0:
            return jsonify({"error": "Turno no encontrado"}), 404

        conn.commit()
        return jsonify({"mensaje": "Estado actualizado correctamente"}), 200
    except Exception as e:
        print(f"Error en actualizar_estado_turno: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500
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
            (
                SELECT 
                    t.Folio AS folio,
                    t.ID_Turno AS id_turno,
                    s.Sector AS sector,
                    et.Nombre AS estado,
                    t.Fecha_Ticket AS fecha_ticket,
                    t.Fecha_Ultimo_Estado AS fecha_ultimo_estado,
                    'normal' AS tipo
                FROM Turno t
                JOIN Sectores s ON t.ID_Sector = s.ID_Sector
                JOIN Estados_Turno et ON t.ID_Estados = et.ID_Estado
            )
            ORDER BY fecha_ticket DESC
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
        # Turnos normales
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
                t.Fecha_Ticket AS fecha_ticket,
                'normal' AS tipo
            FROM Turno t
            JOIN Alumnos a ON t.ID_Alumno = a.ID_Alumno
            JOIN Sectores s ON t.ID_Sector = s.ID_Sector
            JOIN Estados_Turno et ON t.ID_Estados = et.ID_Estado
            LEFT JOIN Ventanillas v ON t.ID_Ventanilla = v.ID_Ventanilla
            WHERE t.ID_Estados IN (1, 3)
        """)
        tickets_normales = cursor.fetchall()
        
        # Combinar y ordenar
        todos_tickets = tickets_normales
        todos_tickets.sort(key=lambda x: (x['estado_id'] != 3, x['fecha_ticket']))
        return jsonify(todos_tickets), 200
        
    except Exception as e:
        print(f"Error en get_tickets_publico: {e}")
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()