from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text
from models import db
import random
import smtplib
from email.mime.text import MIMEText
import json

# 🔥 IMPORTACIÓN DEL MOTOR CENTRALIZADO DE INVENTARIO 🔥
from ventas.routes import calcular_requerimientos_insumos, validar_stock_disponible

clientes_bp = Blueprint('clientes', __name__, template_folder='templates')

EMAIL = "gp760642@gmail.com"
PASSWORD = "onql lpox tghm igal"

public_bp = Blueprint('public', __name__, template_folder='templates')

@public_bp.route('/')
def menu_digital():
    try:
        # Se muestran los productos activos, la validación de stock se hace al pagar
        query = text("""
            SELECT p.idProducto, p.nombre, p.descripcion, p.precio, p.categoria, p.imagen
            FROM productos p
            WHERE p.estado = 'activo'
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
        # 1. VALIDAR SESIÓN
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

        # 2. VALIDACIÓN DE INSUMOS UNIFICADA (POS + WEB)
        requeridos = calcular_requerimientos_insumos(items)
        faltantes = validar_stock_disponible(requeridos)

        if faltantes:
            flash(f"¡Lo sentimos! Ya no tenemos suficiente stock para preparar tu pedido. Faltan: {', '.join(faltantes)}", "danger")
            return redirect(url_for('public.menu_digital'))

        # 3. TRANSACCIÓN EN BASE DE DATOS
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

        # Insertar Venta Física Automática (Para cocina)
        insert_venta = text("""
            INSERT INTO ventas (idEmpleado, fecha, total, estado, idCorte)
            VALUES (1, NOW(), :total, 'pendiente', NULL)
        """)
        res_venta = db.session.execute(insert_venta, {'total': total})
        id_venta = res_venta.lastrowid

        sql_detalle = text("""
            INSERT INTO detalle_pedido_online (idPedido, idProducto, cantidad, precio, opcion_preparacion)
            VALUES (:idPedido, :idProducto, :cantidad, :precio, :opcion_preparacion)
        """)
        
        insert_detalle_venta = text("""
            INSERT INTO detalleVenta (idVenta, idProducto, cantidad, precio, opcion_preparacion)
            VALUES (:idVenta, :idProducto, :cantidad, :precio, :opcion)
        """)

        for item in items:
            id_prod = item['idProducto']
            opcion_bruta = item.get('opcion', '').strip()
            
            # Sanitización de bebidas y postres
            prod_info = db.session.execute(
                text("SELECT nombre, categoria FROM productos WHERE idProducto = :id LIMIT 1"),
                {'id': id_prod}
            ).mappings().first()

            if prod_info:
                cat = str(prod_info['categoria'] or '').lower()
                nom = str(prod_info['nombre'] or '').lower()
                if 'bebida' in cat or 'postre' in cat or any(x in nom for x in ['refresco', 'coca', 'agua', 'sprite', 'fanta', 'boing', 'pepsi', 'jugo']):
                    opcion_bruta = ''

            # Guardar detalles
            db.session.execute(sql_detalle, {
                'idPedido': id_pedido, 'idProducto': id_prod,
                'cantidad': item['cantidad'], 'precio': item['precio'],
                'opcion_preparacion': opcion_bruta
            })

            db.session.execute(insert_detalle_venta, {
                'idVenta': id_venta, 'idProducto': id_prod,
                'cantidad': item['cantidad'], 'precio': item['precio'],
                'opcion': opcion_bruta
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