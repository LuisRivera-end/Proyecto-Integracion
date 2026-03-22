from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List

class SectorBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    Sector: str = Field(..., max_length=20)

class SectorResponse(SectorBase):
    ID_Sector: int
    
    class Config:
        from_attributes = True

class EmpleadoBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    Nombre: str = Field(..., max_length=50)
    Apellidos: str = Field(..., max_length=50)
    Usuario: str = Field(..., max_length=20, pattern=r"^[a-zA-Z0-9_.-]+$")
    ID_ROL: int
    ID_Estado: int = 1

class EmpleadoCreate(EmpleadoBase):
    Contrasena: str

class EmpleadoResponse(EmpleadoBase):
    ID_Empleado: int
    Rol: Optional[str] = None
    Estado_Empleado: Optional[str] = None
    
    class Config:
        from_attributes = True

class EmpleadoCreateReq(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    nombre1: str = Field(..., max_length=20)
    nombre2: Optional[str] = Field(default="", max_length=20)
    apellido1: str = Field(..., max_length=20)
    apellido2: Optional[str] = Field(default="", max_length=20)
    usuario: str = Field(..., max_length=20, pattern=r"^[a-zA-Z0-9_.-]+$")
    passwd: str = Field(..., min_length=8)
    id_rol: int
    id_sector: Optional[int] = None

class EmpleadoUpdateReq(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    nombre1: str = Field(..., max_length=20)
    nombre2: Optional[str] = Field(default="", max_length=20)
    apellido1: str = Field(..., max_length=20)
    apellido2: Optional[str] = Field(default="", max_length=20)
    usuario: str = Field(..., max_length=20, pattern=r"^[a-zA-Z0-9_.-]+$")
    passwd: Optional[str] = Field(default=None)

class EmpleadoStatusReq(BaseModel):
    estado: int

class EmpleadoSectorReq(BaseModel):
    id_sector: Optional[int] = None

class SectorCreateReq(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    sector: str = Field(..., max_length=20)
    ventanillas: int

class SectorUpdateReq(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    sector: str = Field(..., max_length=20)
