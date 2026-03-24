from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime

class VentanillaBase(BaseModel):
    """Base schema for Ventanilla data."""
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)
    ventanilla: str = Field(..., alias="Ventanilla", max_length=100, pattern=r"^[a-zA-Z0-9\s_-]+$")
    id_sector: int = Field(..., alias="ID_Sector")
    activa: bool = Field(default=True, alias="Activa")

class VentanillaResponse(VentanillaBase):
    """Schema for Ventanilla response data."""
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True, populate_by_name=True)
    id_ventanilla: int = Field(..., alias="ID_Ventanilla")
    sector: Optional[str] = Field(default=None, alias="Sector", max_length=50)

class EmpleadoVentanillaBase(BaseModel):
    """Base schema for EmpleadoVentanilla association."""
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)
    id_empleado: int = Field(..., alias="ID_Empleado")
    id_ventanilla: int = Field(..., alias="ID_Ventanilla")
    id_estado: int = Field(default=1, alias="ID_Estado")

class EmpleadoVentanillaResponse(EmpleadoVentanillaBase):
    """Schema for EmpleadoVentanilla response data."""
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True, populate_by_name=True)
    id_empleado_ventanilla: int = Field(..., alias="ID_Empleado_Ventanilla")
    fecha_inicio: datetime = Field(..., alias="Fecha_Inicio")
    fecha_termino: Optional[datetime] = Field(default=None, alias="Fecha_Termino")

class VentanillaUpdateReq(BaseModel):
    """Schema for Ventanilla update request."""
    model_config = ConfigDict(str_strip_whitespace=True)
    activa: Optional[int] = None
    nombre: Optional[str] = Field(default=None, max_length=100, pattern=r"^[a-zA-Z0-9\s_-]*$")

class EmpleadoVentanillaUpdateReq(BaseModel):
    """Schema for EmpleadoVentanilla update request."""
    model_config = ConfigDict(str_strip_whitespace=True)
    id_ventanilla: Optional[int] = None