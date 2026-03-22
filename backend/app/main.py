from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.routers import (
    auth, ventanillas, tickets, empleados,
    caja_rapida, reporte, health, dashboard
)
from app.websocket.routes import router as websocket_router

from app.models.database import engine, get_db
from app.config import settings
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI(title="UAL API - FastAPI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción deben definirse los dominios reales
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware, 
    secret_key=settings.SECRET_KEY,
    session_cookie="session",
    max_age=86400 * 7
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

app.include_router(auth.router)
app.include_router(ventanillas.router)
app.include_router(tickets.router)
app.include_router(empleados.router)
app.include_router(caja_rapida.router)
app.include_router(reporte.router)
app.include_router(health.router)
app.include_router(dashboard.router)
app.include_router(websocket_router)

