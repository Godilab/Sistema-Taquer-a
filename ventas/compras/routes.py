from flask import Blueprint, render_template, request, jsonify
from sqlalchemy import text
from models import db, Compra, DetalleCompra, Insumo, Proveedor
from decimal import Decimal
from security import requiere_rol

compras_bp = Blueprint('compras', __name__, template_folder='templates')

@compras_bp.route('/')
@requiere_rol(['Administrador', 'Cajero'])
def index():
    try:
        # Usamos el ORM para las consultas simples de carga
        proveedores = Proveedor.query.filter_by(estado='activo').order_by(Proveedor.nombre.asc()).all()
        insumos = Insumo.query.order_by(Insumo.nombre.asc()).all()
        historial = Compra.query.order_by(Compra.fecha.desc()).limit(10).all()
        
        return render_template('compras/registro.html', 
                               proveedores=proveedores, 
                               insumos=insumos, 
                               historial=historial,
                               active_page='Compras')
    except Exception as e:
        return f"Error: {e}", 500

@compras_bp.route('/registrar', methods=['POST'])
@requiere_rol(['Administrador', 'Cajero'])
def registrar():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "mensaje": "Sin datos"}), 400

        id_proveedor = data.get('idProveedor')
        items = data.get('items', [])
        total_compra = Decimal(str(data.get('total', 0)))

        # 1. Insertar Compra (Encabezado) usando el ORM para obtener el ID fácil
        nueva_compra = Compra(
            idProveedor=id_proveedor,
            total=total_compra,
            notas=data.get('notas', ''),
            idCorte=None 
        )
        db.session.add(nueva_compra)
        db.session.flush()

        # 2. Procesar detalles con SQL Puro para forzar la actualización en MySQL
        for item in items:
            id_ins = item.get('idInsumo')
            cant = Decimal(str(item.get('cantidad', 0)))
            prec = Decimal(str(item.get('precio', 0)))

            if not id_ins or cant <= 0: continue

            # Registrar Detalle
            detalle = DetalleCompra(
                idCompra=nueva_compra.idCompra,
                idInsumo=id_ins,
                cantidad=cant,
                precio_unitario=prec
            )
            db.session.add(detalle)

            # --- ACTUALIZACIÓN DIRECTA VÍA SQL (COMO EN TU INVENTARIO) ---
            # Esto ignora el caché de SQLAlchemy y escribe directo en las columnas
            sql_update = text("""
                UPDATE insumos 
                SET stock = stock + :cantidad, 
                    costoUnidad = :precio 
                WHERE idInsumo = :id
            """)
            db.session.execute(sql_update, {
                'cantidad': cant,
                'precio': prec,
                'id': id_ins
            })

        db.session.commit()
        return jsonify({"status": "success", "mensaje": "¡Hecho! Stock y Precio actualizados."})

    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")
        return jsonify({"status": "error", "mensaje": str(e)}), 500