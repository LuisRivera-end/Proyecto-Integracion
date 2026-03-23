from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.database import Base

class Rol(Base):
    __tablename__ = "Rol"
    
    ID_Rol = Column(Integer, primary_key=True, autoincrement=True)
    Rol = Column(String(30), nullable=False)

class Sector(Base):
    __tablename__ = "Sectores"
    
    ID_Sector = Column(Integer, primary_key=True, autoincrement=True)
    Sector = Column(String(20), nullable=False)

class EstadoEmpleado(Base):
    __tablename__ = "Estado_Empleado"
    
    ID_Estado = Column(Integer, primary_key=True, autoincrement=True)
    Nombre = Column(String(15), nullable=False)

class EstadoEmpleadoVentanilla(Base):
    __tablename__ = "Estado_empleado_ventanilla"
    
    ID_Estado = Column(Integer, primary_key=True, autoincrement=True)
    Nombre = Column(String(15), nullable=False)

class EstadoTurno(Base):
    __tablename__ = "Estados_Turno"
    
    ID_Estado = Column(Integer, primary_key=True, autoincrement=True)
    Nombre = Column(String(15), nullable=False)

class Ventanilla(Base):
    __tablename__ = "Ventanillas"
    
    ID_Ventanilla = Column(Integer, primary_key=True, autoincrement=True)
    Ventanilla = Column(String(30), nullable=False)
    ID_Sector = Column(Integer, ForeignKey("Sectores.ID_Sector"), nullable=False)
    Activa = Column(Boolean, nullable=False, default=True)

class Empleado(Base):
    __tablename__ = "Empleado"
    
    ID_Empleado = Column(Integer, primary_key=True, autoincrement=True)
    ID_ROL = Column(Integer, ForeignKey("Rol.ID_Rol"), nullable=False)
    nombre1 = Column(String(20), nullable=False)
    nombre2 = Column(String(20), nullable=False, default='')
    Apellido1 = Column(String(20), nullable=False)
    Apellido2 = Column(String(20), nullable=False, default='')
    Usuario = Column(String(20), nullable=False, unique=True)
    Passwd = Column(String(70), nullable=False)
    ID_Estado = Column(Integer, ForeignKey("Estado_Empleado.ID_Estado"), nullable=False)
    ID_Sector = Column(Integer, ForeignKey("Sectores.ID_Sector"), nullable=True)

class EmpleadoVentanilla(Base):
    __tablename__ = "Empleado_Ventanilla"
    
    ID_Asignacion = Column(Integer, primary_key=True, autoincrement=True)
    ID_Empleado = Column(Integer, ForeignKey("Empleado.ID_Empleado"), nullable=False)
    ID_Ventanilla = Column(Integer, ForeignKey("Ventanillas.ID_Ventanilla"), nullable=False)
    Fecha_Inicio = Column(DateTime, nullable=False, default=datetime.utcnow)
    Fecha_Termino = Column(DateTime, nullable=True)
    ID_Estado = Column(Integer, ForeignKey("Estado_empleado_ventanilla.ID_Estado"), nullable=False)

class Turno(Base):
    __tablename__ = "Turno"
    
    ID_Turno = Column(Integer, primary_key=True, autoincrement=True)
    ID_Sector = Column(Integer, ForeignKey("Sectores.ID_Sector"), nullable=False)
    ID_Ventanilla = Column(Integer, ForeignKey("Ventanillas.ID_Ventanilla"), nullable=True)
    Fecha_Ticket = Column(DateTime(timezone=False), nullable=False)
    Folio = Column(String(10), nullable=False)
    ID_Estados = Column(Integer, ForeignKey("Estados_Turno.ID_Estado"), nullable=False)
    Fecha_Ultimo_Estado = Column(DateTime(timezone=False), nullable=False)
    Tipo_Caja = Column(String(10), nullable=False, default='normal')

class RolVentanilla(Base):
    __tablename__ = "Rol_Ventanilla"
    
    ID_Rol = Column(Integer, ForeignKey("Rol.ID_Rol"), primary_key=True)
    ID_Ventanilla = Column(Integer, ForeignKey("Ventanillas.ID_Ventanilla"), primary_key=True)

class SesionActiva(Base):
    __tablename__ = "Sesion_Activa"
    
    Token = Column(String(64), primary_key=True)
    ID_Empleado = Column(Integer, ForeignKey("Empleado.ID_Empleado", ondelete="CASCADE"), nullable=False)
    Activa = Column(Boolean, nullable=False, default=True)
    Creada = Column(DateTime, nullable=False, default=datetime.utcnow)
    Expira = Column(DateTime, nullable=False)
