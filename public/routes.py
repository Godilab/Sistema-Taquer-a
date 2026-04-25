from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text
from models import db
import random
import smtplib
from email.mime.text import MIMEText
import json

# Definición directa del Blueprint
clientes_bp = Blueprint('clientes', __name__, template_folder='templates')

# =========================
# CONFIG CORREO
# =========================
EMAIL = "gp760642@gmail.com"
PASSWORD = "onql lpox tghm igal"

public_bp = Blueprint('public', __name__, template_folder='templates')

@public_bp.route('/')
def menu_digital():
    try:
        # UNIFICACIÓN: Traemos 'imagen' (Gil) y validamos STOCK DISPONIBLE (Tu versión)
        query = text("""
            SELECT p.idProducto, p.nombre, p.descripcion, p.precio, p.categoria, p.imagen
            FROM productos p
            WHERE p.estado = 'activo'
            AND NOT EXISTS (
                SELECT 1 FROM recetas r
                JOIN detallereceta dr ON r.idReceta = dr.idReceta
                JOIN insumos i ON dr.idInsumo = i.idInsumo
                WHERE r.idProducto = p.idProducto AND i.stock < (dr.cantidad / 1000)
            )
            ORDER BY p.nombre ASC
        """)
        result = db.session.execute(query)
        platillos = [dict(row) for row in result.mappings().all()]

        return render_template(
            'public/menu_digital.html',
            platillos=platillos,
            cliente_id=session.get('cliente_id'),
            cliente_nombre=session.get('cliente_nombre'),
            cliente_telefono=session.get('cliente_telefono')
        )

    except Exception as e:
        print(f"Error al cargar menú: {e}")
        return render_template(
            'public/menu_digital.html',
            platillos=[],
            cliente_id=session.get('cliente_id')
        )

@public_bp.route('/pedido/confirmar', methods=['POST'])
def confirmar_pedido():
    try:
        # ================================
        # 1. VALIDAR SEGURIDAD / SESIÓN (Requisito Sínodo)
        # ================================
        if 'cliente_id' not in session:
            flash('Debes iniciar sesión como cliente para confirmar tu pedido.', 'danger')
            return redirect(url_for('clientes.login'))

        id_cliente = session.get('cliente_id')
        nombre_cliente = session.get('cliente_nombre')
        telefono = session.get('cliente_telefono')
        direccion = request.form.get('direccion', '').strip()
        items_json = request.form.get('carrito_json', '')
        total_pago = request.form.get('total_pago', '0')
        metodo_pago = request.form.get('metodo_pago')

        if not direccion or not items_json:
            flash('Faltan datos obligatorios para el envío.', 'danger')
            return redirect(url_for('public.menu_digital'))

        items = json.loads(items_json)
        total = float(total_pago)

        if not items:
            flash('El pedido está vacío.', 'danger')
            return redirect(url_for('public.menu_digital'))

        # ================================
        # 2. VALIDACIÓN DE INSUMOS ESTRICTA (Tu versión recuperada)
        # ================================
        for item in items:
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
                    flash(f"¡Lo sentimos! Ya no tenemos suficiente stock de {ins['nombre']} para tu pedido.", "danger")
                    return redirect(url_for('public.menu_digital'))

        # ================================
        # 3. TRANSACCIÓN BASE DE DATOS (Estructura Relacional de Gil)
        # ================================
        estado_pago = 'pagado' if metodo_pago == 'tarjeta' else 'pendiente'
        estado = 'en_preparacion' if metodo_pago == 'tarjeta' else 'pendiente'

        # Insertar Pedido Online
        sql_pedido = text("""
            INSERT INTO pedidos_online (idCliente, nombre_cliente, telefono, direccion, total, metodo_pago, estado_pago, estado, fecha)
            VALUES (:idCliente, :nombre_cliente, :telefono, :direccion, :total, :metodo_pago, :estado_pago, :estado, NOW())
        """)
        res = db.session.execute(sql_pedido, {
            'idCliente': id_cliente, 'nombre_cliente': nombre_cliente, 'telefono': telefono,
            'direccion': direccion, 'total': total, 'metodo_pago': metodo_pago,
            'estado_pago': estado_pago, 'estado': estado
        })
        id_pedido = res.lastrowid

        # Insertar Detalle Pedido
        sql_detalle = text("""
            INSERT INTO detalle_pedido_online (idPedido, idProducto, cantidad, precio, opcion_preparacion)
            VALUES (:idPedido, :idProducto, :cantidad, :precio, :opcion_preparacion)
        """)
        for item in items:
            db.session.execute(sql_detalle, {
                'idPedido': id_pedido, 'idProducto': item['idProducto'],
                'cantidad': item['cantidad'], 'precio': item['precio'],
                'opcion_preparacion': item.get('opcion', '')
            })

        # Insertar Venta Física Automática
        insert_venta = text("""
            INSERT INTO ventas (idEmpleado, fecha, total, estado, idCorte)
            VALUES (1, NOW(), :total, 'pendiente', NULL)
        """)
        res_venta = db.session.execute(insert_venta, {'total': total})
        id_venta = res_venta.lastrowid

        insert_detalle_venta = text("""
            INSERT INTO detalleVenta (idVenta, idProducto, cantidad, precio, opcion_preparacion)
            VALUES (:idVenta, :idProducto, :cantidad, :precio, :opcion)
        """)
        for item in items:
            db.session.execute(insert_detalle_venta, {
                'idVenta': id_venta, 'idProducto': item['idProducto'],
                'cantidad': item['cantidad'], 'precio': item['precio'],
                'opcion': item.get('opcion', '')
            })

        # Vincular tablas
        db.session.execute(text("UPDATE pedidos_online SET idVenta = :idVenta WHERE idPedido = :idPedido"),
                           {'idVenta': id_venta, 'idPedido': id_pedido})

        db.session.commit()
        flash('¡Pedido enviado correctamente! Ya lo estamos preparando.', 'success')
        return redirect(url_for('public.menu_digital'))

    except Exception as e:
        db.session.rollback()
        print(f"Error al guardar pedido: {e}")
        flash('Error interno del servidor al procesar tu pedido.', 'danger')
        return redirect(url_for('public.menu_digital'))