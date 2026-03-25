from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, func, and_, case, text
from datetime import datetime
import pytz

from app.models.database import get_db
from app.models.models import (
    Turno, Sector, Ventanilla, Empleado, SesionActiva, 
    EstadoTurno, EmpleadoVentanilla, RolVentanilla
)
from app.schemas.dashboard import DashboardStats, SectorStats

router = APIRouter(prefix="/api", tags=["Dashboard"])


@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(request: Request, db: AsyncSession = Depends(get_db)):
    session_token = request.query_params.get("session_token")
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Token requerido")
    
    token_query = (
        select(SesionActiva.ID_Empleado, SesionActiva.Expira, Empleado.ID_ROL)
        .join(Empleado, SesionActiva.ID_Empleado == Empleado.ID_Empleado)
        .where(and_(SesionActiva.Token == session_token, SesionActiva.Activa == True))
    )
    token_result = await db.execute(token_query)
    token_row = token_result.mappings().fetchone()
    
    if not token_row:
        raise HTTPException(status_code=401, detail="Sesion invalida")
    
    if token_row["Expira"] < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Sesion expirada")
    
    user_rol = token_row["ID_ROL"]
    if user_rol not in (1, 6):
        raise HTTPException(status_code=403, detail="Acceso denegado. Solo administradores y subjefes.")
    
    tz = pytz.timezone('America/Mexico_City')
    hoy_local = datetime.now(tz).strftime('%Y-%m-%d')
    
    tickets_en_cola_q = select(func.count(Turno.ID_Turno)).where(Turno.ID_Estados == 1)
    res_cola = await db.execute(tickets_en_cola_q)
    tickets_en_cola = res_cola.scalar() or 0
    
    tickets_atendiendo_q = select(func.count(Turno.ID_Turno)).where(Turno.ID_Estados == 3)
    res_atendiendo = await db.execute(tickets_atendiendo_q)
    tickets_atendiendo = res_atendiendo.scalar() or 0
    
    tickets_completados_q = (
        select(func.count(Turno.ID_Turno))
        .where(and_(Turno.ID_Estados == 4, func.date(Turno.Fecha_Ticket) == hoy_local))
    )
    res_completados = await db.execute(tickets_completados_q)
    tickets_completados_hoy = res_completados.scalar() or 0
    
    empleados_activos_q = (
        select(func.count(SesionActiva.Token))
        .where(and_(SesionActiva.Activa == True, SesionActiva.Expira > datetime.utcnow()))
    )
    res_emp_activos = await db.execute(empleados_activos_q)
    empleados_activos = res_emp_activos.scalar() or 0
    
    try:
        from app.websocket.manager import manager
        empleados_en_ventanilla = len(manager.active_ventanilla_employees)
    except Exception:
        empleados_en_ventanilla = 0
    
    tiempo_espera_promedio = None
    try:
        tiempo_espera_sql = text("""
            SELECT AVG(TIMESTAMPDIFF(SECOND, Fecha_Ticket, Fecha_Ultimo_Estado)) as avg_wait
            FROM Turno
            WHERE ID_Estados IN (3, 4)
            AND DATE(Fecha_Ticket) = :hoy
        """)
        res_espera = await db.execute(tiempo_espera_sql, {"hoy": hoy_local})
        row_espera = res_espera.fetchone()
        if row_espera and row_espera[0] is not None:
            tiempo_espera_promedio = float(row_espera[0])
    except Exception:
        pass
    
    sectores_q = (
        select(
            Sector.ID_Sector,
            Sector.Sector
        )
        .order_by(Sector.Sector)
    )
    res_sectores = await db.execute(sectores_q)
    sectores_raw = res_sectores.mappings().fetchall()
    
    por_sector = []
    for s in sectores_raw:
        tickets_cola_q = (
            select(func.count(Turno.ID_Turno))
            .where(and_(Turno.ID_Sector == s["ID_Sector"], Turno.ID_Estados == 1))
        )
        res_tickets = await db.execute(tickets_cola_q)
        tickets_en_cola_sector = res_tickets.scalar() or 0
        
        v_activas_q = (
            select(func.count(Ventanilla.ID_Ventanilla))
            .where(and_(Ventanilla.ID_Sector == s["ID_Sector"], Ventanilla.Activa == True))
        )
        res_v = await db.execute(v_activas_q)
        ventanillas_activas = res_v.scalar() or 0
        
        por_sector.append(SectorStats(
            id_sector=s["ID_Sector"],
            nombre=s["Sector"],
            tickets_en_cola=tickets_en_cola_sector,
            ventanillas_activas=ventanillas_activas
        ))
    
    historico_sql = text("""
        SELECT 
            DATE(Fecha_Ticket) as fecha,
            SUM(CASE WHEN ID_Estados = 4 THEN 1 ELSE 0 END) as completados,
            SUM(CASE WHEN ID_Estados = 2 THEN 1 ELSE 0 END) as cancelados,
            AVG(CASE WHEN ID_Estados IN (3, 4) THEN TIMESTAMPDIFF(SECOND, Fecha_Ticket, Fecha_Ultimo_Estado) ELSE NULL END) as tiempo_promedio_espera
        FROM Turno
        WHERE Fecha_Ticket >= DATE_SUB(:hoy, INTERVAL 6 DAY)
        GROUP BY DATE(Fecha_Ticket)
        ORDER BY DATE(Fecha_Ticket) ASC
    """)
    res_historico = await db.execute(historico_sql, {"hoy": hoy_local})
    historico_raw = res_historico.fetchall()
    
    historico_7_dias = []
    for row in historico_raw:
        historico_7_dias.append({
            "fecha": str(row[0]),
            "completados": int(row[1]) if row[1] else 0,
            "cancelados": int(row[2]) if row[2] else 0,
            "tiempo_promedio_espera": float(row[3]) if row[3] is not None else None
        })

    return DashboardStats(
        tickets_en_cola=tickets_en_cola,
        tickets_atendiendo=tickets_atendiendo,
        tickets_completados_hoy=tickets_completados_hoy,
        empleados_activos=empleados_activos,
        empleados_en_ventanilla=empleados_en_ventanilla,
        tiempo_espera_promedio_segundos=tiempo_espera_promedio,
        tiempo_servicio_promedio_segundos=None,
        por_sector=por_sector,
        historico_7_dias=historico_7_dias
    )
