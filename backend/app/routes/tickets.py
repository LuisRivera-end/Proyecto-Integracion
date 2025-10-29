from flask import Blueprint, request, session, redirect, jsonify, make_response, current_app
from app.models.database import get_db_connection
from app.utils.helpers import generar_folio_unico, obtener_fecha_actual, obtener_fecha_publico, generar_folio_invitado, es_turno_invitado
from app.models.pdf_generator import generar_ticket_PDF, generar_ticket_invitado_PDF
from datetime import datetime
import base64
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload
import json

bp = Blueprint('tickets', __name__, url_prefix='/api')


CLIENT_ID = "261213902739-l54b36b00cb3a933msoe4sq96q0g3jc9.apps.googleusercontent.com"
CLIENT_SECRET = "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"
REDIRECT_URI = "https://localhost:4443/api/google_callback"
AUTH_SCOPE = ['https://www.googleapis.com/auth/drive.file']
TOKEN_URI = 'https://oauth2.googleapis.com/token'
GOOGLE_DRIVE_FOLDER_ID = None

# Archivo de tokens
TOKEN_FILE = "token.json"
TOKEN_STORE = {}

# Funciones de persistencia
def save_tokens():
    """Guardar tokens en un archivo para que persistan entre reinicios"""
    with open(TOKEN_FILE, "w") as f:
        json.dump(TOKEN_STORE, f)

def load_tokens():
    """Cargar tokens desde archivo"""
    global TOKEN_STORE
    try:
        with open(TOKEN_FILE) as f:
            TOKEN_STORE = json.load(f)
    except FileNotFoundError:
        TOKEN_STORE = {}

# Función para obtener credenciales válidas
def get_valid_credentials():
    """
    Obtiene credenciales válidas, refrescando si es necesario
    """
    load_tokens()  # Cargar tokens actuales

    if not TOKEN_STORE.get('access_token'):
        return None

    # Crear objeto Credentials de Google
    creds = Credentials(
        token=TOKEN_STORE['access_token'],
        refresh_token=TOKEN_STORE.get('refresh_token'),
        token_uri=TOKEN_URI,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scopes=AUTH_SCOPE
    )

    # Verificar si el token expiró y refrescar si es necesario
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            # Actualizar almacenamiento
            TOKEN_STORE['access_token'] = creds.token
            TOKEN_STORE['expires_at'] = creds.expiry.timestamp() if creds.expiry else None
            save_tokens()
        except Exception as e:
            print(f"Error refrescando token: {e}")
            return None

    return creds

# Función para subir PDF a Google Drive
def subir_pdf_a_drive(pdf_bytes, nombre_archivo, folder_id=None):
    """
    Sube un PDF a Google Drive y retorna la URL de visualización
    """
    creds = get_valid_credentials()

    if not creds:
        raise Exception("No hay credenciales válidas de Google Drive. Autentica primero.")

    try:
        # Crear servicio de Google Drive
        service = build('drive', 'v3', credentials=creds)

        # Metadata del archivo
        file_metadata = {
            'name': nombre_archivo,
            'mimeType': 'application/pdf'
        }

        # Si se especifica una carpeta, asignarla
        if folder_id:
            file_metadata['parents'] = [folder_id]

        # Crear objeto de medios para la subida
        media = MediaInMemoryUpload(
            pdf_bytes,
            mimetype='application/pdf',
            resumable=True
        )

        # Subir archivo
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink, webContentLink'
        ).execute()

        print(f"✅ PDF subido exitosamente a Google Drive: {file.get('id')}")

        return {
            'file_id': file.get('id'),
            'view_link': file.get('webViewLink'),
            'download_link': file.get('webContentLink')
        }

    except Exception as e:
        print(f"❌ Error subiendo a Google Drive: {e}")
        raise Exception(f"Error al subir a Google Drive: {str(e)}")

# Endpoints de autenticación Google
@bp.route('/login_google')
def login_google():
    """Endpoint 1: Inicia el flujo OAuth2"""
    flow = Flow.from_client_config(
        {'web': {
            'client_id': CLIENT_ID, 
            'client_secret': CLIENT_SECRET, 
            'auth_uri': 'https://accounts.google.com/o/oauth2/v2/auth', 
            'token_uri': TOKEN_URI
        }},
        scopes=AUTH_SCOPE,
        redirect_uri=REDIRECT_URI
    )

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    session['google_oauth_state'] = state

    return redirect(authorization_url)

@bp.route('/google_callback')
def google_auth_callback():
    """Endpoint 2: Recibe el código de Google y realiza el intercambio por tokens"""
    flow = Flow.from_client_config(
        {
            'web': {
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'auth_uri': 'https://accounts.google.com/o/oauth2/v2/auth',
                'token_uri': TOKEN_URI
            }
        },
        scopes=AUTH_SCOPE,
        redirect_uri=REDIRECT_URI
    )

    try:
        flow.fetch_token(
            authorization_response=request.url,
            state=session.pop('google_oauth_state', None)
        )
    except Exception as e:
        return jsonify({"error": f"Error en la autenticación: {e}"}), 400

    # Almacenamiento
    TOKEN_STORE['access_token'] = flow.credentials.token
    TOKEN_STORE['refresh_token'] = flow.credentials.refresh_token
    TOKEN_STORE['expires_at'] = flow.credentials.expiry.timestamp() if flow.credentials.expiry else None

    save_tokens()

    return jsonify({
        "message": "✅ Autenticación con Google Drive completada.",
        "access_token": TOKEN_STORE['access_token'],
        "refresh_token": TOKEN_STORE['refresh_token'],
        "expira_en": TOKEN_STORE['expires_at']
    }), 200

# Endpoint para verificar estado de autenticación
@bp.route('/auth_status')
def auth_status():
    """Verifica si estamos autenticados y el estado del token"""
    creds = get_valid_credentials()

    if not creds:
        return jsonify({
            "authenticated": False,
            "message": "No autenticado. Visita /login_google"
        }), 401

    return jsonify({
        "authenticated": True,
        "expires_at": TOKEN_STORE.get('expires_at'),
        "has_refresh_token": bool(TOKEN_STORE.get('refresh_token'))
    }), 200

# Endpoint para verificar estado de Google Drive
@bp.route('/drive/status', methods=['GET'])
def drive_status():
    """Verifica el estado de la conexión con Google Drive"""
    try:
        creds = get_valid_credentials()

        if not creds:
            return jsonify({
                "authenticated": False,
                "message": "No autenticado con Google Drive"
            }), 401

        # Probar la conexión listando archivos (solo 1 para verificar)
        service = build('drive', 'v3', credentials=creds)
        results = service.files().list(
            pageSize=1,
            fields="files(id, name)"
        ).execute()

        return jsonify({
            "authenticated": True,
            "message": "Conexión con Google Drive activa",
            "files_count": len(results.get('files', [])),
            "expires_at": TOKEN_STORE.get('expires_at')
        }), 200

    except Exception as e:
        return jsonify({
            "authenticated": False,
            "error": f"Error en la conexión: {str(e)}"
        }), 401

# Endpoint principal para generar y subir tickets
@bp.route('/ticket/download', methods=['POST'])
def download_ticket_pdf():
    data = request.get_json()
    matricula = data.get('matricula', 'N/A')
    numero_ticket = data.get('numero_ticket', 'N/A')
    sector = data.get('sector', 'N/A')
    fecha = data.get('fecha', 'N/A')
    tiempo_estimado = data.get('tiempo_estimado', 'N/A')

    try:
        # 1. Generar el PDF
        pdf_bytes = generar_ticket_PDF(matricula, numero_ticket, sector, fecha, tiempo_estimado)

        # 2. Verificar autenticación con Google Drive
        creds = get_valid_credentials()
        if not creds:
            return jsonify({
                "error": "Autenticación de Google Drive requerida",
                "auth_url": f"{request.host_url}api/login_google"
            }), 401

        # 3. Subir a Google Drive
        nombre_archivo = f"Ticket_{numero_ticket}_{matricula}_{fecha.replace(' ', '_').replace(':', '-')}.pdf"

        drive_result = subir_pdf_a_drive(
            pdf_bytes=pdf_bytes,
            nombre_archivo=nombre_archivo,
            folder_id=GOOGLE_DRIVE_FOLDER_ID
        )

        # 4. Retornar éxito con información de Drive
        return jsonify({
            "message": "✅ Ticket generado y subido a Google Drive exitosamente",
            "drive_info": {
                "file_id": drive_result['file_id'],
                "view_link": drive_result['view_link'],
                "download_link": drive_result['download_link']
            },
            "ticket_info": {
                "matricula": matricula,
                "numero_ticket": numero_ticket,
                "sector": sector,
                "fecha": fecha,
                "tiempo_estimado": tiempo_estimado
            }
        }), 200

    except Exception as e:
        print(f"❌ Error en download_ticket_pdf: {e}")

        # Si el error es de autenticación, retornar 401
        if "No hay credenciales válidas" in str(e) or "autentica primero" in str(e):
            return jsonify({
                "error": "Autenticación de Google Drive requerida",
                "auth_url": f"{request.host_url}api/login_google"
            }), 401

        return jsonify({"error": f"Error interno: {str(e)}"}), 500

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
        
        # ✅ Manejar posibles errores en es_turno_invitado
        try:
            es_invitado = es_turno_invitado(numero_ticket)
            print(f"🔍 DEBUG - Es invitado: {es_invitado}")
        except Exception as e:
            print(f"❌ Error en es_turno_invitado: {e}")
            # Si falla la verificación, asumir que es ticket normal
            es_invitado = False
        
        # ✅ Generar PDF según el tipo
        try:
            if es_invitado:
                print("🖨️ Generando PDF para ticket INVITADO")
                # Verificar datos requeridos para invitados
                required_fields = ['numero_ticket', 'sector', 'fecha', 'tiempo_estimado']
                for field in required_fields:
                    if field not in data:
                        return jsonify({"error": f"Campo requerido faltante: {field}"}), 400
                
                pdf_bytes = generar_ticket_invitado_PDF(
                    data['numero_ticket'],
                    data['sector'],
                    data['fecha'],
                    data['tiempo_estimado']
                )
            else:
                print("🖨️ Generando PDF para ticket NORMAL")
                # Verificar datos requeridos para tickets normales
                required_fields = ['matricula', 'numero_ticket', 'sector', 'fecha', 'tiempo_estimado']
                for field in required_fields:
                    if field not in data:
                        return jsonify({"error": f"Campo requerido faltante: {field}"}), 400
                
                pdf_bytes = generar_ticket_PDF(
                    data['matricula'],
                    data['numero_ticket'], 
                    data['sector'],
                    data['fecha'],
                    data['tiempo_estimado']
                )
                
            print("✅ PDF generado exitosamente")
            
        except Exception as pdf_error:
            print(f"❌ Error al generar PDF: {pdf_error}")
            return jsonify({"error": f"Error al generar el PDF: {str(pdf_error)}"}), 500
        
        # ✅ Convertir a base64
        try:
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
            print("✅ PDF convertido a base64")
        except Exception as base64_error:
            print(f"❌ Error al convertir PDF a base64: {base64_error}")
            return jsonify({"error": "Error al procesar el PDF"}), 500
        
        # ✅ Obtener función de impresión
        send_print_job = current_app.config.get('SEND_PRINT_JOB')
        
        if not send_print_job:
            print("❌ Servicio de impresión no disponible")
            return jsonify({"error": "Servicio de impresión no disponible"}), 500
        
        # ✅ Enviar trabajo de impresión
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
        

@bp.route('/ticket/invitado', methods=['POST'])
def generar_ticket_invitado():
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

        Folio_Invitado = generar_folio_invitado(sector_nombre)
        Fecha_Ticket = obtener_fecha_actual()
        Fecha_Ticket_publico = obtener_fecha_publico()

        cursor.execute("""
            INSERT INTO Turno_Invitado (ID_Sector, ID_Ventanilla, Fecha_Ticket, Folio_Invitado, ID_Estados, Fecha_Ultimo_Estado)
            VALUES (%s, NULL, %s, %s, 1, %s)
        """, (ID_Sector, Fecha_Ticket, Folio_Invitado, Fecha_Ticket))

        conn.commit()

        return jsonify({
            "mensaje": "Ticket invitado generado exitosamente",
            "folio": Folio_Invitado,
            "fecha": Fecha_Ticket_publico,
            "sector": sector_nombre,
            "tipo": "invitado"
        }), 201

    except Exception as e:
        print(f"Error en generar_ticket_invitado: {e}")
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
                    a.Matricula AS matricula,
                    CONCAT(a.nombre1, ' ', a.Apellido1) AS nombre_alumno,
                    s.Sector AS sector,
                    et.Nombre AS estado,
                    t.Fecha_Ticket AS fecha_ticket,
                    'normal' AS tipo
                FROM Turno t
                JOIN Alumnos a ON t.ID_Alumno = a.ID_Alumno
                JOIN Sectores s ON t.ID_Sector = s.ID_Sector
                JOIN Estados_Turno et ON t.ID_Estados = et.ID_Estado
                WHERE t.ID_Estados = 1
            """)
            tickets_normales = cursor.fetchall()
            
            # Turnos invitados
            cursor.execute("""
                SELECT 
                    ti.Folio_Invitado AS folio,
                    ti.ID_TurnoInvitado AS id_turno,
                    NULL AS matricula,
                    'Invitado' AS nombre_alumno,
                    s.Sector AS sector,
                    et.Nombre AS estado,
                    ti.Fecha_Ticket AS fecha_ticket,
                    'invitado' AS tipo
                FROM Turno_Invitado ti
                JOIN Sectores s ON ti.ID_Sector = s.ID_Sector
                JOIN Estados_Turno et ON ti.ID_Estados = et.ID_Estado
                WHERE ti.ID_Estados = 1
            """)
            tickets_invitados = cursor.fetchall()
            
        else:
            # Turnos normales filtrados por sector
            cursor.execute("""
                SELECT 
                    t.Folio AS folio,
                    t.ID_Turno AS id_turno,
                    a.Matricula AS matricula,
                    CONCAT(a.nombre1, ' ', a.Apellido1) AS nombre_alumno,
                    s.Sector AS sector,
                    et.Nombre AS estado,
                    t.Fecha_Ticket AS fecha_ticket,
                    'normal' AS tipo
                FROM Turno t
                JOIN Alumnos a ON t.ID_Alumno = a.ID_Alumno
                JOIN Sectores s ON t.ID_Sector = s.ID_Sector
                JOIN Estados_Turno et ON t.ID_Estados = et.ID_Estado
                WHERE t.ID_Estados = 1 AND s.Sector = %s
            """, (sector,))
            tickets_normales = cursor.fetchall()
            
            # Turnos invitados filtrados por sector
            cursor.execute("""
                SELECT 
                    ti.Folio_Invitado AS folio,
                    ti.ID_TurnoInvitado AS id_turno,
                    NULL AS matricula,
                    'Invitado' AS nombre_alumno,
                    s.Sector AS sector,
                    et.Nombre AS estado,
                    ti.Fecha_Ticket AS fecha_ticket,
                    'invitado' AS tipo
                FROM Turno_Invitado ti
                JOIN Sectores s ON ti.ID_Sector = s.ID_Sector
                JOIN Estados_Turno et ON ti.ID_Estados = et.ID_Estado
                WHERE ti.ID_Estados = 1 AND s.Sector = %s
            """, (sector,))
            tickets_invitados = cursor.fetchall()
        #Combinar todos los tickets
        todos_tickets = tickets_normales + tickets_invitados
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
        
        if es_turno_invitado(folio):
            # Atender turno invitado
            cursor.execute("""
                UPDATE Turno_Invitado
                SET ID_Estados = 3, 
                    Fecha_Ultimo_Estado = %s, 
                    ID_Ventanilla = %s
                WHERE Folio_Invitado = %s AND ID_Estados = 1
            """, (nueva_fecha, id_ventanilla, folio))
        else:
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
        
        if es_turno_invitado(folio):
            cursor.execute("""
                UPDATE Turno_Invitado
                SET ID_Estados = %s, Fecha_Ultimo_Estado = %s
                WHERE Folio_Invitado = %s
            """, (4, nueva_fecha, folio))
        else:
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
        
        if es_turno_invitado(folio):
            cursor.execute("""
                UPDATE Turno_Invitado
                SET ID_Estados = %s, Fecha_Ultimo_Estado = %s
                WHERE Folio_Invitado = %s AND ID_Estados = 3
            """, (2, nueva_fecha, folio))
        else:
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

        # Contar turnos invitados
        cursor.execute("""
            SELECT 
                s.Sector AS nombre_sector,
                COUNT(ti.ID_TurnoInvitado) AS cantidad
            FROM Turno_Invitado ti
            JOIN Sectores s ON ti.ID_Sector = s.ID_Sector
            WHERE ti.ID_Estados = 1
            GROUP BY s.Sector
        """)
        invitados = cursor.fetchall()

        conteos = {}
        for r in normales:
            conteos[r["nombre_sector"]] = conteos.get(r["nombre_sector"], 0) + r["cantidad"]
        
        for r in invitados:
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
        cursor.execute("SELECT COUNT(ID_TurnoInvitado) AS cantidad FROM Turno_Invitado WHERE DATE(Fecha_Ticket) = CURDATE()")
        invitados = cursor.fetchone()
        
        Total = (normales["cantidad"] if normales else 0) + (invitados["cantidad"] if invitados else 0)
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
        
        # 🔥 CONSULTA CORREGIDA - Obtener sector del empleado usando Rol_Ventanilla
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
        
        # 🔥 Buscar el siguiente ticket PENDIENTE del MISMO SECTOR
        cursor.execute("""
            (
                -- TURNOS NORMALES
                SELECT 
                    t.Folio, 
                    t.ID_Turno as id,
                    a.Matricula, 
                    CONCAT(a.nombre1, ' ', a.Apellido1) AS nombre_alumno,
                    'normal' AS tipo,
                    t.Fecha_Ticket
                FROM Turno t
                JOIN Alumnos a ON t.ID_Alumno = a.ID_Alumno
                WHERE t.ID_Estados = 1  -- Pendiente
                AND t.ID_Sector = %s    -- Mismo sector que el empleado
            )
            UNION ALL
            (
                -- TURNOS INVITADOS  
                SELECT 
                    ti.Folio_Invitado AS Folio,
                    ti.ID_TurnoInvitado as id,
                    NULL AS Matricula,
                    'Invitado' AS nombre_alumno,
                    'invitado' AS tipo,
                    ti.Fecha_Ticket
                FROM Turno_Invitado ti
                WHERE ti.ID_Estados = 1  -- Pendiente
                AND ti.ID_Sector = %s    -- Mismo sector que el empleado
            )
            ORDER BY Fecha_Ticket ASC 
            LIMIT 1
        """, (id_sector, id_sector))
        
        siguiente_ticket = cursor.fetchone()
        
        if not siguiente_ticket:
            return jsonify({"message": "No hay tickets pendientes en tu sector"}), 404
        
        folio = siguiente_ticket["Folio"]
        tipo_ticket = siguiente_ticket["tipo"]
        matricula = siguiente_ticket["Matricula"]
        nombre_alumno = siguiente_ticket["nombre_alumno"]
        
        print(f"🎯 Llamando ticket: {folio} - Tipo: {tipo_ticket} - Alumno: {nombre_alumno}")
        
        # Actualizar el ticket a "Atendiendo"
        nueva_fecha = obtener_fecha_actual()
        
        if tipo_ticket == "normal":
            # Actualizar turno normal
            cursor.execute("""
                UPDATE Turno
                SET ID_Estados = 3, 
                    Fecha_Ultimo_Estado = %s, 
                    ID_Ventanilla = %s
                WHERE Folio = %s AND ID_Estados = 1
            """, (nueva_fecha, id_ventanilla, folio))
        else:
            # Actualizar turno invitado
            cursor.execute("""
                UPDATE Turno_Invitado
                SET ID_Estados = 3, 
                    Fecha_Ultimo_Estado = %s, 
                    ID_Ventanilla = %s
                WHERE Folio_Invitado = %s AND ID_Estados = 1
            """, (nueva_fecha, id_ventanilla, folio))

        if cursor.rowcount == 0:
            return jsonify({"error": "El ticket ya fue tomado por otro operador"}), 409

        conn.commit()
        
        return jsonify({
            "message": f"Ticket {folio} llamado para atención",
            "folio": folio,
            "tipo": tipo_ticket,
            "matricula": matricula,
            "nombre_alumno": nombre_alumno
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
    tipo_turno = data.get("tipo", "normal")

    if not nuevo_estado:
        return jsonify({"error": "Estado requerido"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        nueva_fecha = obtener_fecha_actual()
        if tipo_turno == "invitado":
            # Actualizar turno invitado
            cursor.execute("""
                UPDATE Turno_Invitado
                SET ID_Estados = %s, Fecha_Ultimo_Estado = %s
                WHERE ID_TurnoInvitado = %s
            """, (nuevo_estado, nueva_fecha, id_turno))
        else:
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
        
        # PRIMERO: Verificar si hay datos en AMBAS tablas
        cursor.execute("""
            SELECT COUNT(*) as total_tickets 
            FROM Turno 
            WHERE ID_Sector = %s AND ID_Estados = 3
        """, (id_sector,))
        total_tickets_normales = cursor.fetchone()["total_tickets"]
        
        cursor.execute("""
            SELECT COUNT(*) as total_tickets 
            FROM Turno_Invitado 
            WHERE ID_Sector = %s AND ID_Estados = 3
        """, (id_sector,))
        total_tickets_invitados = cursor.fetchone()["total_tickets"]
        
        total_tickets = total_tickets_normales + total_tickets_invitados
        print(f"📊 Total de tickets completados en sector {sector_nombre}: {total_tickets} (normales: {total_tickets_normales}, invitados: {total_tickets_invitados})")
        
        # 1. Calcular el tiempo promedio COMBINADO de ambas tablas
        print("📊 Consultando tiempos históricos COMBINADOS...")
        cursor.execute("""
            (
                -- TURNOS NORMALES completados
                SELECT 
                    TIMESTAMPDIFF(SECOND, t.Fecha_Ticket, t.Fecha_Ultimo_Estado) as segundos,
                    'normal' as tipo
                FROM Turno t
                WHERE t.ID_Estados = 3
                AND t.ID_Sector = %s
                AND t.Fecha_Ticket >= DATE_SUB(NOW(), INTERVAL 2 HOUR)
                AND t.Fecha_Ultimo_Estado > t.Fecha_Ticket
                AND TIMESTAMPDIFF(SECOND, t.Fecha_Ticket, t.Fecha_Ultimo_Estado) > 0
            )
            UNION ALL
            (
                -- TURNOS INVITADOS completados
                SELECT 
                    TIMESTAMPDIFF(SECOND, ti.Fecha_Ticket, ti.Fecha_Ultimo_Estado) as segundos,
                    'invitado' as tipo
                FROM Turno_Invitado ti
                WHERE ti.ID_Estados = 3
                AND ti.ID_Sector = %s
                AND ti.Fecha_Ticket >= DATE_SUB(NOW(), INTERVAL 2 HOUR)
                AND ti.Fecha_Ultimo_Estado > ti.Fecha_Ticket
                AND TIMESTAMPDIFF(SECOND, ti.Fecha_Ticket, ti.Fecha_Ultimo_Estado) > 0
            )
        """, (id_sector, id_sector))
        
        tiempos = cursor.fetchall()
        
        # Calcular promedio manualmente
        if tiempos:
            total_segundos = sum(t['segundos'] for t in tiempos)
            promedio_segundos = total_segundos / len(tiempos)
            total_tickets_historial = len(tiempos)
            print(f"📈 Resultado consulta 2 horas: {promedio_segundos:.1f} segundos (de {total_tickets_historial} tickets)")
        else:
            promedio_segundos = None
            total_tickets_historial = 0
            print("📈 No hay datos en las últimas 2 horas")
        
        # Si no hay datos recientes, intentar con rango más amplio
        if not tiempos:
            print("🕐 Consultando todos los tickets completados...")
            cursor.execute("""
                (
                    SELECT 
                        TIMESTAMPDIFF(SECOND, t.Fecha_Ticket, t.Fecha_Ultimo_Estado) as segundos
                    FROM Turno t
                    WHERE t.ID_Estados = 3
                    AND t.ID_Sector = %s
                    AND t.Fecha_Ultimo_Estado > t.Fecha_Ticket
                    AND TIMESTAMPDIFF(SECOND, t.Fecha_Ticket, t.Fecha_Ultimo_Estado) > 0
                )
                UNION ALL
                (
                    SELECT 
                        TIMESTAMPDIFF(SECOND, ti.Fecha_Ticket, ti.Fecha_Ultimo_Estado) as segundos
                    FROM Turno_Invitado ti
                    WHERE ti.ID_Estados = 3
                    AND ti.ID_Sector = %s
                    AND ti.Fecha_Ultimo_Estado > ti.Fecha_Ticket
                    AND TIMESTAMPDIFF(SECOND, ti.Fecha_Ticket, ti.Fecha_Ultimo_Estado) > 0
                )
            """, (id_sector, id_sector))
            
            tiempos = cursor.fetchall()
            if tiempos:
                total_segundos = sum(t['segundos'] for t in tiempos)
                promedio_segundos = total_segundos / len(tiempos)
                total_tickets_historial = len(tiempos)
                print(f"📈 Resultado consulta completa: {promedio_segundos:.1f} segundos (de {total_tickets_historial} tickets)")
        
        # 2. Contar tickets pendientes por delante en AMBAS tablas
        cursor.execute("""
            SELECT COUNT(*) as tickets_pendientes
            FROM Turno t
            WHERE t.ID_Sector = %s 
            AND t.ID_Estados = 1
        """, (id_sector,))
        pendientes_normales = cursor.fetchone()["tickets_pendientes"]
        
        cursor.execute("""
            SELECT COUNT(*) as tickets_pendientes
            FROM Turno_Invitado ti
            WHERE ti.ID_Sector = %s 
            AND ti.ID_Estados = 1
        """, (id_sector,))
        pendientes_invitados = cursor.fetchone()["tickets_pendientes"]
        
        tickets_pendientes = pendientes_normales + pendientes_invitados
        print(f"🎫 Tickets pendientes en sector {sector_nombre}: {tickets_pendientes} (normales: {pendientes_normales}, invitados: {pendientes_invitados})")
        
        # 3. Determinar el tiempo estimado base
        if promedio_segundos and total_tickets_historial > 0:
            tiempo_base = promedio_segundos / 60  # Convertir a minutos
            print(f"⏱️  Tiempo base calculado: {tiempo_base:.1f} minutos (de {total_tickets_historial} tickets combinados)")
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
            (
                -- TURNOS NORMALES
                SELECT 
                    t.Folio AS folio,
                    t.ID_Turno AS id_turno,
                    a.Matricula AS matricula,
                    CONCAT(a.nombre1, ' ', a.Apellido1) AS nombre_completo,
                    s.Sector AS sector,
                    et.Nombre AS estado,
                    t.Fecha_Ticket AS fecha_ticket,
                    t.Fecha_Ultimo_Estado AS fecha_ultimo_estado,
                    'normal' AS tipo
                FROM Turno t
                JOIN Alumnos a ON t.ID_Alumno = a.ID_Alumno
                JOIN Sectores s ON t.ID_Sector = s.ID_Sector
                JOIN Estados_Turno et ON t.ID_Estados = et.ID_Estado
            )
            UNION ALL
            (
                -- TURNOS INVITADOS
                SELECT 
                    ti.Folio_Invitado AS folio,
                    ti.ID_TurnoInvitado AS id_turno,
                    NULL AS matricula,
                    'Invitado' AS nombre_completo,
                    s.Sector AS sector,
                    et.Nombre AS estado,
                    ti.Fecha_Ticket AS fecha_ticket,
                    ti.Fecha_Ultimo_Estado AS fecha_ultimo_estado,
                    'invitado' AS tipo
                FROM Turno_Invitado ti
                JOIN Sectores s ON ti.ID_Sector = s.ID_Sector
                JOIN Estados_Turno et ON ti.ID_Estados = et.ID_Estado
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
        
        # Turnos invitados
        cursor.execute("""
            SELECT 
                ti.Folio_Invitado AS folio,
                ti.ID_TurnoInvitado AS id_turno,
                ti.ID_Ventanilla AS id_ventanilla,
                v.Ventanilla AS ventanilla,
                NULL AS matricula,
                'Invitado' AS nombre_alumno,
                s.Sector AS sector,
                et.Nombre AS estado,
                et.ID_Estado AS estado_id,
                ti.Fecha_Ticket AS fecha_ticket,
                'invitado' AS tipo
            FROM Turno_Invitado ti
            JOIN Sectores s ON ti.ID_Sector = s.ID_Sector
            JOIN Estados_Turno et ON ti.ID_Estados = et.ID_Estado
            LEFT JOIN Ventanillas v ON ti.ID_Ventanilla = v.ID_Ventanilla
            WHERE ti.ID_Estados IN (1, 3)
        """)
        tickets_invitados = cursor.fetchall()
        
        # Combinar y ordenar
        todos_tickets = tickets_normales + tickets_invitados
        todos_tickets.sort(key=lambda x: (x['estado_id'] != 3, x['fecha_ticket']))
        return jsonify(todos_tickets), 200
        
    except Exception as e:
        print(f"Error en get_tickets_publico: {e}")
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()