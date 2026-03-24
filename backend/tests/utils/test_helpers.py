import pytest
from unittest.mock import AsyncMock, patch
from app.utils.helpers import get_sector_prefix, _gen_prefix, generar_folio_unico, obtener_fecha_actual, obtener_fecha_publico, speak_to_file

@pytest.mark.asyncio
async def test_get_sector_prefix(mock_db_session):
    mock_db_session.execute.return_value.fetchall.return_value = [("Servicios Escolares",), ("Cajas",)]
    prefix = await get_sector_prefix("Servicios Escolares", mock_db_session)
    assert prefix == "SE"
    
    prefix2 = await get_sector_prefix("Cajas", mock_db_session)
    assert prefix2 == "C"

def test_gen_prefix():
    assert _gen_prefix("Servicios Escolares", set()) == "SE"
    assert _gen_prefix("Cajas", set()) == "C"
    assert _gen_prefix("Cajas", {"C"}) == "CA"

@pytest.mark.asyncio
async def test_generar_folio_unico(mock_db_session):
    # Mock para get_sector_prefix
    mock_db_session.execute.return_value.fetchall.return_value = [("Cajas",)]
    
    # Necesitamos mockear fetchone que se llama dentro de generar_folio_unico
    mock_result = AsyncMock()
    mock_result.fetchone.return_value = (15,)
    
    # Primero se llama db.execute() en get_sector_prefix (devuelve mock con fetchall)
    # Luego en generar_folio_unico (devuelve mock con fetchone)
    mock_db_session.execute.side_effect = [
        AsyncMock(fetchall=lambda: [("Cajas",)]),
        mock_result
    ]
    
    folio = await generar_folio_unico("Cajas", mock_db_session)
    assert folio == "C16"

def test_obtener_fecha_actual():
    fecha = obtener_fecha_actual()
    assert isinstance(fecha, str)
    assert len(fecha) > 10

def test_obtener_fecha_publico():
    fecha = obtener_fecha_publico()
    assert isinstance(fecha, str)
    assert len(fecha) > 10

@patch("app.utils.helpers.subprocess.run")
@patch("app.utils.helpers.threading.Timer")
def test_speak_to_file(mock_timer, mock_subprocess):
    # Sin mockear gTTS para que intente importarlo, o si falla pase a subprocess
    filename = speak_to_file("Prueba")
    assert filename.startswith("turno_")
