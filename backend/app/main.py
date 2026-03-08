from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.models.database import engine, get_db

app = FastAPI(title="UAL API - FastAPI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción deben definirse los dominios reales
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        from sqlalchemy import text
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API FastAPI UAL"}
