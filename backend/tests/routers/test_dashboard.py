import pytest

@pytest.mark.asyncio
async def test_get_dashboard_stats_no_token(client):
    response = await client.get("/api/dashboard/stats")
    assert response.status_code == 401
    assert response.json()["detail"] == "Token requerido"

@pytest.mark.asyncio
async def test_get_dashboard_stats_invalid_token(client, mock_db_session):
    mock_db_session.execute.return_value.mappings().fetchone.return_value = None
    response = await client.get("/api/dashboard/stats?session_token=invalid")
    assert response.status_code == 401
    assert response.json()["detail"] == "Sesion invalida"
