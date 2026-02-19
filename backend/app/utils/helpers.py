import random
import string
from datetime import datetime
from app.models.database import get_db_connection
from functools import wraps
from flask import session, jsonify
import pytz
import qrcode
import uuid
from datetime import datetime, timedelta
import os
import threading

def get_sector_prefix_and_length(sector_nombre):
    """Mapea el nombre del sector a su prefijo y la longitud de la parte aleatoria."""
    # Los prefijos de ejemplo son 'C', 'B' y 'SE'.
    # La longitud total del folio será 6 caracteres.
    if sector_nombre == "Cajas":
        return "C", 5 # C (1 char) + 5 random chars = 6 total
    elif sector_nombre == "Becas":
        return "B", 5 # B (1 char) + 5 random chars = 6 total
    elif sector_nombre == "Servicios Escolares":
        return "SE", 4 # SE (2 chars) + 4 random chars = 6 total
    elif sector_nombre == "Tesoreria":
        return "T"  , 5 # T (1 char) + 5 random chars = 6 total
    else:
        # Valor por defecto si el sector no coincide.
        return "", 6

def generar_folio_unico(sector_nombre):
    estados_activos = (1, 3)
    # Obtener el prefijo y cuántos caracteres aleatorios generar
    prefix, random_part_length = get_sector_prefix_and_length(sector_nombre)
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        while True:
            # Generar la parte aleatoria
            # Se usa string.ascii_uppercase + string.digits para alfanumérico
            random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=random_part_length))
            
            # Crear el folio completo de 6 caracteres
            folio = prefix + random_part
            
            # Verificar unicidad en la base de datos
            placeholders = ','.join(['%s'] * len(estados_activos))
            query_normal = f"""
                SELECT 1 FROM Turno 
                WHERE Folio = %s AND ID_Estados IN ({placeholders})
            """
            cursor.execute(query_normal, (folio, *estados_activos))
            
            if cursor.fetchone():
                continue  # Folio ya existe en Turno, generar otro
            if not cursor.fetchone():
                return folio
    finally:
        cursor.close()
        conn.close()

def obtener_fecha_actual():
    tz_mexico = pytz.timezone('America/Mexico_City')
    return datetime.now(tz_mexico).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

def obtener_fecha_publico():
    tz_mexico = pytz.timezone('America/Mexico_City')
    return datetime.now(tz_mexico).strftime("%Y-%m-%d %H:%M:%S")

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "No autenticado"}), 401
        return f(*args, **kwargs)
    return decorated

API_BASE_URL = os.getenv("IP_ADDRESS", "https://localhost:4443")

def programar_eliminacion(*rutas, delay=40):
    """Elimina los archivos indicados después de `delay` segundos."""
    def eliminar():
        for ruta in rutas:
            try:
                if os.path.exists(ruta):
                    os.remove(ruta)
                    print(f"Archivo eliminado: {ruta}")
            except Exception as e:
                print(f"Error al eliminar {ruta}: {e}")
    threading.Timer(delay, eliminar).start()

def generar_qr_ticket(nombre_archivo):
    # Asegurar que el directorio static/qrs existe
    static_folder = os.path.join(os.getcwd(), "app", "static", "qrs")
    os.makedirs(static_folder, exist_ok=True)

    # URL pública CORRECTA
    url = f"{API_BASE_URL}/api/ticket/{nombre_archivo}"
    
    img = qrcode.make(url)
    
    # Nombre del archivo QR
    qr_filename = f"qr_{nombre_archivo.replace('.pdf', '')}.png"
    ruta_completa = os.path.join(static_folder, qr_filename)
    
    img.save(ruta_completa)

    # Programar eliminación del QR y del PDF después de 40s
    ruta_pdf = os.path.join(os.getcwd(), "tickets", nombre_archivo)
    programar_eliminacion(ruta_completa, ruta_pdf, delay=40)

    return ruta_completa

tokens = {}

def crear_token(nombre_archivo):
    token = uuid.uuid4().hex
    tokens[token] = {
        "archivo": nombre_archivo,
        "expira": datetime.now() + timedelta(seconds=40)
    }
    return token