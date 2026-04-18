from flask import Blueprint, render_template, request, jsonify
from sqlalchemy import text
from models import db
from security import requiere_rol

recetas_bp = Blueprint('recetas', __name__, template_folder='templates')

@recetas_bp.route('/')
@requiere_rol(['Administrador', 'Cocina']) # Los cocineros pueden ver, pero no editar
def lista():
    try:
        # 1. Consultar cabeceras de recetas
        query = text("""
            SELECT r.idReceta, p.nombre as producto_nombre, r.idProducto, r.rendimientoPorcion
            FROM recetas r
            JOIN productos p ON r.idProducto = p.idProducto
            WHERE p.estado = 'activo'
            ORDER BY p.nombre ASC
        """)
        recetas_raw = db.session.execute(query).mappings().all()

        recetas_procesadas = []
        for r in recetas_raw:
            # 2. Consultar detalles incluyendo el COSTO y las UNIDADES para la conversión
            ing_query = text("""
                SELECT dr.idInsumo, dr.cantidad, dr.unidad as unidad_receta, 
                       i.nombre as insumo_nombre, COALESCE(i.costoUnidad, 0) as costo_insumo,
                       i.unidadCompra
                FROM detallereceta dr
                JOIN insumos i ON dr.idInsumo = i.idInsumo
                WHERE dr.idReceta = :id
            """)
            detalles = db.session.execute(ing_query, {'id': r['idReceta']}).mappings().all()
            
            ingredientes_vista = []
            costo_total_receta = 0.0 # Acumulador para el costo de producción
            
            for d in detalles:
                cant = float(d['cantidad'])
                costo_uni = float(d['costo_insumo'])
                
                # Normalización de unidades para validación técnica
                uni_receta = (d['unidad_receta'] or 'pz').lower()
                uni_compra = (d['unidadCompra'] or 'pz').lower()
                
                # --- LÓGICA DE CONVERSIÓN (EXPLOSIÓN DE MATERIALES) ---
                # Determinamos la cantidad real en términos de la unidad de compra
                cant_para_calculo = cant
                
                # Caso A: Receta en gramos (gr) y compra por kilogramo (kg)
                if uni_receta == 'gr' and uni_compra == 'kg':
                    cant_para_calculo = cant / 1000.0
                
                # Caso B: Receta en mililitros (ml) y compra por litro (l)
                elif uni_receta == 'ml' and uni_compra in ['l', 'litro', 'litros', 'lt']:
                    cant_para_calculo = cant / 1000.0
                
                # Caso C: Receta en piezas (pz) y compra por kilo (kg) - REGLA: 1kg = 40 tortillas
                elif uni_receta == 'pz' and uni_compra == 'kg':
                    cant_para_calculo = cant / 40.0 # Basado en la parametrización de piezas 

                # Cálculo del subtotal por ingrediente y suma al total de la receta
                subtotal_ingrediente = cant_para_calculo * costo_uni
                costo_total_receta += subtotal_ingrediente

                # Formateo de cantidad para la interfaz (ej: 2.0 -> 2)
                cant_final = "{:,.0f}".format(cant) if cant % 1 == 0 else "{:,.2f}".format(cant)

                ingredientes_vista.append({
                    'nombre': d['insumo_nombre'],
                    'cantidad': cant_final,
                    'unidad': d['unidad_receta'] or 'pz'
                })
            
            recetas_procesadas.append({
                'id': r['idReceta'],
                'idProducto': r['idProducto'],
                'producto': r['producto_nombre'],
                'rendimiento': r['rendimientoPorcion'] or 1,
                'ingredientes': ingredientes_vista,
                'costo_total': costo_total_receta, # Resultado final corregido
                'detalles_raw': [dict(d) for d in detalles]
            })

        # Listas para el modal de configuración de nuevas recetas
        productos_libres = db.session.execute(text("""
            SELECT idProducto, nombre FROM productos 
            WHERE estado='activo' AND idProducto NOT IN (SELECT idProducto FROM recetas)
        """)).mappings().all()
        
        insumos = db.session.execute(text("SELECT idInsumo, nombre FROM insumos ORDER BY nombre ASC")).mappings().all()

        return render_template('recetas/lista.html', 
                               active_page='Recipes', 
                               recetas=recetas_procesadas,
                               productos=productos_libres,
                               insumos=insumos)
    except Exception as e:
        print(f"Error crítico en GET recetas: {e}")
        return f"Error en el servidor: {e}", 500

@recetas_bp.route('/guardar', methods=['POST'])
@requiere_rol(['Administrador'])
def guardar():
    data = request.get_json()
    try:
        id_receta = data.get('id')
        
        # Iniciar transacción manual si es necesario, aunque session.execute lo maneja
        if id_receta:
            # ACTUALIZAR: Limpiar detalles viejos y actualizar rendimiento
            db.session.execute(text("DELETE FROM detallereceta WHERE idReceta = :id"), {'id': id_receta})
            db.session.execute(text("UPDATE recetas SET rendimientoPorcion = :ren WHERE idReceta = :id"), 
                               {'ren': data['rendimiento'], 'id': id_receta})
        else:
            # CREAR: Insertar nueva cabecera
            sql_r = text("INSERT INTO recetas (idProducto, rendimientoPorcion) VALUES (:idP, :ren)")
            res = db.session.execute(sql_r, {'idP': data['idProducto'], 'ren': data['rendimiento']})
            id_receta = res.lastrowid

        # 3. Inserción de los ingredientes con la UNIDAD seleccionada por el usuario
        for ing in data['ingredientes']:
            sql_d = text("""
                INSERT INTO detallereceta (idReceta, idInsumo, cantidad, unidad) 
                VALUES (:idR, :idI, :cant, :und)
            """)
            db.session.execute(sql_d, {
                'idR': id_receta, 
                'idI': ing['idInsumo'], 
                'cant': float(ing['cantidad']),
                'und': ing['unidad'] # Aquí se guarda 'gr' o 'pz' según el selector del modal
            })
        
        db.session.commit()
        return jsonify({"status": "success", "mensaje": "Receta guardada correctamente"})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error en POST guardar receta: {e}")
        return jsonify({"status": "error", "mensaje": str(e)}), 500