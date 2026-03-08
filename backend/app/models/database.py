from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import DATABASE_URL

engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Cambiar a True para ver las queries en consola
    pool_recycle=3600
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

Base = declarative_base()

# Dependencia para inyectar en las rutas FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session