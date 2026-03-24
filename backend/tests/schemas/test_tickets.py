import pytest
from pydantic import ValidationError
from app.schemas.tickets import TicketBase, TurnoRequest

def test_ticket_base_valid():
    obj = TicketBase(Folio="FOLIO-123", ID_Sector=1)
    assert obj.folio == "FOLIO-123"
    assert obj.id_sector == 1
    assert obj.estatus == "En Espera"

def test_ticket_base_invalid_folio():
    with pytest.raises(ValidationError):
        TicketBase(Folio="FOLIO 123!", ID_Sector=1)

def test_turno_request_valid():
    obj = TurnoRequest(folio="FOLIO-123", ventanilla_nombre="Caja 1")
    assert obj.folio == "FOLIO-123"

def test_turno_request_invalid_folio():
    with pytest.raises(ValidationError):
        TurnoRequest(folio="FOLIO 123", ventanilla_nombre="Caja 1")

def test_ticket_base_strip():
    obj = TicketBase(Folio=" FOLIO-123 ", ID_Sector=1)
    assert obj.folio == "FOLIO-123"