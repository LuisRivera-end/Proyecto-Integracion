from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import DATABASE_URL

engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Cambiar a True para ver las queries en consola
    pool_recycle=3600
)

async_session_local = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

Base = declarative_base()

async def get_db():
    """
    Dependencia de FastAPI para obtener la sesión de la base de datos.
    Asegura que la conexión se cierre o se devuelva al pool automáticamente después de cada petición.
    
    Yields:
        AsyncSession: Sesión asíncrona de SQLAlchemy.
    """
    async with async_session_local() as session:
        yield session