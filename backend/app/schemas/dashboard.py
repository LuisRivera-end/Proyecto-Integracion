from pydantic import BaseModel, ConfigDict
from typing import List

class SectorStats(BaseModel):
    """Schema representing statistics for a specific sector."""
    model_config = ConfigDict(str_strip_whitespace=True)
    id_sector: int
    nombre: str
    tickets_en_cola: int
    ventanillas_activas: int

class DashboardStats(BaseModel):
    """Schema representing overall dashboard statistics."""
    model_config = ConfigDict(str_strip_whitespace=True)
    tickets_en_cola: int
    tickets_atendiendo: int
    tickets_completados_hoy: int
    empleados_activos: int
    empleados_en_ventanilla: int
    tiempo_espera_promedio_segundos: float | None
    tiempo_servicio_promedio_segundos: float | None
    por_sector: List[SectorStats]