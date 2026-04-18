--  ==========================================================================
--  Artifact:   taqueria.sql
--  Version:    1.0
--  Date:       2026-03-02 14:00:00
--  Authors:     Diego Landeros Bolaños, Estefania Isabel Arellano Martinez, Gilberto Sanchez Perez y
-- 				Erick Missael Perez de la Torre
--  Emails:      82907@alumnos.utleon.edu.mx, 83075@alumnos.utleon.edu.mx, 85689@alumnos.utleon.edu.mx y
-- 				85816@alumnos.utleon.edu.mx
--  ==========================================================================
--  Comments:   Script SQL para la creación y gestión del sistema de una taqueria. 
--              Incluye la estructura relacional normalizada (eliminación de 
--              totales calculados y control de rendimientos), datos de prueba 
--              iniciales, configuración de usuarios/privilegios de MySQL, y un 
--              Procedimiento Almacenado transaccional (realizar_venta) que 
--              gestiona la deducción automática de inventario mediante 
--              explosión de materiales, integrando validación de existencias, 
--              manejo de excepciones, COMMIT y ROLLBACK.
--  ==========================================================================

DROP DATABASE IF EXISTS taqueria;
CREATE DATABASE taqueria;
USE taqueria;

-- =========================
-- PERSONAS, EMPLEADOS, ROLES, USUARIOS Y PROVEEDORES
-- =========================
CREATE TABLE personas(
    idPersona INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100),
    telefono VARCHAR(20),
    direccion VARCHAR(200)
);

CREATE TABLE empleados(
    idEmpleado INT AUTO_INCREMENT PRIMARY KEY,
    idPersona INT,
    puesto VARCHAR(50),
    salario DECIMAL(10,2),
    FOREIGN KEY(idPersona) REFERENCES personas(idPersona)
);

CREATE TABLE roles(
    idRol INT AUTO_INCREMENT PRIMARY KEY,
    nombreRol VARCHAR(50),
    descripcion VARCHAR(150)
);

CREATE TABLE usuarios(
    idUsuario INT AUTO_INCREMENT PRIMARY KEY,
    idEmpleado INT,
    email VARCHAR(100),
    password VARCHAR(255),
    idRol INT,
    estado VARCHAR(20) DEFAULT 'activo',
    FOREIGN KEY(idEmpleado) REFERENCES empleados(idEmpleado),
    FOREIGN KEY(idRol) REFERENCES roles(idRol)
);

CREATE TABLE proveedores(
    idProveedor INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100),
    telefono VARCHAR(20),
    direccion VARCHAR(200),
    estado VARCHAR(20) DEFAULT 'activo'
);

-- =========================
-- INSUMOS Y PRODUCTOS
-- =========================
CREATE TABLE insumos(
    idInsumo INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100),
    unidadCompra VARCHAR(50),
    unidadMinima VARCHAR(50),
    merma DECIMAL(5,2),
    stock DECIMAL(10,2),
    estado VARCHAR(20) DEFAULT 'activo'
);

CREATE TABLE productos(
    idProducto INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100),
    descripcion VARCHAR(200),
    precio DECIMAL(10,2),
    estado VARCHAR(20) DEFAULT 'activo'
);

-- =========================
-- RECETAS Y DETALLE RECETA (Observación 4)
-- =========================
CREATE TABLE recetas(
    idReceta INT AUTO_INCREMENT PRIMARY KEY,
    idProducto INT,
    descripcion TEXT,
    rendimientoPorcion INT COMMENT 'Especifica cuántas unidades o elementos produce esta receta',
    FOREIGN KEY(idProducto) REFERENCES productos(idProducto)
);

CREATE TABLE detalleReceta(
    idDetalleReceta INT AUTO_INCREMENT PRIMARY KEY,
    idReceta INT,
    idInsumo INT,
    cantidad DECIMAL(10,2) COMMENT 'Cantidad en unidad mínima',
    FOREIGN KEY(idReceta) REFERENCES recetas(idReceta),
    FOREIGN KEY(idInsumo) REFERENCES insumos(idInsumo)
);

-- =========================
-- COMPRAS (Observación 2)
-- =========================
CREATE TABLE compras(
    idCompra INT AUTO_INCREMENT PRIMARY KEY,
    idProveedor INT,
    idEmpleado INT,
    fecha DATE,
    FOREIGN KEY(idProveedor) REFERENCES proveedores(idProveedor),
    FOREIGN KEY(idEmpleado) REFERENCES empleados(idEmpleado)
);

CREATE TABLE detalleCompra(
    idDetalleCompra INT AUTO_INCREMENT PRIMARY KEY,
    idCompra INT,
    idInsumo INT,
    presentacionCompra VARCHAR(100) COMMENT 'Ej. Caja de 20kg, Galon, Costal',
    cantidad DECIMAL(10,2),
    precio DECIMAL(10,2),
    FOREIGN KEY(idCompra) REFERENCES compras(idCompra),
    FOREIGN KEY(idInsumo) REFERENCES insumos(idInsumo)
);

-- =========================
-- VENTAS (Observación 2)
-- =========================
CREATE TABLE ventas(
    idVenta INT AUTO_INCREMENT PRIMARY KEY,
    idEmpleado INT,
    fecha DATETIME,
    FOREIGN KEY(idEmpleado) REFERENCES empleados(idEmpleado)
);

CREATE TABLE detalleVenta(
    idDetalleVenta INT AUTO_INCREMENT PRIMARY KEY,
    idVenta INT,
    idProducto INT,
    cantidad INT,
    precio DECIMAL(10,2),
    FOREIGN KEY(idVenta) REFERENCES ventas(idVenta),
    FOREIGN KEY(idProducto) REFERENCES productos(idProducto)
);

-- =========================
-- REGISTRO DE MERMAS (Observación 1)
-- =========================
CREATE TABLE registroMermas(
    idMerma INT AUTO_INCREMENT PRIMARY KEY,
    idInsumo INT,
    idEmpleado INT,
    cantidad DECIMAL(10,2),
    tipoMerma ENUM('Cocción', 'Caducidad', 'Error humano', 'Otro'),
    motivo TEXT,
    fechaRegistro DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(idInsumo) REFERENCES insumos(idInsumo),
    FOREIGN KEY(idEmpleado) REFERENCES empleados(idEmpleado)
);

-- =========================
-- INSERCIÓN DE DATOS DE PRUEBA
-- =========================

INSERT INTO personas(nombre,telefono,direccion) VALUES
('Juan Perez','4771112233','Leon Guanajuato'),
('Maria Lopez','4775558899','Leon Guanajuato'),
('Carlos Ruiz','4777778899','Leon Guanajuato');

INSERT INTO empleados(idPersona,puesto,salario) VALUES
(1,'Administrador',12000),
(2,'Cajero',8000),
(3,'Cocinero',9000);

INSERT INTO roles(nombreRol,descripcion) VALUES
('Administrador','Control total del sistema'),
('Cajero','Gestiona ventas'),
('Cocina','Gestiona preparación');

INSERT INTO usuarios(idEmpleado,email,password,idRol) VALUES
(1,'admin@taqueria.com','12345',1),
(2,'cajero@taqueria.com','12345',2),
(3,'cocina@taqueria.com','12345',3);

INSERT INTO proveedores(nombre,telefono,direccion) VALUES
('Carnes San Juan','4772223344','Mercado Abastos'),
('Verduras El Campo','4773334455','Central de Abastos'),
('Tortilleria La Tradicional','4774445566','Zona Centro');

INSERT INTO insumos(nombre,unidadCompra,unidadMinima,merma,stock) VALUES
('Carne Pastor','kg','gramos',5,10000),
('Cebolla','kg','gramos',3,5000),
('Cilantro','kg','gramos',2,2000),
('Tortilla','paquete','pieza',0,500),
('Piña','pieza','gramos',10,1000);

INSERT INTO productos(nombre,descripcion,precio) VALUES
('Taco al Pastor','Taco con carne al pastor',18),
('Gringa','Tortilla con queso y carne',35),
('Quesadilla','Quesadilla con carne',30),
('Refresco','Bebida 600ml',20);

-- Se añade el rendimientoPorcion
INSERT INTO recetas(idProducto,descripcion, rendimientoPorcion) VALUES
(1,'Receta taco pastor', 1),
(2,'Receta gringa', 1),
(3,'Receta quesadilla', 1);

INSERT INTO detalleReceta(idReceta,idInsumo,cantidad) VALUES
(1,1,150),
(1,2,30),
(1,3,10),
(1,4,1),
(1,5,20),
(2,1,200),
(2,4,2),
(2,2,20),
(3,1,120),
(3,4,1);

-- Se remueve el "total"
INSERT INTO compras(idProveedor,idEmpleado,fecha) VALUES
(1,1,'2026-03-15'),
(2,1,'2026-03-15'),
(3,1,'2026-03-15');

-- Se añade la "presentacionCompra"
INSERT INTO detalleCompra(idCompra,idInsumo,presentacionCompra,cantidad,precio) VALUES
(1,1,'Caja de 10kg',10,150),
(2,2,'Costal de 5kg',5,50),
(2,3,'Manojo',3,30),
(3,4,'Paquete de 1kg',200,2);

-- Se remueve el "total"
INSERT INTO ventas(idEmpleado,fecha) VALUES
(2,NOW()),
(2,NOW());

INSERT INTO detalleVenta(idVenta,idProducto,cantidad,precio) VALUES
(1,1,4,18),
(1,4,2,20),
(2,2,2,35);

INSERT INTO registroMermas(idInsumo, idEmpleado, cantidad, tipoMerma, motivo) VALUES
(1, 3, 500, 'Cocción', 'Se quemó una porción de carne al pastor en la plancha'),
(2, 3, 200, 'Caducidad', 'Cebolla en mal estado retirada antes de picar'),
(4, 3, 15, 'Error humano', 'Tortillas rotas al calentar');

-- =========================
-- ÍNDICES Y CONSULTAS DE PRUEBA
-- =========================

CREATE INDEX idx_ventas_fecha ON ventas(fecha);
CREATE INDEX idx_detalleVenta_producto ON detalleVenta(idProducto);
CREATE INDEX idx_merma_fecha ON registroMermas(fechaRegistro);

SELECT nombre, stock FROM insumos WHERE estado = 'activo';
SELECT nombre, precio FROM productos WHERE estado = 'activo';

-- Nueva consulta calculada para obtener el total de ventas del día mediante JOIN
SELECT SUM(dv.cantidad * dv.precio) AS totalVentasDelDia 
FROM ventas v 
JOIN detalleVenta dv ON v.idVenta = dv.idVenta 
WHERE DATE(v.fecha) = CURDATE();

-- =======================================================
-- SEGURIDAD: CREACIÓN DE USUARIOS DE MYSQL Y PRIVILEGIOS
-- =======================================================

DROP USER IF EXISTS 'adminDB'@'localhost';
CREATE USER 'adminDB'@'localhost' IDENTIFIED BY 'Admin123';
GRANT ALL PRIVILEGES ON taqueria.* TO 'adminDB'@'localhost';

DROP USER IF EXISTS 'operador1'@'localhost';
CREATE USER 'operador1'@'localhost' IDENTIFIED BY 'Operador123';
GRANT SELECT, INSERT, UPDATE ON taqueria.* TO 'operador1'@'localhost';

DROP USER IF EXISTS 'consulta1'@'localhost';
CREATE USER 'consulta1'@'localhost' IDENTIFIED BY 'Consulta123';
GRANT SELECT ON taqueria.* TO 'consulta1'@'localhost';
-- Este si se creo en Proyecto 3
DROP USER IF EXISTS 'backupUser'@'localhost';
CREATE USER 'backupUser'@'localhost' IDENTIFIED BY 'Backup123';
GRANT SELECT, LOCK TABLES, SHOW VIEW ON taqueria.* TO 'backupUser'@'localhost';

FLUSH PRIVILEGES;
-- =======================================================
-- STP 
-- =======================================================
USE taqueria;

DELIMITER //

CREATE PROCEDURE realizar_venta(
    IN p_idEmpleado INT, 
    IN p_idProducto INT, 
    IN p_cantidad INT
)
BEGIN
    -- 1. Si la base de datos detecta un error, aborta todo.
    DECLARE EXIT HANDLER FOR SQLEXCEPTION 
    BEGIN
        ROLLBACK; 
        SELECT 'Error de base de datos: Transacción cancelada (Rollback automático)' AS Resultado;
    END;

    -- 2. Iniciamos el bloque seguro.
    START TRANSACTION;

    -- 3. Revisamos si ALGÚN insumo de la receta no alcanza para la cantidad pedida.
    IF EXISTS (
        SELECT 1 FROM detalleReceta dr
        JOIN insumos i ON dr.idInsumo = i.idInsumo
        JOIN recetas r ON dr.idReceta = r.idReceta
        WHERE r.idProducto = p_idProducto 
        AND i.stock < (dr.cantidad * p_cantidad)
    ) THEN
        -- Si falta stock, cancelamos y avisamos
        ROLLBACK;
        SELECT 'Venta rechazada: No hay ingredientes suficientes en el inventario' AS Resultado;
    ELSE
        -- 4. Insertamos la venta y su detalle directamente
        INSERT INTO ventas(idEmpleado, fecha) VALUES (p_idEmpleado, NOW());
        
        INSERT INTO detalleVenta(idVenta, idProducto, cantidad, precio) 
        VALUES (LAST_INSERT_ID(), p_idProducto, p_cantidad, (SELECT precio FROM productos WHERE idProducto = p_idProducto));
        
        -- 5. Restamos los ingredientes exactos de la receta
        UPDATE insumos i
        JOIN detalleReceta dr ON i.idInsumo = dr.idInsumo
        JOIN recetas r ON dr.idReceta = r.idReceta
        SET i.stock = i.stock - (dr.cantidad * p_cantidad)
        WHERE r.idProducto = p_idProducto;

        -- 6. Confirmamos que todos los pasos se hicieron bien
        COMMIT;
        SELECT 'Éxito: Venta registrada y stock descontado correctamente' AS Resultado;
    END IF;

END //

DELIMITER ;

-- Queremos vender 2 Tacos al Pastor (idProducto = 1) hechos por el Cajero (idEmpleado = 2)
CALL realizar_venta(2, 1, 2);

-- Verificamos la tabla de insumos para confirmar que se restaron los gramos exactos de la receta
SELECT * FROM insumos;