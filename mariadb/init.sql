/* Script de Inicialización del Esquema TurnosUal para MariaDB (Optimizado) */

DROP DATABASE IF EXISTS `TurnosUal`;
CREATE DATABASE IF NOT EXISTS `TurnosUal`;
USE `TurnosUal`;

/* Tablas Sin Dependencias */
-- -----------------------------------------------------

DROP TABLE IF EXISTS `Rol`;
CREATE TABLE Rol (
    ID_Rol INT(1) PRIMARY KEY AUTO_INCREMENT,
    Rol VARCHAR(30) NOT NULL
);

DROP TABLE IF EXISTS `Sectores`;
CREATE TABLE Sectores (
    ID_Sector INT(1) PRIMARY KEY AUTO_INCREMENT, 
    Sector VARCHAR(20) NOT NULL
);

DROP TABLE IF EXISTS `Estado_Empleado`;
CREATE TABLE Estado_Empleado (
    ID_Estado INT(1) PRIMARY KEY AUTO_INCREMENT,
    Nombre VARCHAR(15) NOT NULL
);

DROP TABLE IF EXISTS `Estado_empleado_ventanilla`;
CREATE TABLE Estado_empleado_ventanilla (
    ID_Estado INT(1) PRIMARY KEY AUTO_INCREMENT,
    Nombre VARCHAR(15) NOT NULL
);

DROP TABLE IF EXISTS `Estados_Turno`;
CREATE TABLE Estados_Turno (
    ID_Estado INT(1) PRIMARY KEY AUTO_INCREMENT,
    Nombre VARCHAR(15) NOT NULL
);

DROP TABLE IF EXISTS `Tipo_Horario`;
CREATE TABLE Tipo_Horario (
    ID_Tipo INT(1) PRIMARY KEY AUTO_INCREMENT,
    Nombre VARCHAR(15) NOT NULL
);

DROP TABLE IF EXISTS `Alumnos`;
CREATE TABLE Alumnos (
    ID_Alumno INT(6) PRIMARY KEY AUTO_INCREMENT,
    nombre1 VARCHAR(20) NOT NULL,
    nombre2 VARCHAR(20) NOT NULL DEFAULT '',
    Apellido1 VARCHAR(20) NOT NULL,
    Apellido2 VARCHAR(20) NOT NULL DEFAULT '',
    Carrera VARCHAR(10) NOT NULL,
    Matricula INT(6) NOT NULL UNIQUE
);


/* Tablas con Dependencias Simples */
-- -----------------------------------------------------

DROP TABLE IF EXISTS `Horarios`;
CREATE TABLE Horarios (
    ID_Horario INT(6) AUTO_INCREMENT PRIMARY KEY,
    ID_Tipo INT(1) NOT NULL,
    Descripcion VARCHAR(30) NOT NULL,
    Hora_Inicio TIME NOT NULL,
    Hora_Fin TIME NOT NULL,
    FOREIGN KEY (ID_Tipo) REFERENCES Tipo_Horario(ID_Tipo)
);

DROP TABLE IF EXISTS `Ventanillas`;
CREATE TABLE Ventanillas (
    ID_Ventanilla INT(6) AUTO_INCREMENT PRIMARY KEY,
    Ventanilla VARCHAR(30) NOT NULL,
    ID_Sector INT(1) NOT NULL,
    FOREIGN KEY (ID_Sector) REFERENCES Sectores(ID_Sector)
);

DROP TABLE IF EXISTS `Empleado`;
CREATE TABLE Empleado (
    ID_Empleado INT(6) NOT NULL AUTO_INCREMENT PRIMARY KEY,
    ID_ROL INT(1) NOT NULL,
    nombre1 VARCHAR(20) NOT NULL,
    nombre2 VARCHAR(20) NOT NULL DEFAULT '',
    Apellido1 VARCHAR(20) NOT NULL,
    Apellido2 VARCHAR(20) NOT NULL DEFAULT '',
    Usuario VARCHAR(20) NOT NULL UNIQUE,
    Passwd VARCHAR(70) NOT NULL,
    ID_Estado INT(1) NOT NULL,
    FOREIGN KEY (ID_ROL) REFERENCES Rol(ID_Rol),
    FOREIGN KEY (ID_Estado) REFERENCES Estado_Empleado(ID_Estado)
);


/* Tablas con Dependencias Múltiples */
-- -----------------------------------------------------

DROP TABLE IF EXISTS `Empleado_Horario`;
CREATE TABLE Empleado_Horario (
    ID_Registro INT(6) NOT NULL AUTO_INCREMENT PRIMARY KEY,
    ID_Horario INT(6) NOT NULL,
    ID_Empleado INT(6) NOT NULL,
    Fecha_Inicio_Ausencia DATETIME NOT NULL,
    Fecha_Final_Ausencia DATETIME NOT NULL,
    FOREIGN KEY (ID_Horario) REFERENCES Horarios(ID_Horario),
    FOREIGN KEY (ID_Empleado) REFERENCES Empleado(ID_Empleado)
);

DROP TABLE IF EXISTS `Empleado_Ventanilla`;
CREATE TABLE Empleado_Ventanilla (
    ID_Asignacion INT(6) NOT NULL AUTO_INCREMENT PRIMARY KEY,
    ID_Empleado INT(6) NOT NULL,
    ID_Ventanilla INT(6) NOT NULL,
    Fecha_Inicio DATETIME NOT NULL,
    Fecha_Termino DATETIME,
    ID_Estado INT(1) NOT NULL,
    FOREIGN KEY (ID_Empleado) REFERENCES Empleado(ID_Empleado),
    FOREIGN KEY (ID_Ventanilla) REFERENCES Ventanillas(ID_Ventanilla),
    FOREIGN KEY (ID_Estado) REFERENCES Estado_empleado_ventanilla(ID_Estado)
);

DROP TABLE IF EXISTS `Turno`;
CREATE TABLE Turno (
    ID_Turno INT(6) NOT NULL AUTO_INCREMENT PRIMARY KEY,
    ID_Alumno INT(6) NOT NULL,
    ID_Ventanilla INT(6),
    Fecha_Ticket DATETIME NOT NULL,
    Folio VARCHAR(6) NOT NULL,
    ID_Estados INT(1) NOT NULL,
    FOREIGN KEY (ID_Alumno) REFERENCES Alumnos(ID_Alumno),
    FOREIGN KEY (ID_Ventanilla) REFERENCES Ventanillas(ID_Ventanilla),
    FOREIGN KEY (ID_Estados) REFERENCES Estados_Turno(ID_Estado)
);

DROP TABLE IF EXISTS `Turno_Invitado`;
CREATE TABLE Turno_Invitado (
    ID_TurnoInvitado INT(6) NOT NULL AUTO_INCREMENT PRIMARY KEY,
    ID_Ventanilla INT(6),
    Fecha_Ticket DATETIME NOT NULL,
    Folio_Invitado VARCHAR(6) NOT NULL,
    ID_Estados INT(1) NOT NULL,
    FOREIGN KEY (ID_Ventanilla) REFERENCES Ventanillas(ID_Ventanilla),
    FOREIGN KEY (ID_Estados) REFERENCES Estados_Turno(ID_Estado)
);

/* ==============================================
    INSERTS INICIALES - TurnosUal
============================================== */

/* ====== 1. Roles ====== */
INSERT INTO Rol (Rol) VALUES 
('Admin'), 
('Operador Cajas'), 
('Operador Ventanillas'), 
("Operador Becas");

/* ====== 2. Sectores ====== */
INSERT INTO Sectores (Sector) VALUES 
('Cajas'),
('Becas'),
('Servicios Escolares');

/* ====== 3. Estado_Empleado ====== */
INSERT INTO Estado_Empleado (Nombre) VALUES
('Activo'),
('Suspendido'),
('Despedido'),
('Inactivo');

/* ====== 4. Estado_empleado_ventanilla ====== */
INSERT INTO Estado_empleado_ventanilla (Nombre) VALUES
('Activo'),
('Inactivo');

/* ====== 5. Estados_Turno ====== */
INSERT INTO Estados_Turno (Nombre) VALUES
('Pendiente'),
('Cancelado'),
('Activo'),
('Atendido');

/* ====== 6. Tipo_Horario ====== */
INSERT INTO Tipo_Horario (Nombre) VALUES
('Semanal'),
('Sabatino');

/* ====== 7. Horarios ====== */
INSERT INTO Horarios (ID_Tipo, Descripcion, Hora_Inicio, Hora_Fin) VALUES
(1, 'Horario Administrativo', '08:00:00', '17:00:00'),
(2, 'Horario Sabatino', '08:00:00', '14:00:00');

/* ====== 8. Ventanillas ====== */
/* 4 Cajas, 1 Becas, 4 Servicios Escolares */
INSERT INTO Ventanillas (Ventanilla, ID_Sector) VALUES
('Caja1', 1),
('Caja2', 1),
('Caja3', 1),
('Caja4', 1),
('Beca1', 2),
('ServiciosEscolares1', 3),
('ServiciosEscolares2', 3),
('ServiciosEscolares3', 3),
('ServiciosEscolares4', 3);

/* ====== 9. Empleado (Admin) ====== */
/* Estado = Activo */
INSERT INTO Empleado (ID_ROL, nombre1, nombre2, Apellido1, Apellido2, Usuario, Passwd, ID_Estado)
VALUES (1, 'Luis', '', 'Rivera', '', 'admin', SHA2('12345', 256), 1);

/* ====== 10. Alumnos ====== */
INSERT INTO Alumnos (nombre1, nombre2, Apellido1, Apellido2, Carrera, Matricula) VALUES
('Carlos', 'Eduardo', 'Ramirez', 'Lopez', 'ISC', '28385'),
('Ana', 'Maria', 'Torres', 'Jimenez', 'LAE', '28381'),
('Jorge', '', 'Martinez', 'Santos', 'ARQ', '28313'),
('Lucia', 'Fernanda', 'Mendez', 'Perez', 'LANG', '24355');