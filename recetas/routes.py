from flask import Blueprint, render_template, request, jsonify
from sqlalchemy import text
from models import db
from security import requiere_rol

recetas_bp = Blueprint('recetas', __name__, template_folder='templates')

@recetas_bp.route('/')
@requiere_rol(['Administrador', 'Cocina'])
def lista():
    try:
        # 1. Consultar cabeceras de recetas activas
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
            # 2. Consultar detalles con datos de insumos
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
            detalles_edicion = [] # Arreglo saneado para el frontend
            costo_total_receta = 0.0 
            
            for d in detalles:
                cant_db = float(d['cantidad'])
                costo_kg_lt = float(d['costo_insumo'])
                uni_receta = (d['unidad_receta'] or 'pz').lower()
                
                # --- LÓGICA DE COSTEO PROFESIONAL ---
                if uni_receta in ['gr', 'ml']:
                    # La BD guarda el valor entero (ej. 50), se divide / 1000 para obtener el costo Kg/Lt
                    subtotal_ingrediente = (cant_db / 1000.0) * costo_kg_lt
                elif uni_receta == 'pz':
                    if "tortilla" in d['insumo_nombre'].lower():
                        subtotal_ingrediente = (cant_db / 40.0) * costo_kg_lt
                    else:
                        subtotal_ingrediente = cant_db * costo_kg_lt
                else:
                    subtotal_ingrediente = cant_db * costo_kg_lt

                costo_total_receta += subtotal_ingrediente

                # --- LÓGICA DE VISUALIZACIÓN PARA EL USUARIO ---
                cant_formateada = "{:,.0f}".format(cant_db) if cant_db % 1 == 0 else "{:,.2f}".format(cant_db)

                ingredientes_vista.append({
                    'nombre': d['insumo_nombre'],
                    'cantidad': cant_formateada,
                    'unidad': uni_receta
                })

                # --- LÓGICA DE EDICIÓN ---
                detalles_edicion.append({
                    'idInsumo': d['idInsumo'],
                    'cantidad': cant_db,
                    'unidad': uni_receta # Mapeo correcto de llave para evitar el 'pz' por defecto en JS
                })
            
            recetas_procesadas.append({
                'id': r['idReceta'],
                'idProducto': r['idProducto'],
                'producto': r['producto_nombre'],
                'rendimiento': r['rendimientoPorcion'] or 1,
                'ingredientes': ingredientes_vista,
                'costo_total': round(costo_total_receta, 2),
                'detalles_raw': detalles_edicion # Pasamos el arreglo estructuralmente correcto
            })

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
        id_producto = data.get('idProducto')
        rendimiento = data.get('rendimiento', 1)
        ingredientes = data.get('ingredientes', [])

        check_receta = db.session.execute(
            text("SELECT idReceta FROM recetas WHERE idProducto = :idP"), 
            {'idP': id_producto}
        ).mappings().first()

        if check_receta:
            id_receta = check_receta['idReceta']
            db.session.execute(
                text("UPDATE recetas SET rendimientoPorcion = :ren WHERE idReceta = :id"),
                {'ren': rendimiento, 'id': id_receta}
            )
            db.session.execute(text("DELETE FROM detallereceta WHERE idReceta = :id"), {'id': id_receta})
        else:
            res = db.session.execute(
                text("INSERT INTO recetas (idProducto, rendimientoPorcion) VALUES (:idP, :ren)"),
                {'idP': id_producto, 'ren': rendimiento}
            )
            id_receta = res.lastrowid

        # 2. Inserción Directa sin interferir en las conversiones
        for ing in ingredientes:
            cant_original = float(ing['cantidad'])
            unidad = str(ing['unidad']).lower()
            
            db.session.execute(
                text("""
                    INSERT INTO detallereceta (idReceta, idInsumo, cantidad, unidad) 
                    VALUES (:idR, :idI, :cant, :und)
                """), 
                {
                    'idR': id_receta, 
                    'idI': ing['idInsumo'], 
                    'cant': cant_original, # Se almacena la integridad de lo capturado (ej. 50 gr)
                    'und': unidad
                }
            )
        
        db.session.commit()
        return jsonify({"status": "success", "mensaje": "Receta guardada exitosamente"})
        
    except Exception as e:
        db.session.rollback()
        print(f"ERROR AL GUARDAR: {str(e)}")
        return jsonify({"status": "error", "mensaje": str(e)}), 500