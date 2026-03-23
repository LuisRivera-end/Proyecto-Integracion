from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime

class VentanillaBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    Ventanilla: str = Field(..., max_length=100)
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

class VentanillaUpdateReq(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    activa: Optional[int] = None
    nombre: Optional[str] = Field(default=None, max_length=100)

class EmpleadoVentanillaUpdateReq(BaseModel):
    id_ventanilla: Optional[int] = None
