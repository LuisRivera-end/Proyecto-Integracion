import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.database import get_db
from unittest.mock import AsyncMock

@pytest.fixture
def mock_db_session():
    mock_session = AsyncMock()
    return mock_session

@pytest.fixture
def override_get_db(mock_db_session):
    async def _override_get_db():
        yield mock_db_session
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()

@pytest.fixture
async def client(override_get_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
