from flask import Blueprint, render_template, request, jsonify
from sqlalchemy import text
from models import db
from security import requiere_rol

inventario_bp = Blueprint('inventario', __name__, template_folder='templates')
    
@inventario_bp.route('/')
@requiere_rol(['Administrador'])
def lista():
    try:
        # 1. Consulta de Insumos incluyendo unidadMinima y merma (factor de rendimiento)
        query = text("""
            SELECT idInsumo, nombre, categoria, stock, stockMinimo, 
                   costoUnidad, proveedor, unidadCompra, unidadMinima, merma 
            FROM insumos ORDER BY nombre ASC
        """)
        result = db.session.execute(query).mappings().all()
        
        # 2. Consulta de Proveedores Activos
        prov_query = text("SELECT nombre FROM proveedores WHERE estado = 'activo' ORDER BY nombre ASC")
        proveedores_raw = db.session.execute(prov_query).fetchall()
        lista_proveedores = [p[0] for p in proveedores_raw]

        insumos = []
        total_items = len(result)
        stock_bajo_count = 0
        valor_total = 0

        for row in result:
            actual = float(row['stock'] or 0)
            minimo = float(row['stockMinimo'] or 0)
            costo = float(row['costoUnidad'] or 0)
            # Factor de rendimiento (merma): ej. 0.75 para carne, 40 para tortillas
            factor = float(row['merma']) if row['merma'] else 1.0
            
            # CÁLCULO DE RENDIMIENTO OPERATIVO
            # Stock que realmente rinde para las recetas
            stock_operativo = actual * factor
            
            is_low = actual <= minimo
            if is_low: stock_bajo_count += 1
            valor_total += (actual * costo)

            insumos.append({
                'id': row['idInsumo'],
                'nombre': row['nombre'],
                'categoria': row['categoria'] or 'Otros',
                'stock': actual,
                'minimo': minimo,
                'costo': costo,
                'proveedor': row['proveedor'] or '',
                'unidad': row['unidadCompra'] or 'kg',
                'unidad_minima': row['unidadMinima'] or 'pza',
                'factor': factor,
                'stock_operativo': stock_operativo,
                'is_low': is_low
            })

        stats = {
            'total': total_items, 
            'ok': total_items - stock_bajo_count, 
            'bajo': stock_bajo_count, 
            'valor': valor_total
        }
        
        categorias = ['Carnes', 'Verduras', 'Tortillas', 'Bebidas', 'Abarrotes', 'Desechables', 'Limpieza', 'Otros']
        
        return render_template('inventario/lista.html', 
                               active_page='Inventory', 
                               insumos=insumos, stats=stats, proveedores=lista_proveedores,
                               categorias=categorias)
    except Exception as e:
        print(f"Error en Inventario: {e}")
        return f"Error de base de datos: {e}", 500

@inventario_bp.route('/guardar', methods=['POST'])
@requiere_rol(['Administrador'])
def guardar():
    try:
        data = request.get_json()
        id_insumo = data.get('id')
        
        # Incluimos unidad_minima (unidad operativa) y factor (merma)
        params = {
            'nom': data['nombre'], 
            'cat': data['categoria'], 
            'stk': data['stock'],
            'min': data['minimo'], 
            'cos': data['costo'], 
            'prov': data['proveedor'],
            'uni': data['unidad'],
            'uni_min': data['unidad_minima'],
            'mer': data.get('factor', 1.0)
        }

        if id_insumo:
            sql = text("""
                UPDATE insumos SET 
                    nombre=:nom, categoria=:cat, stock=:stk, 
                    stockMinimo=:min, costoUnidad=:cos, proveedor=:prov, 
                    unidadCompra=:uni, unidadMinima=:uni_min, merma=:mer 
                WHERE idInsumo=:id
            """)
            params['id'] = id_insumo
        else:
            sql = text("""
                INSERT INTO insumos (nombre, categoria, stock, stockMinimo, costoUnidad, proveedor, unidadCompra, unidadMinima, merma)
                VALUES (:nom, :cat, :stk, :min, :cos, :prov, :uni, :uni_min, :mer)
            """)
        
        db.session.execute(sql, params)
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        print(f"Error al guardar insumo: {e}")
        return jsonify({"status": "error", "mensaje": str(e)}), 500

@inventario_bp.route('/sumar/<int:id_insumo>', methods=['POST'])
@requiere_rol(['Administrador'])
def sumar(id_insumo):
    try:
        data = request.get_json()
        # El incremento de stock se hace siempre sobre la unidad de compra (física)
        db.session.execute(text("UPDATE insumos SET stock = stock + :c WHERE idInsumo = :id"), 
                           {'c': data['cantidad'], 'id': id_insumo})
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "mensaje": str(e)}), 500