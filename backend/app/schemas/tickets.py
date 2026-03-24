from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime

class TicketBase(BaseModel):
    """Base schema for Ticket data."""
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)
    folio: str = Field(..., alias="Folio", max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    id_sector: int = Field(..., alias="ID_Sector")
    matricula_id: Optional[str] = Field(default=None, alias="Matricula_ID", max_length=50)
    estatus: str = Field(default="En Espera", alias="Estatus", max_length=20, pattern=r"^[a-zA-Z0-9\s_-]+$")

class TicketCreate(BaseModel):
    """Schema for creating a Ticket."""
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)
    id_sector: int = Field(..., alias="ID_Sector")
    matricula_id: Optional[str] = Field(default=None, alias="Matricula_ID", max_length=50)

class TicketResponse(TicketBase):
    """Schema for Ticket response data."""
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True, populate_by_name=True)
    id_ticket: int = Field(..., alias="ID_Ticket")
    fecha_creacion: datetime = Field(..., alias="Fecha_Creacion")
    fecha_atencion: Optional[datetime] = Field(default=None, alias="Fecha_Atencion")
    id_ventanilla: Optional[int] = Field(default=None, alias="ID_Ventanilla")
    id_empleado: Optional[int] = Field(default=None, alias="ID_Empleado")

class TurnoRequest(BaseModel):
    """Schema for Turno request."""
    model_config = ConfigDict(str_strip_whitespace=True)
    folio: str = Field(..., max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    ventanilla_nombre: Optional[str] = Field(default="", max_length=100)
    id_ventanilla: Optional[int] = None

class TicketGenerateReq(BaseModel):
    """Schema for Ticket generation request."""
    model_config = ConfigDict(str_strip_whitespace=True)
    sector: str = Field(..., max_length=50, pattern=r"^[a-zA-Z0-9\s_-]+$")
    tipo_caja: Optional[str] = Field(default="normal", max_length=20, pattern=r"^[a-zA-Z0-9\s_-]+$")

class TicketAttendReq(BaseModel):
    """Schema for attending a Ticket request."""
    model_config = ConfigDict(str_strip_whitespace=True)
    id_ventanilla: int

class TicketNextReq(BaseModel):
    """Schema for requesting next Ticket."""
    model_config = ConfigDict(str_strip_whitespace=True)
    id_ventanilla: int
    id_empleado: int
    tipo_caja: Optional[str] = Field(default="normal", max_length=20, pattern=r"^[a-zA-Z0-9\s_-]+$")

class TurnoStatusReq(BaseModel):
    """Schema for updating Turno status request."""
    model_config = ConfigDict(str_strip_whitespace=True)
    estado: int