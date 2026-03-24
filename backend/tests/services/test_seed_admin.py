"""
Tests for the setup endpoints and admin seed utility.
"""

import pytest
import pytest_asyncio
from hashlib import sha256

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import select, insert
from unittest.mock import patch
from datetime import datetime, timedelta

from app.models.database import Base
from app.models.models import Empleado, Rol, EstadoEmpleado, SesionActiva
from app.services.seed_admin import TEMPORAL_MARKER


SQLALCHEMY_TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create tables and seed base catalog data for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        session.add(Rol(ID_Rol=1, Rol="Admin"))
        session.add(Rol(ID_Rol=2, Rol="Operador"))
        session.add(EstadoEmpleado(ID_Estado=1, Nombre="Activo"))
        await session.commit()

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ── Utility tests ──

@pytest.mark.asyncio
async def test_admin_exists_returns_false_when_no_admin(setup_database):
    """admin_exists() returns False when no admin in DB."""
    with patch("app.services.seed_admin.async_session_local", TestingSessionLocal):
        from app.services.seed_admin import admin_exists
        result = await admin_exists()
    assert result is False


@pytest.mark.asyncio
async def test_admin_exists_returns_true_when_admin_present(setup_database):
    """admin_exists() returns True when admin exists."""
    async with TestingSessionLocal() as session:
        session.add(Empleado(
            ID_ROL=1, nombre1="Admin", nombre2="", Apellido1="Test",
            Apellido2="", Usuario="admin", Passwd=sha256(b"test").hexdigest(), ID_Estado=1,
        ))
        await session.commit()

    with patch("app.services.seed_admin.async_session_local", TestingSessionLocal):
        from app.services.seed_admin import admin_exists
        result = await admin_exists()
    assert result is True


@pytest.mark.asyncio
async def test_admin_is_temporal_true(setup_database):
    """admin_is_temporal() returns True when admin has temporal marker."""
    async with TestingSessionLocal() as session:
        session.add(Empleado(
            ID_ROL=1, nombre1="Admin", nombre2=TEMPORAL_MARKER, Apellido1="Temporal",
            Apellido2="", Usuario="admin_temp", Passwd=sha256(b"test").hexdigest(), ID_Estado=1,
        ))
        await session.commit()

    with patch("app.services.seed_admin.async_session_local", TestingSessionLocal):
        from app.services.seed_admin import admin_is_temporal
        result = await admin_is_temporal()
    assert result is True


@pytest.mark.asyncio
async def test_admin_is_temporal_false_when_configured(setup_database):
    """admin_is_temporal() returns False when admin has real data."""
    async with TestingSessionLocal() as session:
        session.add(Empleado(
            ID_ROL=1, nombre1="Luis", nombre2="", Apellido1="Rivera",
            Apellido2="", Usuario="admin", Passwd=sha256(b"test").hexdigest(), ID_Estado=1,
        ))
        await session.commit()

    with patch("app.services.seed_admin.async_session_local", TestingSessionLocal):
        from app.services.seed_admin import admin_is_temporal
        result = await admin_is_temporal()
    assert result is False


# ── Router tests (via HTTPX) ──

from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.database import get_db


async def override_get_db():
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db

transport = ASGITransport(app=app)
client = AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_status_needs_setup_true(setup_database):
    """GET /api/setup/status returns needs_setup=true when no admin."""
    response = await client.get("/api/setup/status")
    assert response.status_code == 200
    assert response.json()["needs_setup"] is True


@pytest.mark.asyncio
async def test_status_needs_setup_false(setup_database):
    """GET /api/setup/status returns needs_setup=false when admin exists."""
    async with TestingSessionLocal() as session:
        session.add(Empleado(
            ID_ROL=1, nombre1="Admin", nombre2="", Apellido1="Test",
            Apellido2="", Usuario="admin", Passwd=sha256(b"test").hexdigest(), ID_Estado=1,
        ))
        await session.commit()

    response = await client.get("/api/setup/status")
    assert response.status_code == 200
    assert response.json()["needs_setup"] is False


@pytest.mark.asyncio
async def test_init_creates_temporal_admin(setup_database):
    """POST /api/setup/init creates a temporal admin and returns credentials."""
    response = await client.post("/api/setup/init")
    assert response.status_code == 201
    data = response.json()
    assert "usuario" in data
    assert "password" in data
    assert len(data["password"]) >= 12

    # Verify in DB
    async with TestingSessionLocal() as session:
        result = await session.execute(
            select(Empleado).where(Empleado.ID_ROL == 1)
        )
        admin = result.scalars().first()
    assert admin is not None
    assert admin.Usuario == data["usuario"]
    assert admin.nombre2 == TEMPORAL_MARKER


@pytest.mark.asyncio
async def test_init_fails_when_admin_exists(setup_database):
    """POST /api/setup/init fails with 409 when admin already exists."""
    async with TestingSessionLocal() as session:
        session.add(Empleado(
            ID_ROL=1, nombre1="Admin", nombre2="", Apellido1="Test",
            Apellido2="", Usuario="admin", Passwd=sha256(b"test").hexdigest(), ID_Estado=1,
        ))
        await session.commit()

    response = await client.post("/api/setup/init")
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_finalize_updates_admin(setup_database):
    """POST /api/setup/finalize updates temporal admin with real data."""
    # 1. Create temporal admin via init
    init_res = await client.post("/api/setup/init")
    assert init_res.status_code == 201
    creds = init_res.json()

    # 2. Login with those creds
    login_res = await client.post("/api/login", json={
        "username": creds["usuario"],
        "password": creds["password"],
    })
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["needs_setup"] is True
    token = login_data["session_token"]

    # 3. Finalize
    finalize_res = await client.post("/api/setup/finalize", json={
        "session_token": token,
        "nombre1": "Luis",
        "nombre2": "",
        "apellido1": "Rivera",
        "apellido2": "",
        "usuario": "admin_real",
        "passwd": "nueva_password_segura",
    })
    assert finalize_res.status_code == 200

    # 4. Verify admin is updated
    async with TestingSessionLocal() as session:
        result = await session.execute(
            select(Empleado).where(Empleado.ID_ROL == 1)
        )
        admin = result.scalars().first()
    assert admin is not None
    assert admin.Usuario == "admin_real"
    assert admin.nombre1 == "Luis"
    assert admin.nombre2 != TEMPORAL_MARKER
    assert admin.Passwd == sha256(b"nueva_password_segura").hexdigest()
