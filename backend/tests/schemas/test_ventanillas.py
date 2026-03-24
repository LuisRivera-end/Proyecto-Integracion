import pytest
from pydantic import ValidationError
from app.schemas.ventanillas import VentanillaBase, VentanillaUpdateReq

def test_ventanilla_base_valid():
    obj = VentanillaBase(Ventanilla="Caja 1", ID_Sector=1)
    assert obj.ventanilla == "Caja 1"
    assert obj.activa is True

def test_ventanilla_base_invalid_pattern():
    with pytest.raises(ValidationError):
        VentanillaBase(Ventanilla="Caja 1!", ID_Sector=1)

def test_ventanilla_update_req_valid():
    obj = VentanillaUpdateReq(nombre=" Caja 2 ")
    assert obj.nombre == "Caja 2"

def test_ventanilla_update_req_invalid():
    with pytest.raises(ValidationError):
        VentanillaUpdateReq(nombre="Caja 2@")

def test_ventanilla_base_strip():
    obj = VentanillaBase(Ventanilla=" Caja 1 ", ID_Sector=1)
    assert obj.ventanilla == "Caja 1"