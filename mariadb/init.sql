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

/* Tablas con Dependencias Simples */
-- -----------------------------------------------------

DROP TABLE IF EXISTS `Ventanillas`;

CREATE TABLE Ventanillas (
    ID_Ventanilla INT(1) AUTO_INCREMENT PRIMARY KEY,
    Ventanilla VARCHAR(30) NOT NULL,
    ID_Sector INT(1) NOT NULL,
    FOREIGN KEY (ID_Sector) REFERENCES Sectores (ID_Sector)
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
    ID_Sector INT(1) DEFAULT NULL,
    FOREIGN KEY (ID_ROL) REFERENCES Rol (ID_Rol),
    FOREIGN KEY (ID_Estado) REFERENCES Estado_Empleado (ID_Estado),
    FOREIGN KEY (ID_Sector) REFERENCES Sectores (ID_Sector)
);

/* Tablas con Dependencias Múltiples */
-- -----------------------------------------------------

DROP TABLE IF EXISTS `Empleado_Ventanilla`;

CREATE TABLE Empleado_Ventanilla (
    ID_Asignacion INT(6) NOT NULL AUTO_INCREMENT PRIMARY KEY,
    ID_Empleado INT(6) NOT NULL,
    ID_Ventanilla INT(1) NOT NULL,
    Fecha_Inicio DATETIME NOT NULL,
    Fecha_Termino DATETIME,
    ID_Estado INT(1) NOT NULL,
    FOREIGN KEY (ID_Empleado) REFERENCES Empleado (ID_Empleado),
    FOREIGN KEY (ID_Ventanilla) REFERENCES Ventanillas (ID_Ventanilla),
    FOREIGN KEY (ID_Estado) REFERENCES Estado_empleado_ventanilla (ID_Estado)
);

DROP TABLE IF EXISTS `Turno`;

CREATE TABLE Turno (
    ID_Turno INT(6) NOT NULL AUTO_INCREMENT PRIMARY KEY,
    ID_Sector INT(1) NOT NULL,
    ID_Ventanilla INT(6),
    Fecha_Ticket DATETIME(6) NOT NULL,
    Folio VARCHAR(6) NOT NULL,
    ID_Estados INT(1) NOT NULL,
    Fecha_Ultimo_Estado DATETIME(3) NOT NULL,
    FOREIGN KEY (ID_Sector) REFERENCES Sectores (ID_Sector),
    FOREIGN KEY (ID_Ventanilla) REFERENCES Ventanillas (ID_Ventanilla),
    FOREIGN KEY (ID_Estados) REFERENCES Estados_Turno (ID_Estado)
);

DROP TABLE IF EXISTS `Rol_Ventanilla`;

CREATE TABLE Rol_Ventanilla (
    ID_Rol INT(1),
    ID_Ventanilla INT(1),
    PRIMARY KEY (ID_Rol, ID_Ventanilla),
    FOREIGN KEY (ID_Ventanilla) REFERENCES Ventanillas (ID_Ventanilla),
    FOREIGN KEY (ID_ROL) REFERENCES Rol (ID_Rol)
);

/* ==============================================
INSERTS INICIALES - TurnosUal
============================================== */

/* ====== 1. Roles ====== */
INSERT INTO
    Rol (Rol)
VALUES ('Admin'),
    ('Operador Cajas'),
    ('Operador Becas'),
    (
        "Operador Servicios Escolares"
    ),
    ("Operador Tesoreria"),
    ('Jefe de Departamento');

/* ====== 2. Sectores ====== */
INSERT INTO Sectores (Sector) VALUES 
('Cajas'),
    ('Becas'),
    ('Servicios Escolares'),
    ('Tesoreria');

/* ====== 3. Estado_Empleado ====== */
INSERT INTO Estado_Empleado (Nombre) VALUES
('Activo'),
    ('Descanso'),
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
    ('Atendiendo'),
    ('Completado');

/* ====== 6. Ventanillas ====== */
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
('ServiciosEscolares4', 3),
('Tesoreria1', 4);

/* ====== 7. Empleado (Admin) ====== */
/* Estado = Activo */
INSERT INTO Empleado (ID_ROL, nombre1, nombre2, Apellido1, Apellido2, Usuario, Passwd, ID_Estado)
VALUES 
(1, 'Luis', '', 'Rivera', '', 'admin', SHA2('12345678', 256), 1),
(2, 'Luis', '', 'Rivera', 'Gamez', 'Fur1us', SHA2('12345678', 256), 1),
(2, 'Gabriel', '', 'Ortiz', '', 'itzumi', SHA2('12345678', 256), 1),
(3, 'Salvador', '', 'Butanda', '', 'python', SHA2('12345678', 256), 1),
(4, 'Cristian', '', 'Butanda', '', 'butanda', SHA2('12345678', 256), 1),
(2, 'Jose', 'Antonio', 'Zenil', 'Ruiz', 'antoniozr', SHA2('12345678', 256), 1),
(5, 'Jaime', '', 'Mendez', '', 'jaime', SHA2('12345678', 256), 1);

/* ====== 8. Rol_Ventanilla ====== */
INSERT INTO Rol_Ventanilla (ID_Rol, ID_Ventanilla) VALUES
    -- Operador Cajas (Rol 2) tiene acceso a las 4 cajas
(2, 1),  -- Caja1
(2, 2),  -- Caja2
(2, 3),  -- Caja3
(2, 4),  -- Caja4

-- Operador Becas (Rol 3) tiene acceso solo a Beca1
(3, 5),  -- Beca1

-- Operador Servicios Escolares (Rol 4) tiene acceso a las 4 ventanillas
(4, 6),  -- ServiciosEscolares1
(4, 7),  -- ServiciosEscolares2
(4, 8),  -- ServiciosEscolares3
(4, 9),  -- ServiciosEscolares4

-- Operador Tesoreria (Rol 5) tiene acceso a la ventanilla de Tesoreria
(5, 10); -- Tesoreria1