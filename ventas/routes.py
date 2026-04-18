from flask import Blueprint, render_template, request, jsonify
from sqlalchemy import text
from models import db, Venta, DetalleVenta, Producto, Insumo
from datetime import datetime
import json
from security import requiere_rol

# --- IMPORTACIONES NOSQL (Persistencia Políglota) ---
from models import pedidos_collection
from bson.objectid import ObjectId

ventas_bp = Blueprint('ventas', __name__, template_folder='templates')

@ventas_bp.route('/')
@requiere_rol(['Administrador', 'Cajero'])
def pos_index():
    try:
        # --- REGLA DE NEGOCIO: CONTROL PREDICTIVO DE INVENTARIO ---
        query_disponibles = text("""
            SELECT 
                p.idProducto, 
                p.nombre, 
                p.precio, 
                p.categoria,
                COALESCE(
                    (SELECT MIN(
                        FLOOR(i.stock / (
                            CASE 
                                WHEN i.categoria = 'TORTILLAS' THEN (dr.cantidad / NULLIF(i.merma, 0))
                                ELSE (dr.cantidad / 1000) / NULLIF(i.merma, 0)
                            END
                        ))
                    )
                    FROM recetas r
                    JOIN detallereceta dr ON r.idReceta = r.idReceta
                    JOIN insumos i ON dr.idInsumo = i.idInsumo
                    WHERE r.idProducto = p.idProducto
                    ), 0
                ) AS max_disponible
            FROM productos p
            WHERE p.estado = 'activo'
        """)
        
        result = db.session.execute(query_disponibles)
        productos_bd = [dict(row) for row in result.mappings().all()]

        lista_cats = [p['categoria'] for p in productos_bd if p['categoria']]
        categorias_unicas = sorted(list(set(lista_cats)))

        # Se mapea el nuevo campo max_disponible y se ajusta el booleano 'disponible'
        productos_finales = [{
            'id': p['idProducto'],
            'nombre': p['nombre'],
            'precio': float(p['precio']),
            'categoria': p['categoria'] or 'General',
            'disponible': p['max_disponible'] > 0,          # Sigue bloqueando si es 0
            'max_disponible': int(p['max_disponible'])      # Envía el límite exacto a JavaScript
        } for p in productos_bd]

        return render_template(
            'ventas/registro.html',
            active_page='POS',
            productos=productos_finales,
            categorias=categorias_unicas
        )

    except Exception as e:
        print(f"ERROR GET POS: {e}")
        return f"Error al cargar el POS: {e}", 500


@ventas_bp.route('/registrar', methods=['POST'])
@requiere_rol(['Administrador', 'Cajero'])
def registrar():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "mensaje": "Sin datos recibidos"}), 400

        id_empleado = data.get('idEmpleado', 1)
        carrito = data.get('carrito', [])
        monto_total = data.get('total', 0)

        # 1. Creamos la venta principal (MySQL)
        nueva_venta = Venta(
            idEmpleado=id_empleado,
            fecha=datetime.now(),
            total=monto_total,
            estado='pendiente',
            idCorte=None
        )
        db.session.add(nueva_venta)
        db.session.flush() # Para obtener el idVenta antes del commit

        # --- AQUÍ VA EL BLOQUE NUEVO ---
        for item in carrito:
            # Registramos cada producto en el detalle de la venta
            nuevo_detalle = DetalleVenta(
                idVenta=nueva_venta.idVenta,
                idProducto=item['idProducto'],
                cantidad=item['cantidad'],
                precio=item['precio'],
                opcion=item.get('opcion', 'Con verdura')
            )
            db.session.add(nuevo_detalle)

            # Lógica de Explosión de Materiales corregida:
            # Esta consulta detecta si es Tortilla (usa factor directo) 
            # o Carne (divide entre 1000 para kg y luego por el factor de cocción)
            query_descontar = text("""
                UPDATE insumos i
                JOIN detallereceta dr ON i.idInsumo = dr.idInsumo
                JOIN recetas r ON dr.idReceta = r.idReceta
                SET i.stock = i.stock - (
                    CASE 
                        WHEN i.categoria = 'TORTILLAS' THEN (dr.cantidad / NULLIF(i.merma, 0))
                        ELSE (dr.cantidad / 1000) / NULLIF(i.merma, 0)
                    END * :cantidad_vendida
                )
                WHERE r.idProducto = :id_producto
            """)
            db.session.execute(query_descontar, {
                'cantidad_vendida': item['cantidad'],
                'id_producto': item['idProducto']
            })
        # --- FIN DEL BLOQUE NUEVO ---

        db.session.commit()
        return jsonify({
            "status": "success",
            "mensaje": "Venta registrada e inventario actualizado",
            "id_venta": nueva_venta.idVenta
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"ERROR POST REGISTRAR: {e}")
        return jsonify({"status": "error", "mensaje": str(e)}), 500


@ventas_bp.route('/check_pedidos')
@requiere_rol(['Administrador', 'Cajero'])
def check_pedidos():
    try:
        count = pedidos_collection.count_documents({"estado": "pendiente"})
        return jsonify({"nuevos": count})
    except Exception as e:
        return jsonify({"nuevos": 0, "error": str(e)}), 500


@ventas_bp.route('/get_pedidos_pendientes')
@requiere_rol(['Administrador', 'Cajero'])
def get_pedidos_pendientes():
    try:
        cursor = pedidos_collection.find({"estado": "pendiente"}).sort("fecha_registro", -1)
        pedidos = []
        for doc in cursor:
            items_str = doc.get('items', '[]')
            items_lista = json.loads(items_str) if isinstance(items_str, str) else items_str

            pedidos.append({
                'id': str(doc['_id']),
                'cliente': doc.get('cliente', 'Sin Nombre'),
                'telefono': doc.get('telefono', ''),
                'direccion': doc.get('direccion', 'Sin dirección'),
                'total': doc.get('total', 0.0),
                'items': items_lista,
                'fecha': doc['fecha_registro'].strftime('%H:%M') if 'fecha_registro' in doc else '--:--'
            })
        return jsonify(pedidos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ventas_bp.route('/aceptar_pedido_web/<id_pedido>', methods=['POST'])
@requiere_rol(['Administrador', 'Cajero'])
def aceptar_pedido_web(id_pedido):
    try:
        pedidos_collection.update_one(
            {"_id": ObjectId(id_pedido)},
            {"$set": {"estado": "completado"}}
        )
        return jsonify({"status": "success", "mensaje": "Pedido aceptado"})
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500


@ventas_bp.route('/get_ordenes_listas')
@requiere_rol(['Administrador', 'Cajero'])
def get_ordenes_listas():
    try:
        query = text("""
            SELECT v.idVenta, v.fecha, v.estado, p.nombre, dv.cantidad, dv.opcion
            FROM ventas v
            JOIN detalleVenta dv ON v.idVenta = dv.idVenta
            JOIN productos p ON dv.idProducto = p.idProducto
            WHERE v.estado IN ('pendiente', 'listo', 'entregado')
            ORDER BY v.fecha DESC
        """)
        result = db.session.execute(query)

        ordenes_dict = {}
        for row in result:
            id_v = row.idVenta
            if id_v not in ordenes_dict:
                ordenes_dict[id_v] = {
                    'id': id_v,
                    'fecha': row.fecha.strftime('%H:%M'),
                    'estado': row.estado,
                    'productos': []
                }
            ordenes_dict[id_v]['productos'].append({
                'nombre': row.nombre,
                'cantidad': row.cantidad,
                'opcion': row.opcion
            })
        return jsonify(list(ordenes_dict.values()))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ventas_bp.route('/cancelar_orden/<int:id_venta>', methods=['POST'])
@requiere_rol(['Administrador', 'Cajero'])
def cancelar_orden(id_venta):
    try:
        data = request.get_json()
        password_admin = data.get('password')

        # BUSQUEDA DINÁMICA DEL ADMIN (Evita errores por cambio de ID)
        from models import Usuario
        admin = Usuario.query.filter_by(rol='Administrador', estado='activo').first()

        if not admin or admin.password != password_admin:
            return jsonify({
                "status": "error", 
                "mensaje": "❌ Contraseña de Administrador incorrecta o no autorizada."
            }), 403

        # 2. Verificar existencia y estado
        venta = Venta.query.get(id_venta)
        if not venta or venta.estado == 'cancelado':
            return jsonify({"status": "error", "mensaje": "Orden no válida para cancelación."}), 400

        # 3. LÓGICA DE RESTAURACIÓN DE INVENTARIO
        detalles = DetalleVenta.query.filter_by(idVenta=id_venta).all()
        for item in detalles:
            query_restaurar = text("""
                UPDATE insumos i
                JOIN detallereceta dr ON i.idInsumo = dr.idInsumo
                JOIN recetas r ON dr.idReceta = r.idReceta
                SET i.stock = i.stock + (
                    CASE 
                        WHEN i.categoria = 'TORTILLAS' THEN (dr.cantidad / i.merma)
                        ELSE (dr.cantidad / 1000) / i.merma
                    END * :cantidad_vendida
                )
                WHERE r.idProducto = :id_producto
            """)
            db.session.execute(query_restaurar, {
                'cantidad_vendida': item.cantidad,
                'id_producto': item.idProducto
            })

        # 4. Finalizar cancelación
        venta.estado = 'cancelado'
        db.session.commit()
        
        return jsonify({
            "status": "success", 
            "mensaje": "✅ Venta cancelada e insumos restaurados."
        })

    except Exception as e:
        db.session.rollback()
        print(f"ERROR EN CANCELACIÓN: {e}")
        return jsonify({"status": "error", "mensaje": str(e)}), 500
    
@ventas_bp.route('/alertas_stock')
@requiere_rol(['Administrador', 'Cajero'])
def alertas_stock():
    query = text("""
        SELECT nombre, stock, stock_minimo 
        FROM insumos 
        WHERE stock <= stock_minimo
    """)