from flask import Blueprint, render_template, request, jsonify, session
from sqlalchemy import text
from models import db
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP


ventas_bp = Blueprint('ventas', __name__, template_folder='templates')

# =========================================================
# UTILIDADES Y LÓGICA DE NEGOCIO
# =========================================================

def d(valor):
    return Decimal(str(valor or 0))

def normalizar_texto(valor):
    return (valor or '').strip().lower()

# SANITIZADOR ABSOLUTO PARA BEBIDAS Y POSTRES
def es_producto_sin_preparacion(categoria, nombre):
    cat = normalizar_texto(categoria)
    nom = normalizar_texto(nombre)
    return any(k in cat for k in ['bebida', 'postre']) or any(k in nom for k in ['refresco', 'coca', 'agua', 'sprite', 'fanta', 'boing', 'pepsi'])

def opcion_a_ingredientes(opcion):
    op = normalizar_texto(opcion)
    mapeo = {
        'con todo': {'cilantro', 'cebolla', 'salsa'},
        'completo': {'cilantro', 'cebolla', 'salsa'},
        'todo aparte': {'cilantro', 'cebolla', 'salsa'},
        'con verdura': {'cilantro', 'cebolla'},
        'solo verdura': {'cilantro', 'cebolla'},
        'sin verdura': set(),
        'solo cilantro': {'cilantro'},
        'solo cebolla': {'cebolla'},
        'solo salsa': {'salsa'}
    }
    return mapeo.get(op, {'cilantro', 'cebolla', 'salsa'})

def clasificar_insumo_variable(nombre_insumo):
    nombre = normalizar_texto(nombre_insumo)
    if 'cilantro' in nombre: return 'cilantro'
    if 'cebolla' in nombre: return 'cebolla'
    if 'salsa' in nombre: return 'salsa'
    return None

def normalizar_unidad(unidad):
    u = normalizar_texto(unidad)
    equivalencias = {
        'gr': 'gr', 'g': 'gr', 'gramo': 'gr', 'gramos': 'gr',
        'kg': 'kg', 'kilo': 'kg', 'kilos': 'kg', 'kilogramo': 'kg', 'kilogramos': 'kg',
        'ml': 'ml', 'mililitro': 'ml', 'mililitros': 'ml',
        'lt': 'lt', 'l': 'lt', 'litro': 'lt', 'litros': 'lt',
        'pz': 'pz', 'pza': 'pz', 'pzas': 'pz', 'pieza': 'pz', 'piezas': 'pz',
        'unidad': 'pz', 'unidades': 'pz'
    }
    return equivalencias.get(u, u)

def convertir_unidad(cantidad, unidad_origen, unidad_destino):
    cantidad = d(cantidad)
    origen = normalizar_unidad(unidad_origen)
    destino = normalizar_unidad(unidad_destino)

    if not origen or not destino or origen == destino: return cantidad

    if origen == 'gr' and destino == 'kg': return cantidad / Decimal('1000')
    if origen == 'kg' and destino == 'gr': return cantidad * Decimal('1000')
    if origen == 'ml' and destino == 'lt': return cantidad / Decimal('1000')
    if origen == 'lt' and destino == 'ml': return cantidad * Decimal('1000')
    return cantidad

def obtener_columnas_insumos():
    query = text("SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'insumos'")
    return set(db.session.execute(query).scalars().all())

def obtener_columna_unidad_stock():
    columnas = obtener_columnas_insumos()
    for col in ['unidadCompra', 'unidad_compra', 'unidad', 'unidadMedida', 'unidad_medida']:
        if col in columnas: return col
    return None

def obtener_columna_unidad_minima():
    columnas = obtener_columnas_insumos()
    for col in ['unidadMinima', 'unidad_minima']:
        if col in columnas: return col
    return None

def obtener_receta_producto(id_producto):
    col_stock_unit = obtener_columna_unidad_stock()
    col_min_unit = obtener_columna_unidad_minima()
    select_extra = f", i.{col_stock_unit} AS unidad_stock" if col_stock_unit else ", NULL AS unidad_stock"
    select_extra += f", i.{col_min_unit} AS unidad_minima" if col_min_unit else ", NULL AS unidad_minima"

    query = text(f"""
        SELECT dr.idInsumo, dr.cantidad, dr.unidad AS unidad_receta, i.nombre AS nombre_insumo, i.stock {select_extra}
        FROM recetas r
        JOIN detallereceta dr ON r.idReceta = dr.idReceta
        JOIN insumos i ON dr.idInsumo = i.idInsumo
        WHERE r.idProducto = :idProducto
    """)
    rows = db.session.execute(query, {'idProducto': id_producto}).mappings().all()

    return [{
        'idInsumo': r['idInsumo'], 'cantidad': r['cantidad'], 'unidad_receta': r.get('unidad_receta') or 'pz',
        'nombre_insumo': r['nombre_insumo'], 'stock': r['stock'],
        'unidad_stock': r.get('unidad_stock') or r.get('unidad_receta') or 'pz',
        'unidad_minima': r.get('unidad_minima') or ''
    } for r in rows]

def obtener_unidad_stock_insumo(id_insumo):
    col = obtener_columna_unidad_stock()
    if not col: return ''
    row = db.session.execute(text(f"SELECT {col} AS unidad_stock FROM insumos WHERE idInsumo = :idInsumo LIMIT 1"), {'idInsumo': id_insumo}).mappings().first()
    return row['unidad_stock'] if row else ''

def calcular_requerimientos_insumos(items):
    requeridos = {}
    for item in items:
        id_producto = int(item['idProducto'])
        cantidad_producto = d(item['cantidad'])
        opcion = item.get('opcion', 'Con todo')
        ing_permitidos = opcion_a_ingredientes(opcion)
        receta = obtener_receta_producto(id_producto)

        for insumo in receta:
            tipo_var = clasificar_insumo_variable(insumo['nombre_insumo'])
            if tipo_var is not None and tipo_var not in ing_permitidos: continue

            cant_conv = convertir_unidad(d(insumo['cantidad']) * cantidad_producto, insumo.get('unidad_receta') or 'pz', insumo.get('unidad_stock') or insumo.get('unidad_receta') or 'pz')
            
            if insumo['idInsumo'] not in requeridos:
                requeridos[insumo['idInsumo']] = {'idInsumo': insumo['idInsumo'], 'nombre': insumo['nombre_insumo'], 'cantidad': Decimal('0'), 'unidad': insumo.get('unidad_stock') or insumo.get('unidad_receta') or 'pz'}
            requeridos[insumo['idInsumo']]['cantidad'] += cant_conv
    return requeridos

def validar_stock_disponible(requeridos):
    faltantes = []
    for _, dato in requeridos.items():
        insumo = db.session.execute(text("SELECT idInsumo, nombre, stock FROM insumos WHERE idInsumo = :id LIMIT 1"), {'id': dato['idInsumo']}).mappings().first()
        if not insumo:
            faltantes.append(f"Insumo no encontrado (ID {dato['idInsumo']})")
            continue
        stock_actual = d(insumo['stock'])
        cant_req = d(dato['cantidad'])
        if stock_actual < cant_req:
            faltantes.append(f"{insumo['nombre']} insuficiente")
    return faltantes

def calcular_max_absoluto(id_producto, opcion):
    receta = obtener_receta_producto(id_producto)
    ing_permitidos = opcion_a_ingredientes(opcion)
    max_unidades = float('inf')
    
    if not receta: return 0

    for insumo in receta:
        tipo_var = clasificar_insumo_variable(insumo['nombre_insumo'])
        if tipo_var is not None and tipo_var not in ing_permitidos:
            continue
        cant_req_1 = convertir_unidad(d(insumo['cantidad']), insumo.get('unidad_receta') or 'pz', insumo.get('unidad_stock') or insumo.get('unidad_receta') or 'pz')
        
        if cant_req_1 > 0:
            stock_actual = d(insumo['stock'])
            posibles = int(stock_actual // cant_req_1)
            if posibles < max_unidades:
                max_unidades = posibles
                
    return max_unidades if max_unidades != float('inf') else 0

def descontar_stock(requeridos):
    upd_q = text("UPDATE insumos SET stock = stock - :cant WHERE idInsumo = :id")
    for _, dato in requeridos.items():
        db.session.execute(upd_q, {'cant': float(dato['cantidad']), 'id': dato['idInsumo']})

# =========================================================
# RUTAS POS Y VALIDACIÓN
# =========================================================

@ventas_bp.route('/')
def pos_index():
    try:
        query = text("SELECT idProducto, nombre, precio, categoria, imagen FROM productos WHERE estado = 'activo' ORDER BY nombre ASC")
        productos_bd = db.session.execute(query).mappings().all()
        categorias_unicas = sorted(list({p['categoria'] for p in productos_bd if p['categoria']}))
        productos_finales = [{'id': p['idProducto'], 'nombre': p['nombre'], 'precio': float(p['precio']), 'categoria': p['categoria'] or 'General', 'imagen': p.get('imagen')} for p in productos_bd]
        return render_template('ventas/registro.html', active_page='POS', productos=productos_finales, categorias=categorias_unicas)
    except Exception as e:
        return f"Error interno: {e}", 500

@ventas_bp.route('/validar_stock', methods=['POST'])
def validar_stock():
    try:
        data = request.get_json() or {}
        carrito = data.get('carrito', [])
        id_prod = data.get('idProducto')
        opcion = data.get('opcion', '')
        nombre = data.get('nombre', 'producto')

        if not carrito: return jsonify({"status": "success"})
        
        requeridos = calcular_requerimientos_insumos(carrito)
        faltantes = validar_stock_disponible(requeridos)
        
        if faltantes:
            if id_prod:
                max_posible = calcular_max_absoluto(id_prod, opcion)
                return jsonify({
                    "status": "error", 
                    "mensaje": f"No hay stock suficiente. Solo alcanzan para {max_posible} '{nombre}'."
                })
            return jsonify({"status": "error", "mensaje": "Inventario insuficiente para procesar la orden."})
            
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500

@ventas_bp.route('/registrar', methods=['POST'])
def registrar():
    try:
        data = request.get_json()
        if not data or not data.get('carrito'): 
            return jsonify({"status": "error", "mensaje": "Datos inválidos"}), 400

        requeridos = calcular_requerimientos_insumos(data['carrito'])
        faltantes = validar_stock_disponible(requeridos)
        if faltantes: 
            return jsonify({"status": "error", "mensaje": "Stock insuficiente. Revisa el inventario."}), 400

        descontar_stock(requeridos)

        id_venta = db.session.execute(
            text("INSERT INTO ventas (idEmpleado, fecha, total, estado) VALUES (:emp, NOW(), :tot, 'pendiente')"),
            {'emp': data.get('idEmpleado', 1), 'tot': float(d(data.get('total', 0)))}
        ).lastrowid

        q_det = text("INSERT INTO detalleVenta (idVenta, idProducto, cantidad, precio, opcion_preparacion) VALUES (:idV, :idP, :cant, :precio, :opcion)")
        
        for item in data['carrito']:
            # SANITIZACIÓN ULTRA AGRESIVA
            prod_info = db.session.execute(text("SELECT categoria, nombre FROM productos WHERE idProducto = :id LIMIT 1"), {'id': item['idProducto']}).mappings().first()
            opcion_final = item.get('opcion', '')
            
            if prod_info:
                cat = str(prod_info['categoria'] or '').lower()
                nom = str(prod_info['nombre'] or '').lower()
                if 'bebida' in cat or 'postre' in cat or any(x in nom for x in ['refresco', 'coca', 'agua', 'sprite', 'fanta', 'boing', 'pepsi']):
                    opcion_final = ''

            db.session.execute(q_det, {'idV': id_venta, 'idP': item['idProducto'], 'cant': item['cantidad'], 'precio': item['precio'], 'opcion': opcion_final})

        db.session.commit()
        return jsonify({"status": "success", "idVenta": id_venta}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "mensaje": str(e)}), 500

# =========================================================
# RUTAS WEB (AUTO-ACEPTACIÓN Y SANITIZACIÓN)
# =========================================================

@ventas_bp.route('/auto_procesar_pedidos_web')
def auto_procesar_pedidos_web():
    try:
        pendientes = db.session.execute(text("SELECT idPedido, idVenta, nombre_cliente FROM pedidos_online WHERE estado = 'pendiente'")).mappings().all()
        aceptados = []
        rechazados = []

        for p in pendientes:
            id_ped = p['idPedido']
            id_venta_existente = p['idVenta']
            
            claim_res = db.session.execute(
                text("UPDATE pedidos_online SET estado = 'en_preparacion' WHERE idPedido = :id AND estado = 'pendiente'"), 
                {'id': id_ped}
            )
            
            if claim_res.rowcount == 0:
                continue 
                
            detalles = db.session.execute(text("""
                SELECT d.idProducto, d.cantidad, d.opcion_preparacion, p.categoria, p.nombre 
                FROM detalle_pedido_online d
                JOIN productos p ON d.idProducto = p.idProducto
                WHERE d.idPedido = :id
            """), {'id': id_ped}).mappings().all()
            
            requeridos = calcular_requerimientos_insumos([{'idProducto': d['idProducto'], 'cantidad': d['cantidad'], 'opcion': d.get('opcion_preparacion', '')} for d in detalles])
            faltantes = validar_stock_disponible(requeridos)
            
            if faltantes:
                db.session.execute(text("UPDATE pedidos_online SET estado = 'cancelado' WHERE idPedido = :id"), {'id': id_ped})
                if id_venta_existente:
                    db.session.execute(text("UPDATE ventas SET estado = 'cancelado' WHERE idVenta = :idV"), {'idV': id_venta_existente})
                rechazados.append(p['nombre_cliente'])
            else:
                descontar_stock(requeridos)
                
                # SI LA TIENDA EN LÍNEA MANDÓ UN REFRESCO CON VERDURA, LO BORRAMOS DE LA TABLA VENTAS
                if id_venta_existente:
                    q_update_det = text("UPDATE detalleVenta SET opcion_preparacion = '' WHERE idVenta = :idV AND idProducto = :idP")
                    for item in detalles:
                        if es_producto_sin_preparacion(item['categoria'], item['nombre']):
                            db.session.execute(q_update_det, {'idV': id_venta_existente, 'idP': item['idProducto']})

                aceptados.append(p['nombre_cliente'])
        
        db.session.commit()
        count_activos = db.session.execute(text("SELECT COUNT(*) FROM pedidos_online WHERE estado = 'en_preparacion'")).scalar()

        return jsonify({"aceptados": aceptados, "rechazados": rechazados, "activos": count_activos})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@ventas_bp.route('/get_pedidos_pendientes')
def get_pedidos_pendientes():
    try:
        query = text("""
            SELECT po.idPedido, po.idCliente, po.nombre_cliente, po.telefono, po.direccion, po.total, po.fecha,
                   dpo.idProducto, dpo.cantidad, dpo.precio, dpo.opcion_preparacion, p.nombre AS nombre_producto, p.categoria
            FROM pedidos_online po
            JOIN detalle_pedido_online dpo ON po.idPedido = dpo.idPedido
            JOIN productos p ON dpo.idProducto = p.idProducto
            WHERE po.estado = 'en_preparacion' ORDER BY po.fecha DESC
        """)
        result = db.session.execute(query).mappings().all()
        pedidos = {}
        for r in result:
            if r['idPedido'] not in pedidos:
                pedidos[r['idPedido']] = {'id': r['idPedido'], 'cliente': r['nombre_cliente'] or 'NA', 'telefono': r['telefono'] or '', 'direccion': r['direccion'] or '', 'total': float(r['total']), 'fecha': r['fecha'].strftime('%H:%M'), 'items': []}
            
            opcion_final = '' if es_producto_sin_preparacion(r['categoria'], r['nombre_producto']) else (r['opcion_preparacion'] or '')
            
            pedidos[r['idPedido']]['items'].append({'idProducto': r['idProducto'], 'nombre': r['nombre_producto'], 'cantidad': r['cantidad'], 'precio': float(r['precio']), 'opcion': opcion_final})
        return jsonify(list(pedidos.values()))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@ventas_bp.route('/concluir_pedido_web/<int:id_pedido>', methods=['POST'])
def concluir_pedido_web(id_pedido):
    try:
        db.session.execute(text("UPDATE pedidos_online SET estado = 'entregado' WHERE idPedido = :id"), {'id': id_pedido})
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "mensaje": str(e)}), 500

@ventas_bp.route('/aceptar_pedido_web/<int:id_pedido>', methods=['POST'])
def aceptar_pedido_web(id_pedido):
    try:
        pedido = db.session.execute(text("SELECT idPedido, idVenta, nombre_cliente, total, estado FROM pedidos_online WHERE idPedido = :id LIMIT 1"), {'id': id_pedido}).mappings().first()
        if not pedido or pedido['estado'] != 'pendiente': return jsonify({"status": "error", "mensaje": "Pedido no válido"}), 400

        detalles = db.session.execute(text("""
            SELECT d.idProducto, d.cantidad, d.precio, d.opcion_preparacion, p.categoria, p.nombre 
            FROM detalle_pedido_online d
            JOIN productos p ON d.idProducto = p.idProducto
            WHERE d.idPedido = :id
        """), {'id': id_pedido}).mappings().all()

        requeridos = calcular_requerimientos_insumos([{'idProducto': d['idProducto'], 'cantidad': d['cantidad'], 'opcion': d.get('opcion_preparacion', '')} for d in detalles])
        faltantes = validar_stock_disponible(requeridos)
        
        if faltantes: return jsonify({"status": "error", "mensaje": "No hay stock suficiente para surtir el pedido web."}), 400
        
        descontar_stock(requeridos)
        
        if pedido['idVenta']:
            q_update_det = text("UPDATE detalleVenta SET opcion_preparacion = '' WHERE idVenta = :idV AND idProducto = :idP")
            for item in detalles:
                if es_producto_sin_preparacion(item['categoria'], item['nombre']):
                    db.session.execute(q_update_det, {'idV': pedido['idVenta'], 'idP': item['idProducto']})

        db.session.execute(text("UPDATE pedidos_online SET estado = 'en_preparacion' WHERE idPedido = :id"), {'id': id_pedido})
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "mensaje": str(e)}), 500

# =========================================================
# RUTAS HISTORIAL (TICKETS POS)
# =========================================================

@ventas_bp.route('/check_ordenes_listas')
def check_ordenes_listas():
    try:
        # El notificador visual solo debe contar las órdenes de hoy
        query = text("SELECT COUNT(*) FROM ventas WHERE estado = 'completada' AND DATE(fecha) = CURDATE()")
        count = db.session.execute(query).scalar() or 0
        return jsonify({'listas': count})
    except Exception as e:
        return jsonify({'listas': 0})

from datetime import datetime

@ventas_bp.route('/get_ordenes_listas')
def get_ordenes_listas():
    try:
        # Obtenemos la fecha del parámetro GET, si no, usamos la de hoy
        fecha_filtro = request.args.get('fecha')
        if not fecha_filtro:
            fecha_filtro = datetime.now().strftime('%Y-%m-%d')

        # Filtramos por estado 'completada' y por la fecha seleccionada
        query = text("""
            SELECT v.idVenta, v.fecha 
            FROM ventas v 
            WHERE v.estado = 'completada' 
              AND DATE(v.fecha) = :fecha
            ORDER BY v.fecha DESC
        """)
        
        ordenes_db = db.session.execute(query, {'fecha': fecha_filtro}).mappings().all()
        
        resultado = []
        for o in ordenes_db:
            # Consultar productos de cada orden
            query_p = text("""
                SELECT p.nombre, dv.cantidad, dv.opcion_preparacion 
                FROM detalleVenta dv
                JOIN productos p ON dv.idProducto = p.idProducto
                WHERE dv.idVenta = :id
            """)
            prods = db.session.execute(query_p, {'id': o['idVenta']}).mappings().all()
            
            resultado.append({
                'id': o['idVenta'],
                'fecha': o['fecha'].strftime('%H:%M'), # Solo hora para el historial del día
                'productos': [{'nombre': p['nombre'], 'cantidad': p['cantidad'], 'opcion': p['opcion_preparacion']} for p in prods]
            })
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ventas_bp.route('/cancelar_orden/<int:id_venta>', methods=['POST'])
def cancelar_orden(id_venta):
    try:
        data = request.get_json() or {}
        password_ingresada = data.get('password')
        user_rol = session.get('user_rol')

        if user_rol != 1:
            if not password_ingresada:
                return jsonify({"status": "error", "mensaje": "Se requieren credenciales de Administrador."}), 401
            
            admin = db.session.execute(text("SELECT password FROM usuarios WHERE idRol = 1 AND estado = 'activo' LIMIT 1")).mappings().first()
            if not admin or admin['password'] != password_ingresada:
                return jsonify({"status": "error", "mensaje": "Credenciales inválidas."}), 403

        detalles = db.session.execute(text("SELECT idProducto, cantidad, opcion_preparacion FROM detalleVenta WHERE idVenta = :id"), {'id': id_venta}).mappings().all()

        if detalles:
            items = [{'idProducto': d['idProducto'], 'cantidad': d['cantidad'], 'opcion': d['opcion_preparacion']} for d in detalles]
            requeridos = calcular_requerimientos_insumos(items)
            upd_q = text("UPDATE insumos SET stock = stock + :cantidad WHERE idInsumo = :idInsumo")
            for _, dato in requeridos.items():
                db.session.execute(upd_q, {'cantidad': float(dato['cantidad']), 'idInsumo': dato['idInsumo']})

        db.session.execute(text("UPDATE ventas SET estado = 'cancelado' WHERE idVenta = :id"), {'id': id_venta})
        db.session.execute(text("UPDATE pedidos_online SET estado = 'cancelado' WHERE idVenta = :id"), {'id': id_venta})
        
        db.session.commit()
        return jsonify({"status": "success"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "mensaje": str(e)}), 500
    

#-----Ticket
    
def generar_ticket_ascii(id_venta, db_session, metodo_pago='Efectivo', monto_recibido=0.00, cambio=0.00):
    ANCHO = 40
    def centrar(texto): return texto.center(ANCHO)
    def izq_der(izq, der): return f"{izq}{der:>{ANCHO - len(izq)}}"

    query_venta = text("""
        SELECT v.idVenta, v.fecha, v.total, COALESCE(p_emp.nombre, 'Administrador') AS nombre_cajero
        FROM ventas v
        LEFT JOIN empleados e ON v.idEmpleado = e.idEmpleado
        LEFT JOIN personas p_emp ON e.idPersona = p_emp.idPersona
        WHERE v.idVenta = :id
    """)
    venta = db_session.execute(query_venta, {'id': id_venta}).mappings().first()
    if not venta: return "ERROR: Venta no encontrada."

    query_detalles = text("""
        SELECT p.nombre, dv.cantidad, dv.precio, (dv.cantidad * dv.precio) AS subtotal, dv.opcion_preparacion
        FROM detalleVenta dv
        JOIN productos p ON dv.idProducto = p.idProducto
        WHERE dv.idVenta = :id
    """)
    detalles = db_session.execute(query_detalles, {'id': id_venta}).mappings().all()

    lineas = []
    lineas.append("=" * ANCHO)
    lineas.append(centrar("TAQUERÍA LOS INGES"))
    lineas.append(centrar("Universidad Tecnológica de León"))
    lineas.append("=" * ANCHO)
    lineas.append(f"Folio : #{str(venta.idVenta).zfill(6)}")
    lineas.append(f"Fecha : {venta.fecha.strftime('%d/%m/%Y %H:%M')}")
    lineas.append(f"Cajero: {venta.nombre_cajero}")
    lineas.append("-" * ANCHO)
    lineas.append(f"{'CANT':<4} {'DESCRIPCION':<18} {'P.UNIT':>7} {'SUBT':>8}")
    lineas.append("-" * ANCHO)

    for d in detalles:
        nombre = str(d['nombre'])[:18]
        lineas.append(f"{str(d['cantidad']):<4} {nombre:<18} {f'${float(d['precio']):.2f}':>7} {f'${float(d['subtotal']):.2f}':>8}")
        if d['opcion_preparacion']:
            lineas.append(f"  *{str(d['opcion_preparacion'])[:36]}")

    lineas.append("-" * ANCHO)
    lineas.append(izq_der("TOTAL:", f"${float(venta.total):.2f}"))
    lineas.append("=" * ANCHO)

    metodo_upper = str(metodo_pago).upper()
    lineas.append(centrar(f"PAGO CON {metodo_upper}"))
    if 'EFECTIVO' in metodo_upper:
        lineas.append(izq_der("Recibido:", f"${float(monto_recibido):.2f}"))
        lineas.append(izq_der("Cambio:", f"${float(cambio):.2f}"))
    
    lineas.append("=" * ANCHO)
    lineas.append(centrar("¡GRACIAS POR SU PREFERENCIA!"))
    lineas.append("\n\n\n")
    return "\n".join(lineas)

# --- RUTA DEL TICKET ---
@ventas_bp.route('/ticket/<int:id_venta>')
def imprimir_ticket(id_venta):
    try:
        # Capturamos datos dinámicos de la URL
        metodo = request.args.get('metodo', 'Efectivo')
        efectivo = request.args.get('efectivo', 0.0)
        cambio = request.args.get('cambio', 0.0)

        # Generamos el contenido ASCII usando la función utilitaria
        contenido_ticket = generar_ticket_ascii(id_venta, db.session, metodo, efectivo, cambio)

        # Pasamos el string a la plantilla
        return render_template('ventas/ticket.html', ticket_ascii=contenido_ticket)
    except Exception as e:
        return f"Error en la generación del ticket: {str(e)}", 500