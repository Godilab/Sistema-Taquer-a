from flask import Blueprint, render_template, jsonify, request
from sqlalchemy import text
from models import db
from security import requiere_rol  # Adaptar según el nombre exacto de tu decorador

cocina_bp = Blueprint('cocina', __name__, template_folder='templates')

@cocina_bp.route('/')
@cocina_bp.route('/pantalla')
@requiere_rol(['Administrador', 'Cocina'])
def pantalla():
    try:
        # Forzar actualización de datos para evitar caché de sesión
        db.session.expire_all()

        query = text("""
            SELECT 
                v.idVenta,
                v.fecha,
                p.nombre,
                p.categoria,
                dv.cantidad,
                dv.opcion_preparacion AS opcion
            FROM ventas v
            JOIN detalleVenta dv ON v.idVenta = dv.idVenta
            JOIN productos p ON dv.idProducto = p.idProducto
            WHERE v.estado = 'pendiente'
            ORDER BY v.fecha ASC, dv.idDetalleVenta ASC
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

            # --- Lógica de unificación de opciones (Filtro Anti-error) ---
            nombre_prod = str(row.nombre).lower()
            cat_prod = str(row.categoria).lower() if row.categoria else ''
            
            # Identificar si es bebida para limpiar instrucciones de comida
            es_bebida = 'bebida' in cat_prod or 'refresco' in nombre_prod or 'agua' in nombre_prod

            if es_bebida:
                opcion_final = '' # Las bebidas no llevan verdura/salsa
            else:
                # Si es comida, limpiar espacios y poner valor por defecto si está vacío
                opcion_limpia = str(row.opcion).strip() if row.opcion else ''
                opcion_final = opcion_limpia if opcion_limpia else 'Con verdura'

            ordenes_dict[id_v]['productos'].append({
                'nombre': row.nombre,
                'cantidad': row.cantidad,
                'opcion': opcion_final
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
@requiere_rol(['Administrador', 'Cocina'])
def completar_orden(id_venta):
    try:
        # Se cambia el estado a 'listo' para que el POS lo detecte en el historial
        db.session.execute(
            text("UPDATE ventas SET estado = 'completada' WHERE idVenta = :id"),
            {'id': id_venta}
        )
        db.session.commit()

        return jsonify({
            "status": "success",
            "mensaje": f"Orden #{id_venta} marcada como lista"
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "mensaje": str(e)}), 500