"""
Router de configuración inicial (setup).

Gestiona la creación del administrador temporal y la finalización
de la configuración con datos reales. Todos los endpoints están
protegidos: solo funcionan cuando no existe un admin o cuando el
admin aún es temporal.
"""

import secrets
import string
from hashlib import sha256
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, update, insert, and_

from app.models.database import get_db
from app.models.models import Empleado, SesionActiva
from app.schemas.setup import SetupStatusResponse, SetupInitResponse, SetupFinalizeRequest
from app.services.seed_admin import TEMPORAL_MARKER

router = APIRouter(prefix="/api/setup", tags=["Setup Inicial"])


def _generate_random_string(length: int, charset: str) -> str:
    """Genera una cadena aleatoria segura."""
    return "".join(secrets.choice(charset) for _ in range(length))


def _generate_credentials() -> tuple[str, str]:
    """Genera un usuario y contraseña aleatorios para el admin temporal."""
    username_charset = string.ascii_lowercase + string.digits
    password_charset = string.ascii_letters + string.digits
    usuario = "admin_" + _generate_random_string(6, username_charset)
    password = _generate_random_string(12, password_charset)
    return usuario, password


@router.get("/status", response_model=SetupStatusResponse)
async def get_setup_status(db: AsyncSession = Depends(get_db)):
    """Retorna si el sistema necesita configuración inicial (no hay admin)."""
    result = await db.execute(
        select(Empleado.ID_Empleado).where(Empleado.ID_ROL == 1).limit(1)
    )
    admin = result.fetchone()
    return {"needs_setup": admin is None}


@router.post("/init", response_model=SetupInitResponse, status_code=201)
async def init_admin(db: AsyncSession = Depends(get_db)):
    """Crea un administrador temporal con credenciales aleatorias.

    Solo funciona si no existe ningún empleado con rol Admin (1).
    Retorna las credenciales en texto plano para que el usuario las anote.
    """
    # Guard: verificar que no exista admin
    result = await db.execute(
        select(Empleado.ID_Empleado).where(Empleado.ID_ROL == 1).limit(1)
    )
    if result.fetchone():
        raise HTTPException(
            status_code=409,
            detail="Ya existe un administrador. La configuración inicial ya fue completada."
        )

    usuario, password = _generate_credentials()
    passwd_hash = sha256(password.encode()).hexdigest()

    try:
        await db.execute(
            insert(Empleado).values(
                ID_ROL=1,
                nombre1="Admin",
                nombre2=TEMPORAL_MARKER,
                Apellido1="Temporal",
                Apellido2="",
                Usuario=usuario,
                Passwd=passwd_hash,
                ID_Estado=1,
            )
        )
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Error al crear el administrador temporal.")

    return {
        "usuario": usuario,
        "password": password,
        "message": "Administrador temporal creado. Anote las credenciales, no se mostrarán de nuevo.",
    }


@router.post("/finalize")
async def finalize_admin(data: SetupFinalizeRequest, db: AsyncSession = Depends(get_db)):
    """Actualiza el administrador temporal con los datos reales.

    Requiere un session_token válido de un administrador que tenga
    el marcador temporal (__TEMPORAL__).
    """
    # 1. Validar sesión
    result = await db.execute(
        select(SesionActiva.ID_Empleado, SesionActiva.Expira)
        .where(and_(SesionActiva.Token == data.session_token, SesionActiva.Activa == True))
    )
    session_row = result.fetchone()

    if not session_row:
        raise HTTPException(status_code=401, detail="Sesión inválida o expirada.")

    if session_row[1] < datetime.utcnow():
        await db.execute(
            update(SesionActiva)
            .where(SesionActiva.Token == data.session_token)
            .values(Activa=False)
        )
        await db.commit()
        raise HTTPException(status_code=401, detail="Sesión expirada.")

    employee_id: int = session_row[0]

    # 2. Verificar que el empleado es admin temporal
    result = await db.execute(
        select(Empleado.ID_ROL, Empleado.nombre2)
        .where(Empleado.ID_Empleado == employee_id)
    )
    emp_row = result.fetchone()

    if not emp_row or emp_row[0] != 1:
        raise HTTPException(status_code=403, detail="Solo un administrador puede finalizar la configuración.")

    if emp_row[1] != TEMPORAL_MARKER:
        raise HTTPException(status_code=409, detail="El administrador ya fue configurado.")

    # 3. Verificar que el nuevo usuario no esté en uso por otro empleado
    dup_result = await db.execute(
        select(Empleado.ID_Empleado)
        .where(and_(Empleado.Usuario == data.usuario, Empleado.ID_Empleado != employee_id))
        .limit(1)
    )
    if dup_result.fetchone():
        raise HTTPException(status_code=409, detail="El nombre de usuario ya está en uso.")

    # 4. Actualizar admin con datos reales
    passwd_hash = sha256(data.passwd.encode()).hexdigest()

    try:
        await db.execute(
            update(Empleado)
            .where(Empleado.ID_Empleado == employee_id)
            .values(
                nombre1=data.nombre1,
                nombre2=data.nombre2,
                Apellido1=data.apellido1,
                Apellido2=data.apellido2,
                Usuario=data.usuario,
                Passwd=passwd_hash,
            )
        )

        # Extender la sesión del admin
        await db.execute(
            update(SesionActiva)
            .where(SesionActiva.Token == data.session_token)
            .values(Expira=datetime.utcnow() + timedelta(minutes=5))
        )

        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Error al actualizar el administrador.")

    return {"message": "Administrador configurado correctamente."}
