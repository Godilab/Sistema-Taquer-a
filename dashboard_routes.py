from flask import Blueprint, render_template, request, send_file
from sqlalchemy import text
from models import db
from datetime import datetime, timedelta
import pandas as pd
import io
from security import requiere_rol

# Definición del Blueprint
dashboard_bp = Blueprint('dashboard', __name__, template_folder='templates')

@dashboard_bp.route('/dashboard')
@requiere_rol(['Administrador', 'Cajero'])
def index():
    """Calcula todos los indicadores financieros y operativos del negocio"""
    hoy_dt = datetime.now()
    filtro = request.args.get('filtro', 'mes')

    # Lógica de fechas para el filtrado
    if filtro == 'dia':
        fecha_inicio = hoy_dt.strftime('%Y-%m-%d')
        fecha_fin = hoy_dt.strftime('%Y-%m-%d')
        es_un_dia = True
    elif filtro == 'semana':
        inicio_sem = hoy_dt - timedelta(days=hoy_dt.weekday())
        fecha_inicio = inicio_sem.strftime('%Y-%m-%d')
        fecha_fin = hoy_dt.strftime('%Y-%m-%d')
        es_un_dia = False
    else:
        fecha_inicio = hoy_dt.replace(day=1).strftime('%Y-%m-%d')
        fecha_fin = hoy_dt.strftime('%Y-%m-%d')
        es_un_dia = False

    try:
        # 1. KPIs Financieros: Ventas, Ordenes y Utilidad Bruta (Precio - Costo Receta)
        query_kpis = text("""
            SELECT 
                COALESCE(SUM(v.total), 0) as ventas_totales,
                COUNT(DISTINCT v.idVenta) as ordenes_totales,
                COALESCE(SUM((dv.precio - dv.costo_unitario) * dv.cantidad), 0) as utilidad_bruta
            FROM ventas v
            LEFT JOIN detalleVenta dv ON v.idVenta = dv.idVenta
            WHERE DATE(v.fecha) BETWEEN :inicio AND :fin 
        """)
        kpis = db.session.execute(query_kpis, {"inicio": fecha_inicio, "fin": fecha_fin}).mappings().first()
        
        ventas_totales = float(kpis['ventas_totales'])
        ordenes_totales = int(kpis['ordenes_totales'])
        utilidad_bruta = float(kpis['utilidad_bruta'])
        ticket_promedio = ventas_totales / ordenes_totales if ordenes_totales > 0 else 0

        # 2. GASTOS OPERATIVOS: Compras registradas en el periodo (Escenario 6)
        query_gastos = text("""
            SELECT COALESCE(SUM(total), 0) as gastos_totales
            FROM compras
            WHERE DATE(fecha) BETWEEN :inicio AND :fin 
        """)
        gastos_raw = db.session.execute(query_gastos, {"inicio": fecha_inicio, "fin": fecha_fin}).scalar()
        gastos_operativos = float(gastos_raw)

        # 3. UTILIDAD NETA: Ganancia final descontando costos operativos
        utilidad_neta = utilidad_bruta - gastos_operativos

        # 4. TOP PRODUCTOS
        query_top = text("""
            SELECT p.nombre, SUM(dv.cantidad) as total_vendido
            FROM detalleVenta dv
            JOIN productos p ON dv.idProducto = p.idProducto
            JOIN ventas v ON dv.idVenta = v.idVenta
            WHERE DATE(v.fecha) BETWEEN :inicio AND :fin
            GROUP BY p.idProducto
            ORDER BY total_vendido DESC
            LIMIT 5
        """)
        top_productos_raw = db.session.execute(query_top, {"inicio": fecha_inicio, "fin": fecha_fin}).mappings().all()
        top_productos = [dict(p) for p in top_productos_raw]
        producto_estrella = top_productos[0] if top_productos else None

        # 5. ALERTAS DE STOCK
        query_alertas = text("""
            SELECT nombre, stock, stockMinimo, unidadCompra 
            FROM insumos 
            WHERE stock <= stockMinimo AND estado = 'activo'
        """)
        alertas_stock = db.session.execute(query_alertas).mappings().all()

        # 6. DATOS PARA GRÁFICA DE TENDENCIA
        if es_un_dia:
            query_grafica = text("""
                SELECT HOUR(fecha) as etiqueta, SUM(total) as total
                FROM ventas
                WHERE DATE(fecha) = :inicio 
                GROUP BY HOUR(fecha)
                ORDER BY etiqueta ASC
            """)
        else:
            query_grafica = text("""
                SELECT DATE(fecha) as etiqueta, SUM(total) as total
                FROM ventas
                WHERE DATE(fecha) BETWEEN :inicio AND :fin 
                GROUP BY DATE(fecha)
                ORDER BY etiqueta ASC
            """)
        
        ventas_raw = db.session.execute(query_grafica, {"inicio": fecha_inicio, "fin": fecha_fin}).mappings().all()
        ventas_grafica = []
        for v in ventas_raw:
            etiqueta = str(v['etiqueta'])
            if es_un_dia: etiqueta = f"{etiqueta.zfill(2)}:00"
            ventas_grafica.append({"etiqueta": etiqueta, "total": float(v['total'])})

        return render_template('dashboard/index.html', 
                               active_page='Dashboard',
                               ventas_totales=ventas_totales,
                               ordenes_totales=ordenes_totales,
                               utilidad_bruta=utilidad_bruta,
                               gastos_operativos=gastos_operativos,
                               utilidad_neta=utilidad_neta,
                               ticket_promedio=ticket_promedio,
                               producto_estrella=producto_estrella,
                               top_productos=top_productos,
                               alertas_stock=alertas_stock,
                               ventas_grafica=ventas_grafica,
                               es_un_dia=es_un_dia,
                               fecha_inicio=fecha_inicio,
                               fecha_fin=fecha_fin)

    except Exception as e:
        print(f"Error crítico en Dashboard: {e}")
        return f"Error interno: {str(e)}", 500

@dashboard_bp.route('/dashboard/exportar')
@requiere_rol(['Administrador'])
def exportar_excel():
    """Genera el reporte Excel con pandas"""
    fecha_inicio = request.args.get('desde')
    fecha_fin = request.args.get('hasta')

    try:
        query = text("""
            SELECT 
                v.idVenta AS 'Folio',
                v.fecha AS 'Fecha y Hora',
                COALESCE(p.nombre, 'Producto Eliminado') AS 'Producto',
                dv.cantidad AS 'Cantidad',
                dv.precio AS 'Precio Unitario',
                (dv.cantidad * dv.precio) AS 'Subtotal'
            FROM ventas v
            JOIN detalleVenta dv ON v.idVenta = dv.idVenta
            LEFT JOIN productos p ON dv.idProducto = p.idProducto
            WHERE DATE(v.fecha) BETWEEN :inicio AND :fin
            ORDER BY v.fecha DESC
        """)
        
        res = db.session.execute(query, {"inicio": fecha_inicio, "fin": fecha_fin}).mappings().all()
        
        if not res: return "No hay ventas.", 404

        df = pd.DataFrame(res)
        df['Fecha y Hora'] = pd.to_datetime(df['Fecha y Hora']).dt.strftime('%d/%m/%Y %H:%M')

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Ventas')
        
        output.seek(0)
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         as_attachment=True, download_name=f"Reporte_Ventas_{fecha_inicio}.xlsx")
    except Exception as e:
        return f"Error: {e}", 500