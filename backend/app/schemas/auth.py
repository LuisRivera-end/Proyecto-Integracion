from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class LoginRequest(BaseModel):
    """Schema for user login request."""
    model_config = ConfigDict(str_strip_whitespace=True)
    username: str = Field(..., max_length=20, pattern=r"^[a-zA-Z0-9_-]+$")
    password: str = Field(..., min_length=1, max_length=100)

class LoginResponse(BaseModel):
    """Schema for login response."""
    model_config = ConfigDict(str_strip_whitespace=True)
    id: int
    nombre: str = Field(..., max_length=100)
    rol: int
    sector: str = Field(..., max_length=50)
    estado: str = Field(..., max_length=20)
    session_token: str = Field(..., max_length=100)
    id_ventanilla: Optional[int] = None
    ventanilla: Optional[str] = Field(default=None, max_length=100)
    sector_ventanilla: Optional[str] = Field(default=None, max_length=50)

class LogoutRequest(BaseModel):
    """Schema for user logout request."""
    model_config = ConfigDict(str_strip_whitespace=True)
    session_token: str = Field(..., max_length=100)

class RolResponse(BaseModel):
    """Schema for Rol response."""
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True, populate_by_name=True)
    id_rol: int = Field(..., alias="ID_Rol")
    rol: str = Field(..., alias="Rol", max_length=30)

class EstadoEmpleadoResponse(BaseModel):
    """Schema for EstadoEmpleado response."""
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True, populate_by_name=True)
    id_estado: int = Field(..., alias="ID_Estado")
    nombre: str = Field(..., alias="Nombre", max_length=15)