from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class LoginRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    username: str = Field(..., max_length=20, pattern=r"^[a-zA-Z0-9_-]+$")
    password: str = Field(..., min_length=1, max_length=100)

class LoginResponse(BaseModel):
    id: int
    nombre: str
    rol: int
    sector: str
    estado: str
    session_token: str
    id_ventanilla: Optional[int] = None
    ventanilla: Optional[str] = None
    sector_ventanilla: Optional[str] = None

class LogoutRequest(BaseModel):
    session_token: str

class RolResponse(BaseModel):
    ID_Rol: int
    Rol: str

class EstadoEmpleadoResponse(BaseModel):
    ID_Estado: int
    Nombre: str
