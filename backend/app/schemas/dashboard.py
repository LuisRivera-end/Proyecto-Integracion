from pydantic import BaseModel
from typing import List

class SectorStats(BaseModel):
    id_sector: int
    nombre: str
    tickets_en_cola: int
    ventanillas_activas: int

class DashboardStats(BaseModel):
    tickets_en_cola: int
    tickets_atendiendo: int
    tickets_completados_hoy: int
    empleados_activos: int
    empleados_en_ventanilla: int
    tiempo_espera_promedio_segundos: float | None
    tiempo_servicio_promedio_segundos: float | None
    por_sector: List[SectorStats]
