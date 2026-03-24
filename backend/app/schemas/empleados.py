from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List

class SectorBase(BaseModel):
    """Base schema for Sector data."""
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)
    sector: str = Field(..., alias="Sector", max_length=20, pattern=r"^[a-zA-Z0-9\s_-]+$")

class SectorResponse(SectorBase):
    """Schema for Sector response data."""
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True, populate_by_name=True)
    id_sector: int = Field(..., alias="ID_Sector")

class EmpleadoBase(BaseModel):
    """Base schema for Empleado data."""
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)
    nombre: str = Field(..., alias="Nombre", max_length=50)
    apellidos: str = Field(..., alias="Apellidos", max_length=50)
    usuario: str = Field(..., alias="Usuario", max_length=20, pattern=r"^[a-zA-Z0-9_.-]+$")
    id_rol: int = Field(..., alias="ID_ROL")
    id_estado: int = Field(default=1, alias="ID_Estado")

class EmpleadoCreate(EmpleadoBase):
    """Schema for creating a new Empleado."""
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)
    contrasena: str = Field(..., alias="Contrasena", min_length=8, max_length=100)

class EmpleadoResponse(EmpleadoBase):
    """Schema for Empleado response data."""
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True, populate_by_name=True)
    id_empleado: int = Field(..., alias="ID_Empleado")
    rol: Optional[str] = Field(default=None, alias="Rol", max_length=50)
    estado_empleado: Optional[str] = Field(default=None, alias="Estado_Empleado", max_length=50)

class EmpleadoCreateReq(BaseModel):
    """Schema for Empleado creation request."""
    model_config = ConfigDict(str_strip_whitespace=True)
    nombre1: str = Field(..., max_length=20, pattern=r"^[a-zA-Z0-9\s]+$")
    nombre2: Optional[str] = Field(default="", max_length=20)
    apellido1: str = Field(..., max_length=20, pattern=r"^[a-zA-Z0-9\s]+$")
    apellido2: Optional[str] = Field(default="", max_length=20)
    usuario: str = Field(..., max_length=20, pattern=r"^[a-zA-Z0-9_.-]+$")
    passwd: str = Field(..., min_length=8, max_length=100)
    id_rol: int
    id_sector: Optional[int] = None

class EmpleadoUpdateReq(BaseModel):
    """Schema for Empleado update request."""
    model_config = ConfigDict(str_strip_whitespace=True)
    nombre1: str = Field(..., max_length=20, pattern=r"^[a-zA-Z0-9\s]+$")
    nombre2: Optional[str] = Field(default="", max_length=20)
    apellido1: str = Field(..., max_length=20, pattern=r"^[a-zA-Z0-9\s]+$")
    apellido2: Optional[str] = Field(default="", max_length=20)
    usuario: str = Field(..., max_length=20, pattern=r"^[a-zA-Z0-9_.-]+$")
    passwd: Optional[str] = Field(default=None, min_length=8, max_length=100)

class EmpleadoStatusReq(BaseModel):
    """Schema for Empleado status update request."""
    model_config = ConfigDict(str_strip_whitespace=True)
    estado: int

class EmpleadoSectorReq(BaseModel):
    """Schema for Empleado sector update request."""
    model_config = ConfigDict(str_strip_whitespace=True)
    id_sector: Optional[int] = None

class SectorCreateReq(BaseModel):
    """Schema for Sector creation request."""
    model_config = ConfigDict(str_strip_whitespace=True)
    sector: str = Field(..., max_length=20, pattern=r"^[a-zA-Z0-9\s_-]+$")
    ventanillas: int

class SectorUpdateReq(BaseModel):
    """Schema for Sector update request."""
    model_config = ConfigDict(str_strip_whitespace=True)
    sector: str = Field(..., max_length=20, pattern=r"^[a-zA-Z0-9\s_-]+$")