from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class VentanillaBase(BaseModel):
    Ventanilla: str
    ID_Sector: int
    Activa: bool = True

class VentanillaResponse(VentanillaBase):
    ID_Ventanilla: int
    Sector: Optional[str] = None
    
    class Config:
        from_attributes = True

class EmpleadoVentanillaBase(BaseModel):
    ID_Empleado: int
    ID_Ventanilla: int
    ID_Estado: int = 1

class EmpleadoVentanillaResponse(EmpleadoVentanillaBase):
    ID_Empleado_Ventanilla: int
    Fecha_Inicio: datetime
    Fecha_Termino: Optional[datetime] = None
    
    class Config:
        from_attributes = True
