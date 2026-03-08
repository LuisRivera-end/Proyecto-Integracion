from pydantic import BaseModel
from typing import Optional, List

class SectorBase(BaseModel):
    Sector: str
    Abreviatura: str
    Activo: bool = True

class SectorResponse(SectorBase):
    ID_Sector: int
    
    class Config:
        from_attributes = True

class EmpleadoBase(BaseModel):
    Nombre: str
    Apellidos: str
    Usuario: str
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
