import pytest
from pydantic import ValidationError
from app.schemas.auth import LoginRequest, LoginResponse

def test_login_request_valid():
    obj = LoginRequest(username=" admin ", password=" password123 ")
    assert obj.username == "admin"
    assert obj.password == "password123"

def test_login_request_invalid_username():
    with pytest.raises(ValidationError):
        LoginRequest(username="admin@domain", password="password123")

def test_login_response_valid():
    data = {
        "id": 1,
        "nombre": "Admin",
        "rol": 1,
        "sector": "General",
        "estado": "Activo",
        "session_token": "token123"
    }
    obj = LoginResponse(**data)
    assert obj.id == 1
    assert obj.nombre == "Admin"

def test_login_response_strip():
    data = {
        "id": 1,
        "nombre": " Admin ",
        "rol": 1,
        "sector": " General ",
        "estado": " Activo ",
        "session_token": " token123 "
    }
    obj = LoginResponse(**data)
    assert obj.nombre == "Admin"
    assert obj.sector == "General"
    assert obj.estado == "Activo"
    assert obj.session_token == "token123"