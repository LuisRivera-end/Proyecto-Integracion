from datetime import datetime
from app.models.database import get_db_connection
from functools import wraps
from flask import session, jsonify
import pytz
import subprocess
import os
import uuid
import threading

def get_sector_prefix(sector_nombre):
    """Genera un prefijo único para el sector basándose en su nombre.
    Consulta todos los sectores en orden de creación (ID) y asigna
    prefijos determinísticamente para evitar colisiones."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT Sector FROM Sectores ORDER BY ID_Sector")
        sectores = [row["Sector"] for row in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()

    asignados = {}
    for nombre in sectores:
        asignados[nombre] = _gen_prefix(nombre, set(asignados.values()))

    return asignados.get(sector_nombre, "X")


def _gen_prefix(nombre, usados):
    """Genera un prefijo único para un sector dado los ya usados."""
    words = nombre.strip().split()
    upper = nombre.upper().replace(" ", "")

    # Multi-palabra: intentar iniciales (ej. "Servicios Escolares" → "SE")
    if len(words) > 1:
        initials = ''.join(w[0].upper() for w in words)
        if initials not in usados:
            return initials

    # Intentar primera letra
    if upper[0] not in usados:
        return upper[0]

    # Intentar primeras 2 letras
    if len(upper) >= 2 and upper[:2] not in usados:
        return upper[:2]

    # Intentar primeras 3 letras
    if len(upper) >= 3 and upper[:3] not in usados:
        return upper[:3]

    # Fallback: primera letra + número
    for i in range(1, 100):
        candidate = f"{upper[0]}{i}"
        if candidate not in usados:
            return candidate

    return "X"

def generar_folio_unico(sector_nombre):
    prefix = get_sector_prefix(sector_nombre)
    prefix_len = len(prefix)
    
    # Obtener la fecha actual en zona horaria de México
    tz_mexico = pytz.timezone('America/Mexico_City')
    hoy = datetime.now(tz_mexico).strftime('%Y-%m-%d')
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Obtener el número máximo de hoy entre los folios de este sector
        cursor.execute("""
            SELECT MAX(CAST(SUBSTRING(Folio, %s + 1) AS UNSIGNED)) AS max_num
            FROM Turno
            WHERE Folio LIKE CONCAT(%s, '%%') AND DATE(Fecha_Ticket) = %s
        """, (prefix_len, prefix, hoy))
        
        result = cursor.fetchone()
        max_num = result[0] if result and result[0] is not None else 0
        
        folio = prefix + str(max_num + 1)
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

AUDIO_DIR = "/app/audio"

def _cleanup_audio(filepath, delay=120):
    """Elimina un archivo de audio después de un delay en segundos."""
    def _delete():
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"🗑️ Audio eliminado: {filepath}")
        except OSError as e:
            print(f"⚠️ Error al eliminar audio {filepath}: {e}")
    timer = threading.Timer(delay, _delete)
    timer.daemon = True
    timer.start()

def speak_to_file(text):
    os.makedirs(AUDIO_DIR, exist_ok=True)

    filename = f"turno_{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)

    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang='es', slow=False)
        tts.save(filepath)
    except Exception as e:
        print(f"⚠️ gTTS falló ({e}), usando espeak como fallback")
        filename = f"turno_{uuid.uuid4().hex}.wav"
        filepath = os.path.join(AUDIO_DIR, filename)
        subprocess.run([
            "espeak", "-v", "es", "-w", filepath, text
        ], check=True)

    # Programar eliminación automática del archivo en 30 segundos
    _cleanup_audio(filepath)

    return filename