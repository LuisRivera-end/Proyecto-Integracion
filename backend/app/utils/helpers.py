import random
import string
from datetime import datetime
from app.models.database import get_db_connection

def generar_folio_unico():
    estados_activos = (1, 3)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        while True:
            folio = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            
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