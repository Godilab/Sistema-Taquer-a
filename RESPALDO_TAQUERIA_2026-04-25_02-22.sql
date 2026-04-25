
;
;
;
;
;
;
;
;
;
;
DROP TABLE IF EXISTS `clientes`;
;
;
CREATE TABLE `clientes` (
  `idCliente` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `correo` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `telefono` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `verificado` tinyint(1) DEFAULT '0',
  `codigo_verificacion` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`idCliente`),
  UNIQUE KEY `correo` (`correo`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
;

LOCK TABLES `clientes` WRITE;
/*!40000 ALTER TABLE `clientes` DISABLE KEYS */;
INSERT INTO `clientes` VALUES (1,'Diego','diegolanderosbolanos@hotmail.com','scrypt:32768:8:1$co0DyVDMOybiUwf4$5b3587d6c176ae0c3b269adf5620745ddd91cc4ef3652cc1fcf675f44f9a7209fcfcfcf8d4730ead6914743b19a46e5e6195a26acac606dec5c02f33f24e7a5c','4772381218',1,NULL);
/*!40000 ALTER TABLE `clientes` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `compras`;
;
;
CREATE TABLE `compras` (
  `idCompra` int NOT NULL AUTO_INCREMENT,
  `idProveedor` int DEFAULT NULL,
  `idEmpleado` int DEFAULT NULL,
  `fecha` date DEFAULT NULL,
  `total` decimal(10,2) DEFAULT NULL,
  `notas` text,
  `idCorte` int DEFAULT NULL,
  PRIMARY KEY (`idCompra`),
  KEY `idProveedor` (`idProveedor`),
  KEY `idEmpleado` (`idEmpleado`),
  KEY `fk_compras_cortecaja` (`idCorte`),
  CONSTRAINT `compras_ibfk_1` FOREIGN KEY (`idProveedor`) REFERENCES `proveedores` (`idProveedor`),
  CONSTRAINT `compras_ibfk_2` FOREIGN KEY (`idEmpleado`) REFERENCES `empleados` (`idEmpleado`),
  CONSTRAINT `fk_compras_cortecaja` FOREIGN KEY (`idCorte`) REFERENCES `cortes_caja` (`idCorte`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
;

LOCK TABLES `compras` WRITE;
/*!40000 ALTER TABLE `compras` DISABLE KEYS */;
INSERT INTO `compras` VALUES (1,1,1,'2026-03-05',4200.00,'Compra inicial de carne (Tripa/Bistec)',NULL),(2,3,1,'2026-04-02',1100.00,'Insumos indirectos (Escenario 6)',NULL),(3,1,NULL,'2026-04-25',25000.00,'',NULL),(4,1,NULL,'2026-04-25',5000.00,'',NULL),(5,1,NULL,'2026-04-25',2500.00,'',NULL),(6,3,NULL,'2026-04-25',250.00,'',NULL),(9,3,NULL,'2026-04-25',500.00,'',NULL);
/*!40000 ALTER TABLE `compras` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `cortes_caja`;
;
;
CREATE TABLE `cortes_caja` (
  `idCorte` int NOT NULL AUTO_INCREMENT,
  `idEmpleado` int DEFAULT NULL,
  `fecha` datetime DEFAULT CURRENT_TIMESTAMP,
  `monto_inicial` decimal(10,2) NOT NULL,
  `ingresos_ventas` decimal(10,2) DEFAULT '0.00',
  `egresos_compras` decimal(10,2) DEFAULT '0.00',
  `monto_final_esperado` decimal(10,2) DEFAULT NULL,
  `monto_real` decimal(10,2) DEFAULT NULL,
  `diferencia` decimal(10,2) DEFAULT NULL,
  `estado` enum('abierto','cerrado') DEFAULT 'abierto',
  PRIMARY KEY (`idCorte`),
  KEY `fk_cortecaja_empleado` (`idEmpleado`),
  CONSTRAINT `fk_cortecaja_empleado` FOREIGN KEY (`idEmpleado`) REFERENCES `empleados` (`idEmpleado`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
;

LOCK TABLES `cortes_caja` WRITE;
/*!40000 ALTER TABLE `cortes_caja` DISABLE KEYS */;
/*!40000 ALTER TABLE `cortes_caja` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `detalle_compras`;
;
;
CREATE TABLE `detalle_compras` (
  `idDetalle` int NOT NULL AUTO_INCREMENT,
  `idCompra` int DEFAULT NULL,
  `idInsumo` int DEFAULT NULL,
  `cantidad` decimal(10,2) DEFAULT NULL,
  `precio_unitario` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`idDetalle`),
  KEY `idCompra` (`idCompra`),
  KEY `idInsumo` (`idInsumo`),
  CONSTRAINT `detalle_compras_ibfk_1` FOREIGN KEY (`idCompra`) REFERENCES `compras` (`idCompra`),
  CONSTRAINT `detalle_compras_ibfk_2` FOREIGN KEY (`idInsumo`) REFERENCES `insumos` (`idInsumo`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
;

LOCK TABLES `detalle_compras` WRITE;
/*!40000 ALTER TABLE `detalle_compras` DISABLE KEYS */;
INSERT INTO `detalle_compras` VALUES (1,3,7,100.00,250.00),(2,4,7,20.00,250.00),(3,5,7,10.00,250.00),(4,6,4,10.00,25.00),(7,9,4,20.00,25.00);
/*!40000 ALTER TABLE `detalle_compras` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `detalle_pedido_online`;
;
;
CREATE TABLE `detalle_pedido_online` (
  `idDetalle` int NOT NULL AUTO_INCREMENT,
  `idPedido` int NOT NULL,
  `idProducto` int NOT NULL,
  `cantidad` int NOT NULL,
  `precio` decimal(10,2) NOT NULL,
  `opcion_preparacion` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`idDetalle`),
  KEY `fk_detalle_pedido_rel` (`idPedido`),
  KEY `fk_detalle_prod_rel` (`idProducto`),
  CONSTRAINT `fk_detalle_pedido_rel` FOREIGN KEY (`idPedido`) REFERENCES `pedidos_online` (`idPedido`) ON DELETE CASCADE,
  CONSTRAINT `fk_detalle_prod_rel` FOREIGN KEY (`idProducto`) REFERENCES `productos` (`idProducto`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
;

LOCK TABLES `detalle_pedido_online` WRITE;
/*!40000 ALTER TABLE `detalle_pedido_online` DISABLE KEYS */;
INSERT INTO `detalle_pedido_online` VALUES (2,2,9,6,20.00,'Con todo'),(3,3,2,1,35.00,'Con todo'),(4,3,4,1,30.00,'Normal'),(5,3,3,1,30.00,'Con todo'),(6,3,11,1,20.00,'Sin verdura'),(7,4,4,1,30.00,'Normal'),(8,5,4,1,30.00,'Normal'),(9,6,4,2,30.00,'Normal'),(10,7,9,1,20.00,'Con todo'),(11,7,11,1,20.00,'Con todo'),(12,8,4,1,30.00,'Normal'),(13,9,4,1,30.00,'Normal'),(14,10,4,1,30.00,'Normal'),(15,11,4,1,30.00,'Normal'),(16,12,4,4,30.00,''),(17,13,4,1,30.00,''),(18,14,4,4,30.00,'');
/*!40000 ALTER TABLE `detalle_pedido_online` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `detallereceta`;
;
;
CREATE TABLE `detallereceta` (
  `idDetalleReceta` int NOT NULL AUTO_INCREMENT,
  `idReceta` int DEFAULT NULL,
  `idInsumo` int DEFAULT NULL,
  `cantidad` decimal(10,2) DEFAULT NULL COMMENT 'Cantidad en unidad mÔö£├ÂÔö£├éÔö¼├║├ö├Â┬úÔö£├®Ôö£├ÂÔö£├éÔö¼├║├ö├Â┬úÔö£┬«Ôö£├ÂÔö£├éÔö¼ÔòØ├ö├Â┬ú├ö├▓├ª├ö├Â┬úÔö£├é├ö├Â┬úÔö£├®├ö├Â┬╝Ôö£ÔòæÔö£├ÂÔö£├éÔö¼├║Ôö£├ÂÔö£├éÔö£┬«├ö├Â┬úÔö£├é├ö├Â┬úÔö£├®├ö├Â┬╝Ôö£ÔòæÔö£├ÂÔö£├éÔö¼├║Ôö£├ÂÔö£ÔûôÔö£┬¬├ö├Â┬úÔö£├é├ö├Â┬úÔö£├®├ö├Â┬╝Ôö£ÔòæÔö£├ÂÔö£├éÔö¼├║├ö├Â┬úÔö£┬¬Ôö£├ÂÔö£├éÔö¼├║├ö├Â┬úÔö£├®Ôö£├ÂÔö£├éÔö¼├║├ö├Â┬úÔö£┬«Ôö£├ÂÔö£├éÔö¼ÔòØ├ö├Â┬ú├ö├▓├ª├ö├Â┬úÔö£├é├ö├Â┬úÔö£├®├ö├Â┬╝Ôö£ÔòæÔö£├ÂÔö£├éÔö¼ÔòØ├ö├Â┬╝Ôö¼┬óÔö£├ÂÔö£├éÔö¼├║├ö├Â┬úÔö£├®Ôö£├ÂÔö£├éÔö¼├║├ö├Â┬úÔö£┬«Ôö£├ÂÔö£├éÔö¼ÔòØÔö£├ÂÔö£ÔûôÔö£├┐├ö├Â┬úÔö£├é├ö├Â┬úÔö£├®├ö├Â┬╝├ö├▓├ÿÔö£├ÂÔö£├éÔö¼├║├ö├Â┬╝Ôö£┬ínima',
  `unidad` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`idDetalleReceta`),
  KEY `idReceta` (`idReceta`),
  KEY `idInsumo` (`idInsumo`),
  CONSTRAINT `detallereceta_ibfk_1` FOREIGN KEY (`idReceta`) REFERENCES `recetas` (`idReceta`),
  CONSTRAINT `detallereceta_ibfk_2` FOREIGN KEY (`idInsumo`) REFERENCES `insumos` (`idInsumo`)
) ENGINE=InnoDB AUTO_INCREMENT=73 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
;

LOCK TABLES `detallereceta` WRITE;
/*!40000 ALTER TABLE `detallereceta` DISABLE KEYS */;
INSERT INTO `detallereceta` VALUES (10,6,11,1.00,'pz'),(18,4,9,20.00,'gr'),(19,4,6,20.00,'gr'),(20,4,4,2.00,'pz'),(36,5,7,40.00,'gr'),(37,5,4,1.00,'pz'),(38,5,12,20.00,'gr'),(67,3,9,0.05,'gr'),(68,3,4,2.00,'pz'),(69,7,7,0.04,'gr'),(70,7,4,2.00,'pz'),(71,2,6,0.05,'gr'),(72,2,4,2.00,'pz');
/*!40000 ALTER TABLE `detallereceta` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `detalleventa`;
;
;
CREATE TABLE `detalleventa` (
  `idDetalleVenta` int NOT NULL AUTO_INCREMENT,
  `idVenta` int DEFAULT NULL,
  `idProducto` int DEFAULT NULL,
  `cantidad` int DEFAULT NULL,
  `precio` decimal(10,2) DEFAULT NULL,
  `costo_unitario` decimal(10,2) DEFAULT '0.00',
  `opcion` varchar(50) DEFAULT NULL,
  `opcion_preparacion` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`idDetalleVenta`),
  KEY `idVenta` (`idVenta`),
  KEY `idx_detalleVenta_producto` (`idProducto`),
  CONSTRAINT `detalleventa_ibfk_1` FOREIGN KEY (`idVenta`) REFERENCES `ventas` (`idVenta`),
  CONSTRAINT `detalleventa_ibfk_2` FOREIGN KEY (`idProducto`) REFERENCES `productos` (`idProducto`)
) ENGINE=InnoDB AUTO_INCREMENT=86 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
;

LOCK TABLES `detalleventa` WRITE;
/*!40000 ALTER TABLE `detalleventa` DISABLE KEYS */;
INSERT INTO `detalleventa` VALUES (1,1,8,30,27.00,10.50,NULL,NULL),(2,1,3,13,30.00,12.00,NULL,NULL),(3,2,9,38,25.00,8.50,NULL,NULL),(4,3,10,84,25.00,9.80,NULL,NULL),(5,4,8,50,27.00,10.50,NULL,NULL),(6,4,3,16,30.00,12.00,NULL,NULL),(7,5,11,600,20.00,0.00,'Con verdura',NULL),(8,7,9,6,20.00,0.00,NULL,'Con todo'),(11,10,11,1,20.00,0.00,NULL,'Con todo'),(15,14,9,6,20.00,0.00,NULL,'Con todo'),(16,15,2,1,35.00,0.00,NULL,'Con todo'),(17,15,4,1,30.00,0.00,NULL,'Normal'),(18,15,3,1,30.00,0.00,NULL,'Con todo'),(19,15,11,1,20.00,0.00,NULL,'Sin verdura'),(20,16,2,1,35.00,0.00,NULL,'Con todo'),(21,16,4,1,30.00,0.00,NULL,'Normal'),(22,16,3,1,30.00,0.00,NULL,'Con todo'),(23,16,11,1,20.00,0.00,NULL,'Sin verdura'),(24,17,4,1,30.00,0.00,NULL,'Normal'),(25,18,4,1,30.00,0.00,NULL,'Normal'),(26,19,4,1,30.00,0.00,NULL,'Normal'),(27,20,4,1,30.00,0.00,NULL,'Normal'),(28,21,4,2,30.00,0.00,NULL,'Normal'),(29,22,4,1,30.00,0.00,NULL,''),(30,23,10,1,22.00,0.00,NULL,'Con todo'),(31,23,4,1,30.00,0.00,NULL,''),(32,24,9,1,20.00,0.00,NULL,'Con todo'),(33,24,11,1,20.00,0.00,NULL,'Con todo'),(34,25,10,1,22.00,0.00,NULL,'Con todo'),(35,26,4,1,30.00,0.00,NULL,'Normal'),(36,27,4,1,30.00,0.00,NULL,''),(37,28,4,1,30.00,0.00,NULL,''),(38,29,4,1,30.00,0.00,NULL,''),(39,30,4,1,30.00,0.00,NULL,''),(40,31,4,1,30.00,0.00,NULL,''),(41,32,4,1,30.00,0.00,NULL,''),(42,33,4,4,30.00,0.00,NULL,''),(43,34,4,1,30.00,0.00,NULL,''),(44,35,4,1,30.00,0.00,NULL,''),(45,36,4,1,30.00,0.00,NULL,''),(46,37,4,2,30.00,0.00,NULL,''),(47,38,4,1,30.00,0.00,NULL,''),(48,39,4,1,30.00,0.00,NULL,''),(49,40,4,1,30.00,0.00,NULL,''),(50,41,4,1,30.00,0.00,NULL,''),(51,42,4,4,30.00,0.00,NULL,''),(52,43,4,1,30.00,0.00,NULL,''),(53,44,4,1,30.00,0.00,NULL,''),(54,44,11,1,20.00,0.00,NULL,'Con todo'),(55,45,4,1,30.00,0.00,NULL,''),(56,45,8,1,22.00,0.00,NULL,'Con todo'),(57,46,4,4,30.00,0.00,NULL,''),(58,46,8,1,22.00,0.00,NULL,'Con todo'),(59,47,11,1,20.00,0.00,NULL,'Con todo'),(60,48,4,1,30.00,0.00,NULL,''),(61,48,10,1,22.00,0.00,NULL,'Con todo'),(62,48,11,1,20.00,0.00,NULL,'Con todo'),(63,49,4,1,30.00,0.00,NULL,''),(64,49,11,1,20.00,0.00,NULL,'Con todo'),(65,49,8,1,22.00,0.00,NULL,'Con todo'),(66,50,4,1,30.00,0.00,NULL,''),(67,51,4,1,30.00,0.00,NULL,''),(68,52,4,1,30.00,0.00,NULL,''),(69,53,4,1,30.00,0.00,NULL,''),(70,54,4,1,30.00,0.00,NULL,''),(71,55,4,2,30.00,0.00,NULL,''),(72,56,4,2,30.00,0.00,NULL,''),(73,57,4,1,30.00,0.00,NULL,''),(74,58,4,1,30.00,0.00,NULL,''),(75,59,11,1,20.00,0.00,NULL,'Con todo'),(76,60,4,1,30.00,0.00,NULL,''),(77,61,4,1,30.00,0.00,NULL,''),(78,62,4,1,30.00,0.00,NULL,''),(79,63,11,1,20.00,0.00,NULL,'Con todo'),(80,64,4,1,30.00,0.00,NULL,''),(81,65,9,1,20.00,0.00,NULL,'Con todo'),(82,66,9,5,20.00,0.00,NULL,'Con todo'),(83,67,9,10,20.00,0.00,NULL,'Con todo'),(84,68,9,10,20.00,0.00,NULL,'Con todo'),(85,69,9,1,20.00,0.00,NULL,'Con todo');
/*!40000 ALTER TABLE `detalleventa` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `empleados`;
;
;
CREATE TABLE `empleados` (
  `idEmpleado` int NOT NULL AUTO_INCREMENT,
  `idPersona` int DEFAULT NULL,
  `puesto` varchar(50) DEFAULT NULL,
  `salario` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`idEmpleado`),
  KEY `idPersona` (`idPersona`),
  CONSTRAINT `empleados_ibfk_1` FOREIGN KEY (`idPersona`) REFERENCES `personas` (`idPersona`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
;

LOCK TABLES `empleados` WRITE;
/*!40000 ALTER TABLE `empleados` DISABLE KEYS */;
INSERT INTO `empleados` VALUES (1,1,'Administrador',12000.00),(2,2,'Cajero',8000.00),(3,3,'Cocinero',9000.00),(4,4,'admin',NULL),(5,5,'encargado',NULL),(6,6,'admin',NULL),(7,7,'admin',NULL),(8,8,'Encargado',NULL),(9,9,'Administrador',NULL),(10,10,'Cajero',NULL),(11,11,'Cajero de Mostrador',NULL),(12,12,'Jefe de Cocina',NULL),(13,13,'Cocina',NULL);
/*!40000 ALTER TABLE `empleados` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `equivalencias`;
;
;
CREATE TABLE `equivalencias` (
  `idEquivalencia` int NOT NULL AUTO_INCREMENT,
  `idInsumo` int NOT NULL,
  `unidadConsumo` varchar(20) NOT NULL,
  `cantidadEquivalente` decimal(10,4) NOT NULL,
  PRIMARY KEY (`idEquivalencia`),
  KEY `idInsumo` (`idInsumo`),
  CONSTRAINT `equivalencias_ibfk_1` FOREIGN KEY (`idInsumo`) REFERENCES `insumos` (`idInsumo`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
;

LOCK TABLES `equivalencias` WRITE;
/*!40000 ALTER TABLE `equivalencias` DISABLE KEYS */;
/*!40000 ALTER TABLE `equivalencias` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `insumos`;
;
;
CREATE TABLE `insumos` (
  `idInsumo` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) DEFAULT NULL,
  `unidadCompra` varchar(50) DEFAULT NULL,
  `unidadMinima` varchar(50) DEFAULT NULL,
  `merma` decimal(5,2) DEFAULT NULL,
  `stock` decimal(10,3) DEFAULT NULL,
  `estado` varchar(20) DEFAULT 'activo',
  `categoria` varchar(50) DEFAULT 'Otros',
  `stockMinimo` decimal(10,2) DEFAULT '0.00',
  `costoUnidad` decimal(10,2) DEFAULT '0.00',
  `proveedor` varchar(100) DEFAULT 'Desconocido',
  PRIMARY KEY (`idInsumo`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
;

LOCK TABLES `insumos` WRITE;
/*!40000 ALTER TABLE `insumos` DISABLE KEYS */;
INSERT INTO `insumos` VALUES (2,'Cebolla','kg','kg',1.00,10.000,'activo','Verduras',5.00,15.00,'Verduras El Campo'),(3,'Cilantro','kg','kg',0.90,10.000,'activo','Verduras',5.00,15.00,'Verduras El Campo'),(4,'Tortilla','kg','pieza',40.00,20.000,'activo','Tortillas',7.00,25.00,'Tortilleria La Tradicional'),(5,'PiÔö£ÔûÆa','kg','kg',0.70,40.000,'activo','Verduras',5.00,20.00,'Verduras El Campo'),(6,'Tripa','kg','kg',0.60,21.290,'activo','Carnes',10.00,110.00,''),(7,'Bistec','kg','kg',0.75,166.120,'activo','',5.00,250.00,'Carnes San Juan'),(8,'Tortilla de Harina','kg','pza',30.00,6.000,'activo','Tortillas',5.00,25.00,'Tortilleria La Tradicional'),(9,'Chorizo','kg','kg',0.85,23.240,'activo','Carnes',5.00,90.00,'Carnes San Juan'),(10,'Limones','kg','kg',1.00,15.000,'activo','Verduras',5.00,15.00,'Verduras El Campo'),(11,'Refresco','pz','pz',1.00,11.000,'activo','Bebidas',10.00,12.00,'Verduras El Campo'),(12,'Queso','kg','kg',1.00,15.240,'activo','Otros',5.00,120.00,'Carnes San Juan'),(13,'Chorizo','kg','',1.00,23.290,'activo','Carnes',5.00,90.00,'Carnes San Juan');
/*!40000 ALTER TABLE `insumos` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `login_security`;
;
;
CREATE TABLE `login_security` (
  `idSecurity` int NOT NULL AUTO_INCREMENT,
  `idUsuario` int NOT NULL,
  `intentos_fallidos` int DEFAULT '0',
  `ultimo_intento` datetime DEFAULT NULL,
  `bloqueado_hasta` datetime DEFAULT NULL,
  `ip_address` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`idSecurity`),
  KEY `idUsuario` (`idUsuario`),
  CONSTRAINT `login_security_ibfk_1` FOREIGN KEY (`idUsuario`) REFERENCES `usuarios` (`idUsuario`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
;

LOCK TABLES `login_security` WRITE;
/*!40000 ALTER TABLE `login_security` DISABLE KEYS */;
/*!40000 ALTER TABLE `login_security` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `pedidos_online`;
;
;
CREATE TABLE `pedidos_online` (
  `idPedido` int NOT NULL AUTO_INCREMENT,
  `idCliente` int NOT NULL,
  `nombre_cliente` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `telefono` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `direccion` text COLLATE utf8mb4_unicode_ci,
  `total` decimal(10,2) DEFAULT NULL,
  `metodo_pago` enum('efectivo','tarjeta') COLLATE utf8mb4_unicode_ci DEFAULT 'efectivo',
  `estado_pago` enum('pendiente','pagado') COLLATE utf8mb4_unicode_ci DEFAULT 'pendiente',
  `estado` enum('pendiente','en_preparacion','en_camino','entregado','cancelado') COLLATE utf8mb4_unicode_ci DEFAULT 'pendiente',
  `fecha` datetime DEFAULT CURRENT_TIMESTAMP,
  `idVenta` int DEFAULT NULL,
  PRIMARY KEY (`idPedido`),
  KEY `fk_pedido_cliente_online` (`idCliente`),
  CONSTRAINT `fk_pedido_cliente_online` FOREIGN KEY (`idCliente`) REFERENCES `clientes` (`idCliente`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
;

LOCK TABLES `pedidos_online` WRITE;
/*!40000 ALTER TABLE `pedidos_online` DISABLE KEYS */;
INSERT INTO `pedidos_online` VALUES (2,1,'Diego','4772381218','Puerto De Chetumal 407, Granjas Económicas, León, Gto.',120.00,'efectivo','pendiente','entregado','2026-04-24 14:58:35',7),(3,1,'Diego','4772381218','Puerto De Chetumal 407, Granjas Económicas, León, Gto.',115.00,'efectivo','pendiente','entregado','2026-04-24 17:35:18',15),(4,1,'Diego','4772381218','Puerto De Chetumal 407, Granjas Económicas, León, Gto.',30.00,'efectivo','pendiente','entregado','2026-04-24 17:56:44',17),(5,1,'Diego','4772381218','Puerto De Chetumal 407, Granjas Económicas, León, Gto.',30.00,'efectivo','pendiente','entregado','2026-04-24 18:01:45',19),(6,1,'Diego','4772381218','Puerto De Chetumal 407, Granjas Económicas, León, Gto.',60.00,'efectivo','pendiente','entregado','2026-04-24 22:05:13',21),(7,1,'Diego','4772381218','Puerto De Chetumal 407, Granjas Económicas, León, Gto.',40.00,'efectivo','pendiente','entregado','2026-04-24 22:35:19',24),(8,1,'Diego','4772381218','Puerto De Chetumal 407, Granjas Económicas, León, Gto.',30.00,'efectivo','pendiente','entregado','2026-04-24 22:35:52',26),(9,1,'Diego','4772381218','Puerto De Chetumal 407, Granjas Económicas, León, Gto.',30.00,'efectivo','pendiente','entregado','2026-04-24 22:48:39',28),(10,1,'Diego','4772381218','Puerto De Chetumal 407, Granjas Económicas, León, Gto.',30.00,'efectivo','pendiente','entregado','2026-04-24 22:49:30',30),(11,1,'Diego','4772381218','Puerto De Chetumal 407, Granjas Económicas, León, Gto.',30.00,'efectivo','pendiente','entregado','2026-04-24 22:57:13',31),(12,1,'Diego','4772381218','Puerto De Chetumal 407, Granjas Económicas, León, Gto.',120.00,'efectivo','pendiente','entregado','2026-04-24 23:04:24',33),(13,1,'Diego','4772381218','Puerto De Chetumal 407, Granjas Económicas, León, Gto.',30.00,'efectivo','pendiente','entregado','2026-04-24 23:14:43',38),(14,1,'Diego','4772381218','Puerto De Chetumal 407, Granjas Económicas, León, Gto.',120.00,'efectivo','pendiente','cancelado','2026-04-24 23:19:24',42);
/*!40000 ALTER TABLE `pedidos_online` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `personas`;
;
;
CREATE TABLE `personas` (
  `idPersona` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `telefono` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `direccion` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`idPersona`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
;

LOCK TABLES `personas` WRITE;
/*!40000 ALTER TABLE `personas` DISABLE KEYS */;
INSERT INTO `personas` VALUES (1,'Juan Perez','4771112233','Leon Guanajuato'),(2,'Maria Lopez','4775558899','Leon Guanajuato'),(3,'Carlos Ruiz','4777778899','Leon Guanajuato'),(4,'Diego Landeros BolaÔö£├ÂÔö£├éÔö¼├║├ö├Â┬úÔö£├®Ôö£├ÂÔö£├éÔö¼├║├ö├Â┬úÔö£┬«Ôö£├ÂÔö£├éÔö¼ÔòØ├ö├Â┬ú├ö├▓├ª├',NULL,NULL),(5,'Gilberto',NULL,NULL),(6,'Diego',NULL,NULL),(7,'Diego Landeros BolaÔö£├ÂÔö£├éÔö¼├║├ö├Â┬úÔö£├®Ôö£├ÂÔö£├éÔö¼├║├ö├Â┬úÔö£┬«Ôö£├ÂÔö£├éÔö¼ÔòØ├ö├Â┬ú├ö├▓├ª├',NULL,NULL),(8,'Diego Landeros Bola├▒os',NULL,NULL),(9,'Gilberto',NULL,NULL),(10,'Daniel Antonio',NULL,NULL),(11,'Gilberto','4771112233',NULL),(12,'Erick Missael','4774445566',NULL),(13,'Gilberto',NULL,NULL);
/*!40000 ALTER TABLE `personas` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `productos`;
;
;
CREATE TABLE `productos` (
  `idProducto` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) DEFAULT NULL,
  `descripcion` varchar(200) DEFAULT NULL,
  `precio` decimal(10,2) DEFAULT NULL,
  `categoria` varchar(50) DEFAULT NULL,
  `estado` varchar(20) DEFAULT 'activo',
  `imagen` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`idProducto`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
;

LOCK TABLES `productos` WRITE;
/*!40000 ALTER TABLE `productos` DISABLE KEYS */;
INSERT INTO `productos` VALUES (2,'Gringa','Tortilla con queso y carne',35.00,'Gringas','activo','/static/img/productos/dc59830c7df4450d98388f91037f7439.jpeg'),(3,'Quesadilla','Quesadilla con carne',30.00,'Quesadillas','activo',NULL),(4,'Refresco','Bebida 600ml',30.00,'Bebidas','activo',NULL),(5,'Coca-Cola','',25.00,'Bebidas','inactivo',NULL),(6,'Coca-Cola','',25.00,'Bebidas','inactivo',NULL),(7,'Taco de Tripa','Taco con tripa',27.00,'Tacos','inactivo',NULL),(8,'Taco de Tripa','Taco con tripa',22.00,'Tacos','activo',NULL),(9,'Taco de chorizo','Taco con chorizo',20.00,'Tacos','activo',NULL),(10,'Taco Chorizo con Tripa','Taco combinado de chorizo con tripa',22.00,'Tacos','activo',NULL),(11,'Taco con Bistec','Taco con bistec',20.00,'Tacos','activo',NULL);
/*!40000 ALTER TABLE `productos` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `proveedores`;
;
;
CREATE TABLE `proveedores` (
  `idProveedor` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) DEFAULT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `direccion` varchar(200) DEFAULT NULL,
  `estado` varchar(20) DEFAULT 'activo',
  PRIMARY KEY (`idProveedor`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
;

LOCK TABLES `proveedores` WRITE;
/*!40000 ALTER TABLE `proveedores` DISABLE KEYS */;
INSERT INTO `proveedores` VALUES (1,'Carnes San Juan','4772223344','Mercado Abastos','activo'),(2,'Verduras El Campo','4773334455','Central de Abastos','activo'),(3,'Tortilleria La Tradicional','4774445566','Zona Centro','activo');
/*!40000 ALTER TABLE `proveedores` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `recetas`;
;
;
CREATE TABLE `recetas` (
  `idReceta` int NOT NULL AUTO_INCREMENT,
  `idProducto` int DEFAULT NULL,
  `descripcion` text,
  `rendimientoPorcion` int DEFAULT NULL COMMENT 'Especifica cuÔö£├ÂÔö£├éÔö¼├║├ö├Â┬úÔö£├®Ôö£├ÂÔö£├éÔö¼├║├ö├Â┬úÔö£┬«Ôö£├ÂÔö£├éÔö¼ÔòØ├ö├Â┬ú├ö├▓├ª├ö├Â┬úÔö£├é├ö├Â┬úÔö£├®├ö├Â┬╝Ôö£ÔòæÔö£├ÂÔö£├éÔö¼├║Ôö£├ÂÔö£├éÔö£┬«├ö├Â┬úÔö£├é├ö├Â┬úÔö£├®├ö├Â┬╝Ôö£ÔòæÔö£├ÂÔö£├éÔö¼├║Ôö£├ÂÔö£ÔûôÔö£┬¬├ö├Â┬úÔö£├é├ö├Â┬úÔö£├®├ö├Â┬╝Ôö£ÔòæÔö£├ÂÔö£├éÔö¼├║├ö├Â┬úÔö£┬¬Ôö£├ÂÔö£├éÔö¼├║├ö├Â┬úÔö£├®Ôö£├ÂÔö£├éÔö¼├║├ö├Â┬úÔö£┬«Ôö£├ÂÔö£├éÔö¼ÔòØ├ö├Â┬ú├ö├▓├ª├ö├Â┬úÔö£├é├ö├Â┬úÔö£├®├ö├Â┬╝Ôö£ÔòæÔö£├ÂÔö£├éÔö¼ÔòØ├ö├Â┬╝Ôö¼┬óÔö£├ÂÔö£├éÔö¼├║├ö├Â┬úÔö£├®Ôö£├ÂÔö£├éÔö¼├║├ö├Â┬úÔö£┬«Ôö£├ÂÔö£├éÔö¼ÔòØÔö£├ÂÔö£ÔûôÔö£├┐├ö├Â┬úÔö£├é├ö├Â┬úÔö£├®├ö├Â┬╝Ôö£ÔòæÔö£├ÂÔö£├éÔö¼ÔòØ├ö├Â┬úÔö¼├¡ntas unidades o elementos produce esta receta',
  PRIMARY KEY (`idReceta`),
  KEY `idProducto` (`idProducto`),
  CONSTRAINT `recetas_ibfk_1` FOREIGN KEY (`idProducto`) REFERENCES `productos` (`idProducto`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
;

LOCK TABLES `recetas` WRITE;
/*!40000 ALTER TABLE `recetas` DISABLE KEYS */;
INSERT INTO `recetas` VALUES (2,8,NULL,1),(3,9,NULL,1),(4,10,NULL,1),(5,3,NULL,1),(6,4,NULL,1),(7,11,NULL,1);
/*!40000 ALTER TABLE `recetas` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `registromermas`;
;
;
CREATE TABLE `registromermas` (
  `idMerma` int NOT NULL AUTO_INCREMENT,
  `idInsumo` int DEFAULT NULL,
  `idEmpleado` int DEFAULT NULL,
  `cantidad` decimal(10,2) DEFAULT NULL,
  `tipoMerma` varchar(255) DEFAULT NULL,
  `motivo` text,
  `fechaRegistro` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`idMerma`),
  KEY `idInsumo` (`idInsumo`),
  KEY `idEmpleado` (`idEmpleado`),
  KEY `idx_merma_fecha` (`fechaRegistro`),
  CONSTRAINT `registromermas_ibfk_1` FOREIGN KEY (`idInsumo`) REFERENCES `insumos` (`idInsumo`),
  CONSTRAINT `registromermas_ibfk_2` FOREIGN KEY (`idEmpleado`) REFERENCES `empleados` (`idEmpleado`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
;

LOCK TABLES `registromermas` WRITE;
/*!40000 ALTER TABLE `registromermas` DISABLE KEYS */;
INSERT INTO `registromermas` VALUES (1,4,1,20.00,'Caducidad','Ya no sirven','2026-04-25 02:08:41'),(2,4,1,4.00,'Cocción','Se hicieron duritas','2026-04-25 02:09:16');
/*!40000 ALTER TABLE `registromermas` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `roles`;
;
;
CREATE TABLE `roles` (
  `idRol` int NOT NULL AUTO_INCREMENT,
  `nombreRol` varchar(50) DEFAULT NULL,
  `descripcion` varchar(150) DEFAULT NULL,
  PRIMARY KEY (`idRol`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
;

LOCK TABLES `roles` WRITE;
/*!40000 ALTER TABLE `roles` DISABLE KEYS */;
INSERT INTO `roles` VALUES (1,'Administrador','Control total del sistema'),(2,'Cajero','Gestiona ventas'),(3,'Cocina','Gestiona preparaci├ö├Â┬úÔö£├é├ö├Â┬úÔö£├®├ö├Â┬╝Ôö£ÔòæÔö£├ÂÔö£├éÔö¼├║Ôö£├ÂÔö£├éÔö£┬«Ôö£├ÂÔö£├éÔö¼├║├ö├Â┬úÔö£├®Ôö£├ÂÔö£├éÔö¼├║├ö├Â┬úÔö¼ÔòæÔö£├ÂÔö£├éÔö¼├║');
/*!40000 ALTER TABLE `roles` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `two_factor_challenges`;
;
;
CREATE TABLE `two_factor_challenges` (
  `idChallenge` int NOT NULL AUTO_INCREMENT,
  `idUsuario` int NOT NULL,
  `codigo_verificacion` varchar(6) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `expira_en` datetime NOT NULL,
  `utilizado` tinyint(1) DEFAULT '0',
  `tipo_token` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT 'login',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`idChallenge`),
  KEY `idUsuario` (`idUsuario`),
  CONSTRAINT `two_factor_challenges_ibfk_1` FOREIGN KEY (`idUsuario`) REFERENCES `usuarios` (`idUsuario`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=32 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
;

LOCK TABLES `two_factor_challenges` WRITE;
/*!40000 ALTER TABLE `two_factor_challenges` DISABLE KEYS */;
INSERT INTO `two_factor_challenges` VALUES (1,8,'120950','2026-04-17 09:52:06',1,'login','2026-04-18 03:42:05'),(2,8,'657419','2026-04-17 09:57:36',1,'login','2026-04-18 03:47:36'),(3,8,'761179','2026-04-17 09:58:51',1,'login','2026-04-17 21:48:50'),(4,10,'719784','2026-04-17 10:02:19',1,'login','2026-04-17 21:52:19'),(5,8,'247652','2026-04-17 10:06:28',1,'login','2026-04-17 21:56:27'),(6,8,'116081','2026-04-17 10:41:14',1,'login','2026-04-17 22:31:13'),(7,10,'669385','2026-04-17 10:42:23',1,'login','2026-04-17 22:32:23'),(8,8,'748076','2026-04-17 10:52:08',1,'login','2026-04-17 22:42:08'),(9,10,'480554','2026-04-17 10:56:37',1,'login','2026-04-17 22:46:36'),(10,8,'456215','2026-04-17 11:00:23',1,'login','2026-04-17 22:50:23'),(11,8,'549353','2026-04-17 11:00:25',1,'login','2026-04-17 22:50:24'),(12,15,'944982','2026-04-17 11:02:16',1,'login','2026-04-17 22:52:16'),(13,8,'395366','2026-04-17 14:11:12',1,'login','2026-04-18 02:01:12'),(14,8,'317419','2026-04-17 14:17:55',1,'login','2026-04-18 02:07:54'),(15,8,'242255','2026-04-17 16:23:06',1,'login','2026-04-18 04:13:05'),(16,8,'189448','2026-04-17 16:26:49',1,'login','2026-04-18 04:16:49'),(17,8,'216532','2026-04-17 16:29:05',1,'login','2026-04-18 04:19:05'),(18,8,'475840','2026-04-17 16:30:40',1,'login','2026-04-18 04:20:39'),(19,8,'255368','2026-04-17 16:32:29',1,'login','2026-04-18 04:22:28'),(20,8,'958873','2026-04-17 16:54:11',1,'login','2026-04-18 04:44:11'),(21,8,'498027','2026-04-17 16:56:34',1,'login','2026-04-18 04:46:34'),(22,8,'454195','2026-04-17 16:59:14',1,'login','2026-04-18 04:49:13'),(23,8,'527614','2026-04-17 17:01:15',1,'login','2026-04-18 04:51:15'),(24,8,'357706','2026-04-17 17:07:02',1,'login','2026-04-18 04:57:02'),(25,8,'501911','2026-04-24 14:58:06',1,'login','2026-04-24 20:48:06'),(26,10,'992453','2026-04-24 15:09:10',1,'login','2026-04-24 20:59:09'),(27,8,'199602','2026-04-24 16:01:51',1,'login','2026-04-24 21:51:50'),(28,8,'896525','2026-04-24 17:45:49',1,'login','2026-04-24 23:35:48'),(29,8,'262654','2026-04-24 18:06:56',1,'login','2026-04-24 23:56:56'),(30,8,'113653','2026-04-24 22:14:05',1,'login','2026-04-25 04:04:04'),(31,8,'329026','2026-04-24 23:26:14',1,'login','2026-04-25 05:16:13');
/*!40000 ALTER TABLE `two_factor_challenges` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `usuarios`;
;
;
CREATE TABLE `usuarios` (
  `idUsuario` int NOT NULL AUTO_INCREMENT,
  `idEmpleado` int DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `password` varchar(255) DEFAULT NULL,
  `idRol` int DEFAULT NULL,
  `estado` varchar(20) DEFAULT 'activo',
  PRIMARY KEY (`idUsuario`),
  UNIQUE KEY `unique_email` (`email`),
  KEY `idEmpleado` (`idEmpleado`),
  KEY `idRol` (`idRol`),
  CONSTRAINT `usuarios_ibfk_1` FOREIGN KEY (`idEmpleado`) REFERENCES `empleados` (`idEmpleado`),
  CONSTRAINT `usuarios_ibfk_2` FOREIGN KEY (`idRol`) REFERENCES `roles` (`idRol`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
;

LOCK TABLES `usuarios` WRITE;
/*!40000 ALTER TABLE `usuarios` DISABLE KEYS */;
INSERT INTO `usuarios` VALUES (8,8,'diegolanderosbolanos@hotmail.com','051297',1,'activo'),(10,10,'diegolanderosbolanos.23@gmail.com','15963',2,'activo'),(15,13,'vanesalanderosbolanos@hotmail.com','12345',3,'activo');
/*!40000 ALTER TABLE `usuarios` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `ventas`;
;
;
CREATE TABLE `ventas` (
  `idVenta` int NOT NULL AUTO_INCREMENT,
  `idEmpleado` int DEFAULT NULL,
  `fecha` datetime DEFAULT NULL,
  `total` decimal(10,2) DEFAULT NULL,
  `estado` varchar(20) DEFAULT 'pendiente',
  `idCorte` int DEFAULT NULL,
  PRIMARY KEY (`idVenta`),
  KEY `idEmpleado` (`idEmpleado`),
  KEY `idx_ventas_fecha` (`fecha`),
  KEY `fk_ventas_cortecaja` (`idCorte`),
  CONSTRAINT `fk_ventas_cortecaja` FOREIGN KEY (`idCorte`) REFERENCES `cortes_caja` (`idCorte`),
  CONSTRAINT `ventas_ibfk_1` FOREIGN KEY (`idEmpleado`) REFERENCES `empleados` (`idEmpleado`)
) ENGINE=InnoDB AUTO_INCREMENT=70 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
;

LOCK TABLES `ventas` WRITE;
/*!40000 ALTER TABLE `ventas` DISABLE KEYS */;
INSERT INTO `ventas` VALUES (1,2,'2026-03-15 20:00:00',1200.00,'cancelado',NULL),(2,2,'2026-03-28 21:00:00',950.00,'listo',NULL),(3,2,'2026-04-05 19:30:00',2100.00,'listo',NULL),(4,2,'2026-04-12 20:00:00',1850.00,'listo',NULL),(5,1,'2026-04-17 16:23:14',12000.00,'cancelado',NULL),(7,1,'2026-04-24 14:58:35',120.00,'listo',NULL),(10,1,'2026-04-24 16:04:41',20.00,'completada',NULL),(14,1,'2026-04-24 17:33:10',120.00,'listo',NULL),(15,1,'2026-04-24 17:35:18',115.00,'listo',NULL),(16,1,'2026-04-24 17:36:20',115.00,'listo',NULL),(17,1,'2026-04-24 17:56:44',30.00,'listo',NULL),(18,1,'2026-04-24 17:57:24',30.00,'listo',NULL),(19,1,'2026-04-24 18:01:45',30.00,'listo',NULL),(20,1,'2026-04-24 18:01:54',30.00,'listo',NULL),(21,1,'2026-04-24 22:05:13',60.00,'completada',NULL),(22,1,'2026-04-24 22:05:46',30.00,'completada',NULL),(23,1,'2026-04-24 22:06:11',52.00,'completada',NULL),(24,1,'2026-04-24 22:35:19',40.00,'listo',NULL),(25,1,'2026-04-24 22:35:40',22.00,'listo',NULL),(26,1,'2026-04-24 22:35:52',30.00,'listo',NULL),(27,1,'2026-04-24 22:36:25',30.00,'listo',NULL),(28,1,'2026-04-24 22:48:39',30.00,'completada',NULL),(29,1,'2026-04-24 22:49:16',30.00,'listo',NULL),(30,1,'2026-04-24 22:49:30',30.00,'completada',NULL),(31,1,'2026-04-24 22:57:13',30.00,'listo',NULL),(32,1,'2026-04-24 22:57:30',30.00,'listo',NULL),(33,1,'2026-04-24 23:04:24',120.00,'listo',NULL),(34,1,'2026-04-24 23:04:47',30.00,'listo',NULL),(35,1,'2026-04-24 23:06:43',30.00,'cancelado',NULL),(36,1,'2026-04-24 23:07:28',30.00,'cancelado',NULL),(37,1,'2026-04-24 23:13:54',60.00,'listo',NULL),(38,1,'2026-04-24 23:14:43',30.00,'listo',NULL),(39,1,'2026-04-24 23:15:25',30.00,'listo',NULL),(40,1,'2026-04-24 23:16:44',30.00,'listo',NULL),(41,1,'2026-04-24 23:19:13',30.00,'listo',NULL),(42,1,'2026-04-24 23:19:24',120.00,'cancelado',NULL),(43,1,'2026-04-24 23:24:23',30.00,'listo',NULL),(44,1,'2026-04-24 23:25:10',50.00,'listo',NULL),(45,1,'2026-04-24 23:28:39',52.00,'listo',NULL),(46,1,'2026-04-24 23:30:52',142.00,'listo',NULL),(47,1,'2026-04-24 23:31:16',20.00,'listo',NULL),(48,1,'2026-04-24 23:36:18',72.00,'listo',NULL),(49,1,'2026-04-24 23:39:45',72.00,'listo',NULL),(50,1,'2026-04-24 23:40:37',30.00,'listo',NULL),(51,1,'2026-04-24 23:41:08',30.00,'listo',NULL),(52,1,'2026-04-24 23:41:20',30.00,'listo',NULL),(53,1,'2026-04-24 23:41:26',30.00,'listo',NULL),(54,1,'2026-04-24 23:41:37',30.00,'listo',NULL),(55,8,'2026-04-24 23:47:45',60.00,'listo',NULL),(56,8,'2026-04-24 23:48:00',60.00,'listo',NULL),(57,8,'2026-04-24 23:48:45',30.00,'listo',NULL),(58,1,'2026-04-24 23:50:11',30.00,'listo',NULL),(59,1,'2026-04-24 23:50:28',20.00,'listo',NULL),(60,1,'2026-04-24 23:51:34',30.00,'listo',NULL),(61,1,'2026-04-24 23:52:19',30.00,'listo',NULL),(62,1,'2026-04-25 00:01:20',30.00,'listo',NULL),(63,1,'2026-04-25 00:01:35',20.00,'listo',NULL),(64,1,'2026-04-25 00:22:39',30.00,'pendiente',NULL),(65,1,'2026-04-25 00:32:58',20.00,'pendiente',NULL),(66,1,'2026-04-25 00:33:46',100.00,'pendiente',NULL),(67,1,'2026-04-25 00:36:13',200.00,'pendiente',NULL),(68,1,'2026-04-25 00:38:14',200.00,'pendiente',NULL),(69,1,'2026-04-25 00:48:01',20.00,'pendiente',NULL);
/*!40000 ALTER TABLE `ventas` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 DROP PROCEDURE IF EXISTS `realizar_venta` */;
ALTER DATABASE `taqueria` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci ;
 ;
 ;
 ;
 ;
 ;
 ;
 ;
 ;
DELIMITER ;;
CREATE  PROCEDURE `realizar_venta`(
    IN p_idEmpleado INT, 
    IN p_idProducto INT, 
    IN p_cantidad INT
)
BEGIN
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION 
    BEGIN
        ROLLBACK; 
        SELECT 'Error de base de datos: Transacción cancelada (Rollback automático)' AS Resultado;
    END;

    
    START TRANSACTION;

    
    IF EXISTS (
        SELECT 1 FROM detalleReceta dr
        JOIN insumos i ON dr.idInsumo = i.idInsumo
        JOIN recetas r ON dr.idReceta = r.idReceta
        WHERE r.idProducto = p_idProducto 
        AND i.stock < (dr.cantidad * p_cantidad)
    ) THEN
        
        ROLLBACK;
        SELECT 'Venta rechazada: No hay ingredientes suficientes en el inventario' AS Resultado;
    ELSE
        
        INSERT INTO ventas(idEmpleado, fecha) VALUES (p_idEmpleado, NOW());
        
        INSERT INTO detalleVenta(idVenta, idProducto, cantidad, precio) 
        VALUES (LAST_INSERT_ID(), p_idProducto, p_cantidad, (SELECT precio FROM productos WHERE idProducto = p_idProducto));
        
        
        UPDATE insumos i
        JOIN detalleReceta dr ON i.idInsumo = dr.idInsumo
        JOIN recetas r ON dr.idReceta = r.idReceta
        SET i.stock = i.stock - (dr.cantidad * p_cantidad)
        WHERE r.idProducto = p_idProducto;

        
        COMMIT;
        SELECT 'Éxito: Venta registrada y stock descontado correctamente' AS Resultado;
    END IF;

END ;;
DELIMITER ;
 ;
 ;
 ;
 ;
ALTER DATABASE `taqueria` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci ;
/*!50003 DROP PROCEDURE IF EXISTS `realizar_venta_validada` */;
ALTER DATABASE `taqueria` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci ;
 ;
 ;
 ;
 ;
 ;
 ;
 ;
 ;
DELIMITER ;;
CREATE  PROCEDURE `realizar_venta_validada`(
    IN p_idEmpleado INT, 
    IN p_idProducto INT, 
    IN p_cantidad INT
)
BEGIN
    
    DECLARE v_existe_empleado INT;
    DECLARE v_existe_producto INT;
    DECLARE v_precio_actual DECIMAL(10,2);

    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION 
    BEGIN
        ROLLBACK; 
        SELECT 'Error crítico: La venta no pudo procesarse. Rollback ejecutado.' AS Mensaje;
    END;

    
    START TRANSACTION;

    
    SELECT COUNT(*) INTO v_existe_empleado FROM empleados WHERE idEmpleado = p_idEmpleado;
    IF v_existe_empleado = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: El empleado no existe.';
    END IF;

    SELECT COUNT(*) INTO v_existe_producto FROM productos WHERE idProducto = p_idProducto;
    IF v_existe_producto = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: El producto no existe.';
    END IF;

    
    IF EXISTS (
        SELECT 1 FROM detalleReceta dr
        JOIN insumos i ON dr.idInsumo = i.idInsumo
        JOIN recetas r ON dr.idReceta = r.idReceta
        WHERE r.idProducto = p_idProducto 
        AND i.stock < (dr.cantidad * p_cantidad)
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: Inventario insuficiente para la receta.';
    END IF;

    
    SELECT precio INTO v_precio_actual FROM productos WHERE idProducto = p_idProducto;

    
    INSERT INTO ventas(idEmpleado, fecha) VALUES (p_idEmpleado, NOW());
    
    INSERT INTO detalleVenta(idVenta, idProducto, cantidad, precio) 
    VALUES (LAST_INSERT_ID(), p_idProducto, p_cantidad, v_precio_actual);
    
    
    UPDATE insumos i
    JOIN detalleReceta dr ON i.idInsumo = dr.idInsumo
    JOIN recetas r ON dr.idReceta = r.idReceta
    SET i.stock = i.stock - (dr.cantidad * p_cantidad)
    WHERE r.idProducto = p_idProducto;

    
    COMMIT;
    SELECT 'Venta exitosa: Stock actualizado y registro guardado.' AS Mensaje;

END ;;
DELIMITER ;
 ;
 ;
 ;
 ;
ALTER DATABASE `taqueria` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci ;
/*!50003 DROP PROCEDURE IF EXISTS `registrar_detalle_compra_y_stock` */;
ALTER DATABASE `taqueria` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci ;
 ;
 ;
 ;
 ;
 ;
 ;
 ;
 ;
DELIMITER ;;
CREATE  PROCEDURE `registrar_detalle_compra_y_stock`(
    IN p_idCompra INT,
    IN p_idInsumo INT,
    IN p_presentacion VARCHAR(100),
    IN p_cantidad DECIMAL(10,2),
    IN p_precio DECIMAL(10,2)
)
BEGIN
    DECLARE v_existe_compra INT;
    DECLARE v_existe_insumo INT;

    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SELECT 'Error: Transacción cancelada. Verifique los IDs proporcionados.' AS Mensaje;
    END;

    START TRANSACTION;

    
    SELECT COUNT(*) INTO v_existe_compra FROM compras WHERE idCompra = p_idCompra;
    IF v_existe_compra = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: El ID de compra no existe.';
    END IF;

    
    SELECT COUNT(*) INTO v_existe_insumo FROM insumos WHERE idInsumo = p_idInsumo;
    IF v_existe_insumo = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: El ID de insumo no existe.';
    END IF;

    
    INSERT INTO detalleCompra (idCompra, idInsumo, presentacionCompra, cantidad, precio)
    VALUES (p_idCompra, p_idInsumo, p_presentacion, p_cantidad, p_precio);

    
    UPDATE insumos SET stock = stock + p_cantidad WHERE idInsumo = p_idInsumo;

    COMMIT;
    SELECT 'Éxito: Detalle registrado e inventario actualizado.' AS Mensaje;
END ;;
DELIMITER ;
 ;
 ;
 ;
 ;
ALTER DATABASE `taqueria` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci ;
/*!50003 DROP PROCEDURE IF EXISTS `registrar_merma_validada` */;
ALTER DATABASE `taqueria` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci ;
 ;
 ;
 ;
 ;
 ;
 ;
 ;
 ;
DELIMITER ;;
CREATE  PROCEDURE `registrar_merma_validada`(
    IN p_idInsumo INT,
    IN p_idEmpleado INT,
    IN p_cantidad DECIMAL(10,2),
    IN p_tipo ENUM('Cocción', 'Caducidad', 'Error humano', 'Otro'),
    IN p_motivo TEXT
)
BEGIN
    DECLARE v_existe_insumo INT;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SELECT 'Error: No se pudo procesar el registro de merma.' AS Mensaje;
    END;

    START TRANSACTION;

    
    SELECT COUNT(*) INTO v_existe_insumo FROM insumos WHERE idInsumo = p_idInsumo;
    IF v_existe_insumo = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: Insumo no encontrado.';
    END IF;

    
    IF p_cantidad <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: La merma debe ser mayor a 0.';
    END IF;

    
    INSERT INTO registroMermas (idInsumo, idEmpleado, cantidad, tipoMerma, motivo)
    VALUES (p_idInsumo, p_idEmpleado, p_cantidad, p_tipo, p_motivo);

    
    UPDATE insumos SET stock = stock - p_cantidad WHERE idInsumo = p_idInsumo;

    COMMIT;
    SELECT 'Merma registrada y stock descontado exitosamente.' AS Mensaje;
END ;;
DELIMITER ;
 ;
 ;
 ;
 ;
ALTER DATABASE `taqueria` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci ;
/*!50003 DROP PROCEDURE IF EXISTS `registrar_venta_validando_stock` */;
ALTER DATABASE `taqueria` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci ;
 ;
 ;
 ;
 ;
 ;
 ;
 ;
 ;
DELIMITER ;;
CREATE  PROCEDURE `registrar_venta_validando_stock`(
    IN p_idEmpleado INT,
    IN p_idProducto INT,
    IN p_cantidadVendida INT
)
BEGIN
    
    DECLARE v_faltantes INT DEFAULT 0;
    DECLARE v_idVenta INT;
    DECLARE v_precio DECIMAL(10,2);
    
    
    
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error SQL en la transacción. Se hizo Rollback automático.';
    END;

    
    START TRANSACTION;

    
    
    
    
    SELECT COUNT(*) INTO v_faltantes
    FROM detalleReceta dr
    JOIN recetas r ON dr.idReceta = r.idReceta
    JOIN insumos i ON dr.idInsumo = i.idInsumo
    WHERE r.idProducto = p_idProducto
      AND i.stock < (dr.cantidad * p_cantidadVendida / r.rendimientoPorcion);

    
    IF v_faltantes > 0 THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Operación cancelada: Stock insuficiente de insumos para esta receta.';
    ELSE
        
        
        
        
        INSERT INTO ventas(idEmpleado, fecha) VALUES (p_idEmpleado, NOW());
        
        
        SET v_idVenta = LAST_INSERT_ID();
        
        
        SELECT precio INTO v_precio FROM productos WHERE idProducto = p_idProducto LIMIT 1;
        
        
        INSERT INTO detalleVenta(idVenta, idProducto, cantidad, precio) 
        VALUES (v_idVenta, p_idProducto, p_cantidadVendida, v_precio);
        
        
        
        
        UPDATE insumos i
        JOIN detalleReceta dr ON i.idInsumo = dr.idInsumo
        JOIN recetas r ON dr.idReceta = r.idReceta
        SET i.stock = i.stock - (dr.cantidad * p_cantidadVendida / r.rendimientoPorcion)
        WHERE r.idProducto = p_idProducto;

        
        
        
        COMMIT;
    END IF;
END ;;
DELIMITER ;
 ;
 ;
 ;
 ;
ALTER DATABASE `taqueria` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci ;
;

;
;
;
;
;
;
;

