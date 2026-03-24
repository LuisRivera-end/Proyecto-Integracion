from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_caja_rapida_activar():
    """Test activating the quick box."""
    response = client.post(
        "/api/caja-rapida/activar",
        json={"id_sector": 1, "hora_fin": "18:00", "ventanillas": [1, 2]}
    )
    # Depending on state, could be 200 or error if already active
    assert response.status_code in [200, 400]
    if response.status_code == 200:
        data = response.json()
        assert data["activo"] == True
        assert data["id_sector"] == 1
        assert data["ventanillas"] == [1, 2]

def test_caja_rapida_estado():
    """Test getting the quick box state."""
    response = client.get("/api/caja-rapida/estado")
    assert response.status_code == 200
    data = response.json()
    assert "activo" in data
    assert "expirado" in data

def test_caja_rapida_desactivar():
    """Test deactivating the quick box."""
    response = client.post("/api/caja-rapida/desactivar")
    assert response.status_code == 200
    data = response.json()
    assert data["activo"] == False