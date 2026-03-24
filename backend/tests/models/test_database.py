import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import get_db

@pytest.mark.asyncio
async def test_get_db_yields_session():
    """
    Test que asegura que get_db es un generador asíncrono que proporciona
    una instancia de la sesión y la cierra al finalizar.
    """
    with patch("app.models.database.async_session_local") as mock_session_maker:
        mock_session = AsyncMock(spec=AsyncSession)
        
        # mock_session_maker devuelve un context manager asincrono
        mock_session_maker.return_value.__aenter__.return_value = mock_session
        
        generator = get_db()
        
        # Test yield
        session = await anext(generator)
        assert session is mock_session
        
        # Verificamos que se haya entrado al context manager
        mock_session_maker.return_value.__aenter__.assert_awaited_once()

        # Test fin del generador y cierre de sesión (salir de context manager)
        with pytest.raises(StopAsyncIteration):
            await anext(generator)
            
        mock_session_maker.return_value.__aexit__.assert_awaited_once()
