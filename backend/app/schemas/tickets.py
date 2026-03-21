from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime

class TicketBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    Folio: str = Field(..., max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    ID_Sector: int
    Matricula_ID: Optional[str] = Field(default=None, max_length=50)
    Estatus: str = Field(default="En Espera", max_length=20)

class TicketCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    ID_Sector: int
    Matricula_ID: Optional[str] = Field(default=None, max_length=50)

class TicketResponse(TicketBase):
    ID_Ticket: int
    Fecha_Creacion: datetime
    Fecha_Atencion: Optional[datetime] = None
    ID_Ventanilla: Optional[int] = None
    ID_Empleado: Optional[int] = None

    class Config:
        from_attributes = True

class TurnoRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    folio: str = Field(..., max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    ventanilla_nombre: Optional[str] = Field(default="", max_length=100)
    id_ventanilla: Optional[int] = None

class TicketGenerateReq(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    sector: str = Field(..., max_length=50)
    tipo_caja: Optional[str] = Field(default="normal", max_length=20)

class TicketAttendReq(BaseModel):
    id_ventanilla: int

class TicketNextReq(BaseModel):
    id_ventanilla: int
    id_empleado: int
    tipo_caja: Optional[str] = Field(default="normal", max_length=20)

class TurnoStatusReq(BaseModel):
    estado: int
