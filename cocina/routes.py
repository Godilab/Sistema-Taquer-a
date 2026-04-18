from flask import Blueprint, render_template, jsonify
from sqlalchemy import text
from models import db
from security import requiere_rol  # <-- 1. IMPORTAMOS EL DECORADOR DE SEGURIDAD

cocina_bp = Blueprint('cocina', __name__, template_folder='templates')

@cocina_bp.route('/')
@cocina_bp.route('/pantalla')
@requiere_rol(['Administrador', 'Cocina'])  # <-- 2. BLOQUEO: Solo Admin y Cocina entran
def pantalla():
    try:
        db.session.expire_all()

        query = text("""
            SELECT 
                v.idVenta,
                v.fecha,
                p.nombre,
                dv.cantidad,
                dv.opcion
            FROM ventas v
            JOIN detalleVenta dv ON v.idVenta = dv.idVenta
            JOIN productos p ON dv.idProducto = p.idProducto
            WHERE v.estado = 'pendiente'
            ORDER BY v.fecha ASC
        """)
        
        ordenes_raw = db.session.execute(query).fetchall()
        
        ordenes_dict = {}
        for row in ordenes_raw:
            id_v = row.idVenta

            if id_v not in ordenes_dict:
                ordenes_dict[id_v] = {
                    'id': id_v,
                    'fecha': row.fecha,
                    'productos': []
                }

            ordenes_dict[id_v]['productos'].append({
                'nombre': row.nombre,
                'cantidad': row.cantidad,
                'opcion': row.opcion if row.opcion else 'Con verdura'
            })

        lista_ordenes = list(ordenes_dict.values())

        return render_template(
            'cocina/pantalla.html',
            active_page='Kitchen',
            ordenes=lista_ordenes
        )

    except Exception as e:
        print(f"CRITICAL ERROR EN COCINA: {e}")
        return f"Error en el servidor de cocina: {e}", 500


@cocina_bp.route('/completar/<int:id_venta>', methods=['POST'])
@requiere_rol(['Administrador', 'Cocina'])  # <-- 3. BLOQUEO: Evita que alguien más complete órdenes por API
def completar_orden(id_venta):
    try:
        db.session.execute(
            text("UPDATE ventas SET estado = 'listo' WHERE idVenta = :id"),
            {'id': id_venta}
        )
        db.session.commit()

        return jsonify({
            "status": "success",
            "mensaje": f"Orden #{id_venta} finalizada exitosamente"
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"ERROR AL FINALIZAR ORDEN #{id_venta}: {e}")
        return jsonify({
            "status": "error",
            "mensaje": "No se pudo actualizar el estado de la orden"
        }), 500