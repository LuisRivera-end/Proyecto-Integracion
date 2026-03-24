"""Pydantic schemas para los endpoints de configuración inicial (setup)."""

from pydantic import BaseModel, ConfigDict, Field


class SetupStatusResponse(BaseModel):
    """Respuesta del estado de configuración inicial."""
    model_config = ConfigDict(str_strip_whitespace=True)

    needs_setup: bool


class SetupInitResponse(BaseModel):
    """Respuesta tras generar el administrador temporal."""
    model_config = ConfigDict(str_strip_whitespace=True)

    usuario: str
    password: str
    message: str


class SetupFinalizeRequest(BaseModel):
    """Datos para finalizar la configuración del administrador."""
    model_config = ConfigDict(str_strip_whitespace=True)

    session_token: str = Field(..., min_length=1, max_length=100)
    nombre1: str = Field(..., max_length=20, pattern=r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$")
    nombre2: str = Field(default="", max_length=20)
    apellido1: str = Field(..., max_length=20, pattern=r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$")
    apellido2: str = Field(default="", max_length=20)
    usuario: str = Field(..., max_length=20, pattern=r"^[a-zA-Z0-9_.-]+$")
    passwd: str = Field(..., min_length=8, max_length=100)
