from flask import Blueprint, render_template, request, jsonify
from models import db, CorteCaja, Compra, Venta, DetalleVenta, Producto
from sqlalchemy import func
from decimal import Decimal, InvalidOperation
from datetime import datetime
from security import requiere_rol

# Definición del Blueprint para el módulo de finanzas
finanzas_bp = Blueprint('finanzas', __name__, template_folder='templates')

@finanzas_bp.route('/')
@requiere_rol(['Administrador', 'Cajero'])
def corte_diario():
    """
    Calcula los totales de ventas y compras pendientes de corte para la vista principal.
    """
    try:
        # Sincronizamos la sesión para obtener datos recientes (importante en entornos multi-usuario)
        db.session.expire_all()
        db.session.commit()
        
        # 1. Sumar Ventas activas (registros donde idCorte es NULL)
        total_ventas = db.session.query(func.sum(Venta.total))\
            .filter(Venta.idCorte == None).scalar() or 0
        
        # 2. Sumar Compras activas (registros donde idCorte es NULL)
        total_compras = db.session.query(func.sum(Compra.total))\
            .filter(Compra.idCorte == None).scalar() or 0
        
        # 3. Parámetros de flujo de caja
        fondo_fijo = Decimal('500.00')
        # Balance esperado = (Fondo Inicial + Ventas) - Compras
        esperado = (fondo_fijo + Decimal(str(total_ventas))) - Decimal(str(total_compras))
        
        # 4. Obtener historial de cortes (orden descendente por ID)
        historial_cortes = CorteCaja.query.order_by(CorteCaja.idCorte.desc()).all()

        return render_template('finanzas/corte.html', 
                               ventas=total_ventas, 
                               compras=total_compras, 
                               fondo=fondo_fijo, 
                               esperado=esperado,
                               historial_cortes=historial_cortes,
                               active_page='Finanzas')
    except Exception as e:
        print(f"Error en Finanzas INDEX: {e}")
        return f"Error interno del sistema: {e}", 500

@finanzas_bp.route('/detalles_corte/<int:id_corte>')
@requiere_rol(['Administrador', 'Cajero'])
def detalles_corte(id_corte):
    """
    Retorna el desglose de ventas y sus artículos para un corte histórico específico.
    """
    try:
        # Obtenemos las ventas asociadas al ID del corte
        ventas = Venta.query.filter_by(idCorte=id_corte).all()
        lista_ventas = []
        
        for v in ventas:
            # JOIN entre DetalleVenta y Producto para obtener el nombre legible
            detalles = db.session.query(DetalleVenta, Producto.nombre)\
                .join(Producto, DetalleVenta.idProducto == Producto.idProducto)\
                .filter(DetalleVenta.idVenta == v.idVenta).all()
            
            # Formateamos los artículos: "Cantidad x Nombre"
            articulos = [f"{d.DetalleVenta.cantidad}x {d.nombre}" for d in detalles]
            
            lista_ventas.append({
                'id': v.idVenta,
                'fecha': v.fecha.strftime('%H:%M:%S') if v.fecha else "--:--",
                'total': float(v.total),
                'articulos': articulos
            })
            
        return jsonify({"status": "success", "ventas": lista_ventas})
    except Exception as e:
        print(f"Error en Detalles Corte {id_corte}: {e}")
        return jsonify({"status": "error", "mensaje": str(e)}), 500

@finanzas_bp.route('/cerrar', methods=['POST'])
@requiere_rol(['Administrador', 'Cajero'])
def cerrar_caja():
    """
    Realiza el cierre de caja oficial, guardando el registro y archivando transacciones.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "mensaje": "No se recibieron datos"}), 400

        # Función auxiliar para convertir a Decimal de forma segura
        def to_dec(val):
            try:
                return Decimal(str(val))
            except (InvalidOperation, ValueError):
                return Decimal('0.00')

        # 1. Crear el registro maestro del corte
        nuevo_corte = CorteCaja(
            idEmpleado=1, # Se puede integrar con current_user.id
            fecha=datetime.now(),
            monto_inicial=to_dec(data.get('fondo')),
            ingresos_ventas=to_dec(data.get('ventas')),
            egresos_compras=to_dec(data.get('compras')),
            monto_final_esperado=to_dec(data.get('esperado')),
            monto_real=to_dec(data.get('real')),
            diferencia=to_dec(data.get('diferencia')),
            estado='cerrado'
        )
        
        db.session.add(nuevo_corte)
        # Flush para generar el idCorte antes de usarlo en los updates
        db.session.flush()
        
        # 2. ARCHIVADO DE TRANSACCIONES:
        # Vinculamos todas las ventas y compras sin corte al ID recién creado
        Venta.query.filter(Venta.idCorte == None).update({Venta.idCorte: nuevo_corte.idCorte})
        Compra.query.filter(Compra.idCorte == None).update({Compra.idCorte: nuevo_corte.idCorte})
        
        db.session.commit()
        return jsonify({"status": "success", "mensaje": "Caja cerrada y datos archivados satisfactoriamente."})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error al cerrar caja: {e}")
        return jsonify({"status": "error", "mensaje": str(e)}), 500