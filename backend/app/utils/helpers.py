from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, String, Integer
from app.models.models import Sector, Turno
import pytz
import subprocess
import os
import uuid
import threading

async def get_sector_prefix(sector_nombre: str, db: AsyncSession) -> str:
    """Genera un prefijo único para el sector basándose en su nombre.
    Consulta todos los sectores en orden de creación (ID) y asigna
    prefijos determinísticamente para evitar colisiones.
    
    Args:
        sector_nombre (str): Nombre del sector.
        db (AsyncSession): Sesión de base de datos.
        
    Returns:
        str: Prefijo generado para el sector.
    """
    result = await db.execute(select(Sector.Sector).order_by(Sector.ID_Sector))
    sectores = [row[0] for row in result.fetchall()]

    asignados = {}
    for nombre in sectores:
        asignados[nombre] = _gen_prefix(nombre, set(asignados.values()))

    return asignados.get(sector_nombre, "X")


def _gen_prefix(nombre: str, usados: set) -> str:
    """Genera un prefijo único para un sector dado los ya usados.
    
    Args:
        nombre (str): Nombre del sector.
        usados (set): Conjunto de prefijos ya utilizados.
        
    Returns:
        str: Prefijo único generado.
    """
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

async def generar_folio_unico(sector_nombre: str, db: AsyncSession) -> str:
    """Genera un folio único para un turno basado en el sector y la fecha.
    
    Args:
        sector_nombre (str): Nombre del sector.
        db (AsyncSession): Sesión de base de datos.
        
    Returns:
        str: Folio único generado.
    """
    prefix = await get_sector_prefix(sector_nombre, db)
    prefix_len = len(prefix)
    
    # Obtener la fecha actual en zona horaria de México
    tz_mexico = pytz.timezone('America/Mexico_City')
    hoy = datetime.now(tz_mexico).strftime('%Y-%m-%d')
        
    result = await db.execute(
        select(func.max(cast(func.substring(Turno.Folio, prefix_len + 1), Integer)))
        .where(
            Turno.Folio.like(f"{prefix}%"),
            func.date(Turno.Fecha_Ticket) == hoy
        )
    )
    
    row = result.fetchone()
    max_num = max(row[0], 9) if row and row[0] is not None else 9
    
    folio = f"{prefix}{max_num + 1}"
    return folio

def obtener_fecha_actual() -> str:
    """Obtiene la fecha y hora actual en la zona horaria de México (con milisegundos).
    
    Returns:
        str: Fecha y hora actual formateada.
    """
    tz_mexico = pytz.timezone('America/Mexico_City')
    return datetime.now(tz_mexico).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

def obtener_fecha_publico() -> str:
    """Obtiene la fecha y hora actual en la zona horaria de México (sin milisegundos).
    
    Returns:
        str: Fecha y hora actual formateada.
    """
    tz_mexico = pytz.timezone('America/Mexico_City')
    return datetime.now(tz_mexico).strftime("%Y-%m-%d %H:%M:%S")

AUDIO_DIR = "/app/audio"

def _cleanup_audio(filepath: str, delay: int = 120) -> None:
    """Elimina un archivo de audio después de un delay en segundos.
    
    Args:
        filepath (str): Ruta del archivo a eliminar.
        delay (int, opcional): Tiempo de espera en segundos. Por defecto 120.
    """
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

def speak_to_file(text: str) -> str:
    """Genera un archivo de audio a partir de texto y retorna su nombre.
    Utiliza gTTS, con fallback a espeak en caso de error.
    
    Args:
        text (str): Texto a convertir en audio.
        
    Returns:
        str: Nombre del archivo de audio generado.
    """
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

    # Programar eliminación automática del archivo en 120 segundos
    _cleanup_audio(filepath)

    return filename