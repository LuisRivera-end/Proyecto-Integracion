from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TicketBase(BaseModel):
    Folio: str
    ID_Sector: int
    Matricula_ID: Optional[str] = None
    Estatus: str = "En Espera"

class TicketCreate(BaseModel):
    ID_Sector: int
    Matricula_ID: Optional[str] = None

class TicketResponse(TicketBase):
    ID_Ticket: int
    Fecha_Creacion: datetime
    Fecha_Atencion: Optional[datetime] = None
    ID_Ventanilla: Optional[int] = None
    ID_Empleado: Optional[int] = None
    Sector_Abreviatura: Optional[str] = None

    class Config:
        from_attributes = True

class TurnoRequest(BaseModel):
    folio: str
    ventanilla_nombre: Optional[str] = ""
    id_ventanilla: Optional[int] = None
