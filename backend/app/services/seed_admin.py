"""
Utilidad de verificación del administrador.

Provee funciones auxiliares para validar la existencia
de un administrador (rol 1) en la base de datos.
"""

from sqlalchemy import select

from app.models.database import async_session_local
from app.models.models import Empleado

TEMPORAL_MARKER = "__TEMPORAL__"


async def admin_exists() -> bool:
    """Retorna True si existe al menos un empleado con rol Admin (1)."""
    async with async_session_local() as session:
        result = await session.execute(
            select(Empleado.ID_Empleado).where(Empleado.ID_ROL == 1).limit(1)
        )
        return result.fetchone() is not None


async def admin_is_temporal() -> bool:
    """Retorna True si el admin existente aún tiene el marcador temporal."""
    async with async_session_local() as session:
        result = await session.execute(
            select(Empleado.nombre2).where(Empleado.ID_ROL == 1).limit(1)
        )
        row = result.fetchone()
        if not row:
            return False
        return row[0] == TEMPORAL_MARKER
