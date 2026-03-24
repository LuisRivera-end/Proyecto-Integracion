import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models.database import Base, get_db
from app.models.models import Rol, EstadoEmpleado, Empleado, SesionActiva
from app.schemas.auth import LoginRequest

# Override settings for testing
import app.config as config_module
config_module.settings.DATABASE_URL = "sqlite+aiosqlite:///:memory:"
config_module.settings.SESSION_RESET_PIN = "1234"

# Create test engine for SQLite in-memory
SQLALCHEMY_TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)

# Override the get_db dependency
async def override_get_db() -> AsyncSession:
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

app.dependency_overrides[get_db] = override_get_db

# Create async test client
client = AsyncClient(app=app, base_url="http://test")

@pytest.fixture(autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Insert test data
    async with TestingSessionLocal() as session:
        # Create roles
        rol_admin = Rol(ID_Rol=1, Rol="Admin")
        rol_jefe = Rol(ID_Rol=6, Rol="Jefe")
        rol_operador = Rol(ID_Rol=2, Rol="Operador")
        session.add_all([rol_admin, rol_jefe, rol_operador])
        
        # Create employee states
        estado_activo = EstadoEmpleado(ID_Estado=1, Nombre="Activo")
        estado_inactivo = EstadoEmpleado(ID_Estado=2, Nombre="Inactivo")
        session.add_all([estado_activo, estado_inactivo])
        
        # Create a sector
        sector = Sector(ID_Sector=1, Sector="Control Escolar")
        session.add(sector)
        
        # Create an admin employee
        admin_empleado = Empleado(
            ID_Empleado=1,
            ID_ROL=1,
            nombre1="Admin",
            nombre2="",
            Apellido1="User",
            Apellido2="",
            Usuario="admin",
            Passwd="",  # placeholder
            ID_Estado=1,
            ID_Sector=1
        )
        session.add(admin_empleado)
        
        await session.commit()
    yield
    # Clean up
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

async def hash_password(password: str) -> str:
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

async def update_password(username: str, password: str):
    hashed = await hash_password(password)
    async with TestingSessionLocal() as session:
        from sqlalchemy import update
        await session.execute(
            update(Empleado)
            .where(Empleado.Usuario == username)
            .values(Passwd=hashed)
        )
        await session.commit()

@pytest.mark.asyncio
async def test_login_success(setup_database):
    await update_password("admin", "admin123")
    
    response = await client.post(
        "/api/login",
        json={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_token" in data
    assert data["id"] == 1
    assert data["rol"] == 1
    assert data["nombre"] == "Admin User"
    return data["session_token"]

@pytest.mark.asyncio
async def test_login_wrong_password(setup_database):
    await update_password("admin", "admin123")
    
    response = await client.post(
        "/api/login",
        json={"username": "admin", "password": "wrong"}
    )
    assert response.status_code == 401
    assert "Contraseña incorrecta" in response.json()["detail"]

@pytest.mark.asyncio
async def test_login_user_not_found(setup_database):
    response = await client.post(
        "/api/login",
        json={"username": "nonexistent", "password": "any"}
    )
    assert response.status_code == 404
    assert "Usuario no existe" in response.json()["detail"]

@pytest.mark.asyncio
async def test_login_inactive_user(setup_database):
    async def setup_inactive_user():
        async with TestingSessionLocal() as session:
            from sqlalchemy import update
            await session.execute(
                update(Empleado)
                .where(Empleado.Usuario == "admin")
                .values(ID_Estado=2)  # Inactivo
            )
            await session.commit()
    await setup_inactive_user()
    
    await update_password("admin", "admin123")
    
    response = await client.post(
        "/api/login",
        json={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 403
    assert "Usuario no activo" in response.json()["detail"]

@pytest.mark.asyncio
async def test_check_session_valid(setup_database):
    # First login to get a token
    token = await test_login_success(setup_database)
    
    response = await client.post(
        "/api/check_session",
        json={"session_token": token}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["user_id"] == 1
    assert data["rol"] == 1

@pytest.mark.asyncio
async def test_check_session_invalid_token(setup_database):
    response = await client.post(
        "/api/check_session",
        json={"session_token": "invalid_token"}
    )
    assert response.status_code == 401
    assert "No session" in response.json()["detail"]

@pytest.mark.asyncio
async def test_logout(setup_database):
    token = await test_login_success(setup_database)
    
    response = await client.post(
        "/api/logout",
        json={"session_token": token}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Sesión cerrada"
    
    # Verify session is now invalid
    response = await client.post(
        "/api/check_session",
        json={"session_token": token}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_force_close_session(setup_database):
    # Create two employees: admin and operator
    async def setup_employees():
        async with TestingSessionLocal() as session:
            # Operator role
            rol_operador = Rol(ID_Rol=2, Rol="Operador")
            session.add(rol_operador)
            
            # Operator employee
            operador = Empleado(
                ID_Empleado=2,
                ID_ROL=2,
                nombre1="Oper",
                nombre2="",
                Apellido1="User",
                Apellido2="",
                Usuario="operador",
                Passwd="",  # placeholder
                ID_Estado=1,
                ID_Sector=1
            )
            session.add(operador)
            await session.commit()
    await setup_employees()
    
    # Login as admin to get token
    async def update_admin_password():
        await update_password("admin", "admin123")
    await update_admin_password()
    
    admin_token = await test_login_success(setup_database)
    
    # Login as operator to get a session
    async def update_operator_password():
        await update_password("operador", "operador123")
    await update_operator_password()
    
    # We need to login as operator to create a session
    op_response = await client.post(
        "/api/login",
        json={"username": "operador", "password": "operador123"}
    )
    assert op_response.status_code == 200
    op_token = op_response.json()["session_token"]
    
    # Now force close the operator's session as admin
    response = await client.post(
        f"/api/employees/2/forzar-cierre",
        json={"session_token": admin_token}
    )
    assert response.status_code == 200
    assert "Sesión forzada a cerrar" in response.json()["message"]
    
    # Verify operator's session is now invalid
    response = await client.post(
        "/api/check_session",
        json={"session_token": op_token}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_emergency_validate_pin(setup_database):
    response = await client.post(
        "/api/emergency/validate-pin",
        json={"pin": "1234"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "emergency_token" in response.json()
    
    # Wrong PIN
    response = await client.post(
        "/api/emergency/validate-pin",
        json={"pin": "0000"}
    )
    assert response.status_code == 403
    assert "PIN incorrecto" in response.json()["detail"]

@pytest.mark.asyncio
async def test_emergency_reset_sessions(setup_database):
    # First create a session
    async def setup_session():
        await update_password("admin", "admin123")
    await setup_session()
    
    login_response = await client.post(
        "/api/login",
        json={"username": "admin", "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["session_token"]
    
    # Validate emergency token
    emergency_response = await client.post(
        "/api/emergency/validate-pin",
        json={"pin": "1234"}
    )
    assert emergency_response.status_code == 200
    emergency_token = emergency_response.json()["emergency_token"]
    
    # Reset sessions
    reset_response = await client.post(
        "/api/emergency/reset-sessions",
        json={"emergency_token": emergency_token}
    )
    assert reset_response.status_code == 200
    assert "Todas las sesiones han sido reiniciadas" in reset_response.json()["message"]
    
    # Verify the original session is now invalid
    response = await client.post(
        "/api/check_session",
        json={"session_token": token}
    )
    assert response.status_code == 401