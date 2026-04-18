from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from pymongo import MongoClient

db = SQLAlchemy()

mongo_client = MongoClient('mongodb://localhost:27017/')
mongo_db = mongo_client['taqueria_db']
pedidos_collection = mongo_db['pedidos_online']

class Producto(db.Model):
    __tablename__ = 'productos'
    idProducto = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    descripcion = db.Column(db.Text)
    # --- ESTA ES LA LÍNEA QUE TE FALTA ---
    categoria = db.Column(db.String(50)) 
    # -------------------------------------
    estado = db.Column(db.String(20), default='activo')

class Insumo(db.Model):
    __tablename__ = 'insumos'
    idInsumo = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100))
    unidadCompra = db.Column(db.String(50))
    unidadMinima = db.Column(db.String(50))
    merma = db.Column(db.Numeric(5, 2))
    stock = db.Column(db.Numeric(10, 2))
    estado = db.Column(db.String(20), default='activo')

class Venta(db.Model):
    __tablename__ = 'ventas'
    idVenta = db.Column(db.Integer, primary_key=True, autoincrement=True)
    idEmpleado = db.Column(db.Integer)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    # --- AGREGA ESTA LÍNEA PARA EL VÍNCULO CON FINANZAS ---
    idCorte = db.Column(db.Integer, db.ForeignKey('cortes_caja.idCorte'), nullable=True)
    estado = db.Column(db.String(20), default='pendiente') # <-- SOLUCIÓN

class DetalleVenta(db.Model):
    __tablename__ = 'detalleVenta'
    idDetalleVenta = db.Column(db.Integer, primary_key=True, autoincrement=True)
    idVenta = db.Column(db.Integer, db.ForeignKey('ventas.idVenta'))
    idProducto = db.Column(db.Integer, db.ForeignKey('productos.idProducto'))
    cantidad = db.Column(db.Integer)
    precio = db.Column(db.Numeric(10, 2))
    opcion = db.Column(db.String(50)) # Para cosas como "con verdura" o "sin cebolla"
    #costo_unitario = db.Column(db.Numeric(10, 2), default=0.00)

class Merma(db.Model):
    __tablename__ = 'registromermas'
    idMerma = db.Column(db.Integer, primary_key=True)
    idInsumo = db.Column(db.Integer, db.ForeignKey('insumos.idInsumo'))
    # Quitamos el ForeignKey aquí para que Python no busque la tabla 'usuarios'
    idEmpleado = db.Column(db.Integer) 
    cantidad = db.Column(db.Numeric(10, 2))
    tipoMerma = db.Column(db.Enum('Cocción', 'Caducidad', 'Error humano', 'Otro'))
    motivo = db.Column(db.Text)
    fechaRegistro = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Solo dejamos la relación con insumo que sí sabemos que funciona
    insumo = db.relationship('Insumo', backref='mermas_registradas')

class Compra(db.Model):
    __tablename__ = 'compras'
    idCompra = db.Column(db.Integer, primary_key=True)
    idProveedor = db.Column(db.Integer, db.ForeignKey('proveedores.idProveedor'))
    fecha = db.Column(db.DateTime, default=db.func.current_timestamp())
    total = db.Column(db.Numeric(10, 2))
    notas = db.Column(db.Text)
    # --- AGREGA ESTA LÍNEA PARA EL VÍNCULO CON FINANZAS ---
    idCorte = db.Column(db.Integer, db.ForeignKey('cortes_caja.idCorte'), nullable=True)
    
    proveedor = db.relationship('Proveedor', backref='compras')

class DetalleCompra(db.Model):
    __tablename__ = 'detalle_compras'
    idDetalle = db.Column(db.Integer, primary_key=True)
    idCompra = db.Column(db.Integer, db.ForeignKey('compras.idCompra'))
    # CAMBIA ESTO DE idProducto A idInsumo:
    idInsumo = db.Column(db.Integer, db.ForeignKey('insumos.idInsumo')) 
    cantidad = db.Column(db.Numeric(10, 2))
    precio_unitario = db.Column(db.Numeric(10, 2))
    
    # También actualiza la relación si la tienes:
    insumo = db.relationship('Insumo')

class Proveedor(db.Model):
    __tablename__ = 'proveedores' # El nombre que vimos en tu captura de MySQL
    idProveedor = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.String(200))
    estado = db.Column(db.String(20), default='activo')

class CorteCaja(db.Model):
    __tablename__ = 'cortes_caja'
    idCorte = db.Column(db.Integer, primary_key=True)
    idEmpleado = db.Column(db.Integer) # El que hace el cierre
    fecha = db.Column(db.DateTime, default=db.func.current_timestamp())
    monto_inicial = db.Column(db.Numeric(10, 2)) # Fondo de caja
    ingresos_ventas = db.Column(db.Numeric(10, 2), default=0)
    egresos_compras = db.Column(db.Numeric(10, 2), default=0)
    monto_final_esperado = db.Column(db.Numeric(10, 2)) # Lo que debería haber
    monto_real = db.Column(db.Numeric(10, 2)) # Lo que el empleado contó
    diferencia = db.Column(db.Numeric(10, 2)) # Si faltó o sobró
    estado = db.Column(db.String(20), default='abierto') # abierto / cerrado

class DetalleReceta(db.Model):
    __tablename__ = 'detallereceta'
    idDetalleReceta = db.Column(db.Integer, primary_key=True, autoincrement=True)
    idReceta = db.Column(db.Integer, db.ForeignKey('recetas.idReceta'))
    idInsumo = db.Column(db.Integer, db.ForeignKey('insumos.idInsumo'))
    cantidad = db.Column(db.Numeric(10, 2))
    unidad = db.Column(db.String(10)) # <--- AÑADE ESTA LÍNEA