from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.database import Base

class Sector(Base):
    __tablename__ = "Sectores"
    
    ID_Sector = Column(Integer, primary_key=True, autoincrement=True)
    Sector = Column(String(100), nullable=False)
    Abreviatura = Column(String(10), nullable=False)
    Activo = Column(Boolean, default=True)

class Ventanilla(Base):
    __tablename__ = "Ventanillas"
    
    ID_Ventanilla = Column(Integer, primary_key=True, autoincrement=True)
    Ventanilla = Column(String(100), nullable=False)
    ID_Sector = Column(Integer, ForeignKey("Sectores.ID_Sector"))
    Activa = Column(Boolean, default=True)
    
    # relacion con sector si se necesita en el futuro
    # sector = relationship("Sector")

class Empleado(Base):
    __tablename__ = "Empleado"
    
    ID_Empleado = Column(Integer, primary_key=True, autoincrement=True)
    Nombre = Column(String(50), nullable=False)
    Apellidos = Column(String(50), nullable=False)
    Usuario = Column(String(20), nullable=False, unique=True)
    Passwd = Column(String(100), nullable=False)
    ID_ROL = Column(Integer, nullable=False)
    ID_Estado = Column(Integer, default=1)

class Ticket(Base):
    __tablename__ = "Tickets"
    
    ID_Ticket = Column(Integer, primary_key=True, autoincrement=True)
    Folio = Column(String(50), nullable=False, unique=True)
    ID_Sector = Column(Integer, ForeignKey("Sectores.ID_Sector"))
    Matricula_ID = Column(String(50), nullable=True)
    Estatus = Column(String(20), default="En Espera")
    Fecha_Creacion = Column(DateTime, default=datetime.utcnow)
    Fecha_Atencion = Column(DateTime, nullable=True)
    ID_Ventanilla = Column(Integer, ForeignKey("Ventanillas.ID_Ventanilla"), nullable=True)
    ID_Empleado = Column(Integer, ForeignKey("Empleado.ID_Empleado"), nullable=True)

class EmpleadoVentanilla(Base):
    __tablename__ = "Empleado_Ventanilla"
    
    ID_Empleado_Ventanilla = Column(Integer, primary_key=True, autoincrement=True)
    ID_Empleado = Column(Integer, ForeignKey("Empleado.ID_Empleado"))
    ID_Ventanilla = Column(Integer, ForeignKey("Ventanillas.ID_Ventanilla"))
    Fecha_Inicio = Column(DateTime, default=datetime.utcnow)
    Fecha_Termino = Column(DateTime, nullable=True)
    ID_Estado = Column(Integer, default=1) # 1=Activo, 2=Terminado
