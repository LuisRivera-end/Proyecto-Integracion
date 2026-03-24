import pytest

@pytest.mark.asyncio
async def test_get_employees(client, mock_db_session):
    mock_db_session.execute.return_value.mappings().fetchall.return_value = [
        {"id": 1, "rol_id": 1, "name": "Test User", "rol": "Admin", "estado": "Activo"}
    ]
    response = await client.get("/api/employees")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Test User"

@pytest.mark.asyncio
async def test_add_employee_missing_fields(client):
    response = await client.post("/api/employees/add", json={"nombre1": "Test"})
    assert response.status_code == 422 # Pydantic validation error

@pytest.mark.asyncio
async def test_check_user_exists(client, mock_db_session):
    mock_db_session.execute.return_value.fetchone.return_value = (1,)
    response = await client.get("/api/employees/exists/admin")
    assert response.status_code == 200
    assert response.json() == {"exists": True}

    mock_db_session.execute.return_value.fetchone.return_value = None
    response = await client.get("/api/employees/exists/not_found")
    assert response.status_code == 200
    assert response.json() == {"exists": False}
