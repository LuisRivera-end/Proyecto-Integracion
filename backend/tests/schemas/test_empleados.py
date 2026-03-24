import pytest
from pydantic import ValidationError
from app.schemas.empleados import SectorBase, SectorResponse, EmpleadoBase, EmpleadoCreate, EmpleadoResponse, EmpleadoCreateReq, EmpleadoUpdateReq

def test_sector_base_valid():
    obj = SectorBase(Sector="Caja")
    assert obj.sector == "Caja"

def test_sector_base_invalid_pattern():
    with pytest.raises(ValidationError):
        SectorBase(Sector="Caja!@#")

def test_sector_base_strip():
    obj = SectorBase(Sector=" Caja ")
    assert obj.sector == "Caja"

def test_empleado_base_valid():
    obj = EmpleadoBase(Nombre="Juan", Apellidos="Perez", Usuario="juanp", ID_ROL=1)
    assert obj.nombre == "Juan"
    assert obj.id_estado == 1

def test_empleado_base_invalid_usuario():
    with pytest.raises(ValidationError):
        EmpleadoBase(Nombre="Juan", Apellidos="Perez", Usuario="juan p", ID_ROL=1)

def test_empleado_create_req_valid():
    data = {
        "nombre1": "Juan",
        "apellido1": "Perez",
        "usuario": "juanp",
        "passwd": "password123",
        "id_rol": 1
    }
    obj = EmpleadoCreateReq(**data)
    assert obj.nombre1 == "Juan"
    assert obj.usuario == "juanp"

def test_empleado_create_req_invalid_password_length():
    data = {
        "nombre1": "Juan",
        "apellido1": "Perez",
        "usuario": "juanp",
        "passwd": "short",
        "id_rol": 1
    }
    with pytest.raises(ValidationError):
        EmpleadoCreateReq(**data)

def test_empleado_update_req_valid():
    data = {
        "nombre1": "Juan",
        "apellido1": "Perez",
        "usuario": "juanp"
    }
    obj = EmpleadoUpdateReq(**data)
    assert obj.nombre1 == "Juan"

def test_empleado_update_req_invalid():
    data = {
        "nombre1": "Juan123!",
        "apellido1": "Perez",
        "usuario": "juanp"
    }
    with pytest.raises(ValidationError):
        EmpleadoUpdateReq(**data)