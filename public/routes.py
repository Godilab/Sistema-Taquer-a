from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from sqlalchemy import text
from models import db, pedidos_collection
from datetime import datetime
import json

public_bp = Blueprint('public', __name__, template_folder='templates')

@public_bp.route('/')
def menu_digital():
    if 'user_id' in session:
        return redirect('/admin')
    try:
        # Solo traemos productos que tengan stock base disponible
        query = text("""
            SELECT p.idProducto, p.nombre, p.descripcion, p.precio, p.categoria
            FROM productos p
            WHERE p.estado = 'activo'
            AND NOT EXISTS (
                SELECT 1 FROM recetas r
                JOIN detallereceta dr ON r.idReceta = dr.idReceta
                JOIN insumos i ON dr.idInsumo = i.idInsumo
                WHERE r.idProducto = p.idProducto AND i.stock < (dr.cantidad / 1000)
            )
        """)
        result = db.session.execute(query)
        platillos = [dict(row) for row in result.mappings().all()]
        return render_template('public/menu_digital.html', platillos=platillos)
    except Exception as e:
        return render_template('public/menu_digital.html', platillos=[])

@public_bp.route('/pedido/confirmar', methods=['POST'])
def confirmar_pedido():
    try:
        carrito_data = json.loads(request.form.get('carrito_json'))
        
        # --- VALIDACIÓN DE INSUMOS ---
        for item in carrito_data:
            check_query = text("""
                SELECT i.nombre, i.stock, (dr.cantidad / 1000) * :cant AS ocupado
                FROM recetas r
                JOIN detallereceta dr ON r.idReceta = dr.idReceta
                JOIN insumos i ON dr.idInsumo = i.idInsumo
                WHERE r.idProducto = :idP
            """)
            insumos = db.session.execute(check_query, {
                "cant": item['cantidad'], 
                "idP": item['idProducto']
            }).mappings().all()
            
            for ins in insumos:
                if ins['stock'] < ins['ocupado']:
                    # ESTA ES LA ALERTA QUE "BRINCA" SI NO HAY INSUMOS
                    flash(f"¡Lo sentimos! Ya no tenemos suficiente stock de {ins['nombre']} para tu pedido de {item['nombre']}.", "danger")
                    return redirect(url_for('public.menu_digital'))

        # Si pasa la validación, se guarda
        nuevo_pedido = {
            "cliente": request.form.get('cliente'),
            "telefono": request.form.get('tel'),
            "direccion": request.form.get('direccion'),
            "items": carrito_data,
            "total": float(request.form.get('total_pago')),
            "estado": "pendiente",
            "fecha_registro": datetime.utcnow()
        }
        pedidos_collection.insert_one(nuevo_pedido)
        flash('¡Pedido enviado con éxito! En breve lo prepararemos.', 'success')
        return redirect(url_for('public.menu_digital'))
    except Exception as e:
        flash('Error al procesar el pedido.', 'danger')
        return redirect(url_for('public.menu_digital'))