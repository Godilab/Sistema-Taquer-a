from flask import Blueprint, render_template, request, jsonify
from models import db, Compra, DetalleCompra, Insumo, Proveedor
from decimal import Decimal
from security import requiere_rol

compras_bp = Blueprint('compras', __name__, template_folder='templates')

@compras_bp.route('/')
@requiere_rol(['Administrador'])
def index():
    try:
        proveedores = Proveedor.query.filter_by(estado='activo').all()
        insumos = Insumo.query.all() # Traemos el inventario
        historial = Compra.query.order_by(Compra.fecha.desc()).all()
        return render_template('compras/registro.html', 
                               proveedores=proveedores, 
                               insumos=insumos, 
                               historial=historial,
                               active_page='Compras')
    except Exception as e:
        return f"Error al cargar compras: {e}", 500

@compras_bp.route('/registrar', methods=['POST'])
@requiere_rol(['Administrador'])
def registrar():
    try:
        data = request.get_json()
        
        # 1. Crear el encabezado
        nueva_compra = Compra(
            idProveedor=data['idProveedor'],
            total=Decimal(str(data['total'])),
            notas=data.get('notas', '')
        )
        db.session.add(nueva_compra)
        db.session.flush()

        # 2. Registrar detalles y sumar al inventario
        for item in data['items']:
            cantidad_decimal = Decimal(str(item['cantidad']))
            
            detalle = DetalleCompra(
                idCompra=nueva_compra.idCompra,
                idInsumo=item['idInsumo'],
                cantidad=cantidad_decimal,
                precio_unitario=Decimal(str(item['precio']))
            )
            db.session.add(detalle)

            # SUMAR AL STOCK DEL INSUMO
            insumo_obj = Insumo.query.get(item['idInsumo'])
            if insumo_obj:
                # Ajusta 'stock' al nombre real de tu columna en Insumo
                if hasattr(insumo_obj, 'stock'):
                    insumo_obj.stock += cantidad_decimal
                elif hasattr(insumo_obj, 'cantidad'):
                    insumo_obj.cantidad += cantidad_decimal

        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        print(f"Error en compra: {e}")
        return jsonify({"status": "error", "mensaje": str(e)}), 500