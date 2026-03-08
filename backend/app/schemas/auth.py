from pydantic import BaseModel
from typing import Optional

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    id: int
    nombre: str
    rol: int
    sector: str
    estado: str
    id_ventanilla: Optional[int] = None
    ventanilla: Optional[str] = None
    sector_ventanilla: Optional[str] = None

class RolResponse(BaseModel):
    ID_Rol: int
    Rol: str

class EstadoEmpleadoResponse(BaseModel):
    ID_Estado: int
    Nombre: str
