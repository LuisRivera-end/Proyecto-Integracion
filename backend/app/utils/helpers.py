import random
import string
from datetime import datetime
from app.models.database import get_db_connection
from functools import wraps
from flask import session, jsonify

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
            query = f"""
                SELECT 1 FROM Turno 
                WHERE Folio = %s AND ID_Estados IN ({placeholders})
            """
            cursor.execute(query, (folio, *estados_activos))

            if not cursor.fetchone():
                return folio
    finally:
        cursor.close()
        conn.close()

def obtener_fecha_actual():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

def obtener_fecha_publico():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "No autenticado"}), 401
        return f(*args, **kwargs)
    return decorated