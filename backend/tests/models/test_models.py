import pytest
from app.models.models import (
    Rol, Sector, EstadoEmpleado, EstadoEmpleadoVentanilla,
    EstadoTurno, Ventanilla, Empleado, EmpleadoVentanilla,
    Turno, RolVentanilla, SesionActiva
)

def test_models_have_table_names():
    """
    Test que asegura que todos los modelos mapeados tienen su atributo __tablename__ definido.
    """
    models = [
        Rol, Sector, EstadoEmpleado, EstadoEmpleadoVentanilla,
        EstadoTurno, Ventanilla, Empleado, EmpleadoVentanilla,
        Turno, RolVentanilla, SesionActiva
    ]
    
    for model in models:
        assert hasattr(model, "__tablename__")
        assert getattr(model, "__tablename__") is not None

def test_empleado_model_attributes():
    """
    Test que verifica los atributos clave del modelo Empleado.
    """
    assert hasattr(Empleado, "Usuario")
    assert hasattr(Empleado, "Passwd")
    assert hasattr(Empleado, "ID_ROL")

def test_turno_model_attributes():
    """
    Test que verifica los atributos clave del modelo Turno.
    """
    assert hasattr(Turno, "Folio")
    assert hasattr(Turno, "Fecha_Ticket")
    assert hasattr(Turno, "ID_Estados")
