import pytest
from pydantic import ValidationError
from app.schemas.dashboard import SectorStats, DashboardStats

def test_sector_stats_valid():
    data = {
        "id_sector": 1,
        "nombre": "Ventas",
        "tickets_en_cola": 5,
        "ventanillas_activas": 2
    }
    obj = SectorStats(**data)
    assert obj.id_sector == 1
    assert obj.nombre == "Ventas"

def test_sector_stats_whitespace_stripping():
    data = {
        "id_sector": 1,
        "nombre": " Ventas ",
        "tickets_en_cola": 5,
        "ventanillas_activas": 2
    }
    obj = SectorStats(**data)
    assert obj.nombre == "Ventas"

def test_dashboard_stats_valid():
    sector_data = {
        "id_sector": 1,
        "nombre": "Ventas",
        "tickets_en_cola": 5,
        "ventanillas_activas": 2
    }
    data = {
        "tickets_en_cola": 10,
        "tickets_atendiendo": 2,
        "tickets_completados_hoy": 100,
        "empleados_activos": 5,
        "empleados_en_ventanilla": 3,
        "tiempo_espera_promedio_segundos": 120.5,
        "tiempo_servicio_promedio_segundos": 300.2,
        "por_sector": [sector_data]
    }
    obj = DashboardStats(**data)
    assert obj.tickets_en_cola == 10
    assert len(obj.por_sector) == 1

def test_dashboard_stats_invalid():
    with pytest.raises(ValidationError):
        # Missing required field
        DashboardStats(tickets_en_cola=10)
