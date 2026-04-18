from flask import Blueprint, render_template, request, jsonify
from models import db, Merma, Insumo
from decimal import Decimal
from datetime import datetime
from security import requiere_rol

mermas_bp = Blueprint('mermas', __name__, template_folder='templates')

@mermas_bp.route('/')
@requiere_rol(['Administrador'])
def index():
    try:
        # Cargamos insumos ordenados para el selector
        insumos = Insumo.query.order_by(Insumo.nombre.asc()).all()
        # Cargamos el historial ordenado por fecha más reciente
        historial = Merma.query.order_by(Merma.fechaRegistro.desc()).all()
        return render_template('mermas/registro.html', 
                               insumos=insumos, 
                               historial=historial, 
                               active_page='Mermas')
    except Exception as e:
        print(f"Error al cargar vista de mermas: {e}")
        return f"Error al cargar la página: {e}", 500

@mermas_bp.route('/registrar', methods=['POST'])
@requiere_rol(['Administrador', 'Cocina'])
def registrar():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "mensaje": "No se recibieron datos"}), 400

        # 1. Validar existencia del insumo y conversión de datos
        insumo = Insumo.query.get(data['idInsumo'])
        if not insumo:
            return jsonify({"status": "error", "mensaje": "Insumo no encontrado"}), 404

        cantidad_merma = Decimal(str(data['cantidad']))

        # 2. REGLA DE NEGOCIO: Validar stock suficiente
        # No se puede mermar más de lo que hay físicamente en el refrigerador
        if insumo.stock < cantidad_merma:
            return jsonify({
                "status": "error", 
                "mensaje": f"Stock insuficiente. Solo hay {insumo.stock} {insumo.unidadCompra} disponibles."
            }), 400

        # 3. Crear el registro de merma
        nueva_merma = Merma(
            idInsumo=data['idInsumo'],
            idEmpleado=1, # Cambiar por el ID del usuario en sesión si es necesario
            cantidad=cantidad_merma,
            tipoMerma=data['tipo'],
            motivo=data['motivo'],
            fechaRegistro=datetime.now() # Aseguramos que se guarde el momento exacto
        )
        
        # 4. ACTUALIZACIÓN DEL INVENTARIO FÍSICO
        # Restamos directamente del stock crudo. 
        # Esto bajará automáticamente el 'Stock de Rendimiento' en tu Dashboard.
        insumo.stock -= cantidad_merma
        
        db.session.add(nueva_merma)
        db.session.commit()
        
        return jsonify({
            "status": "success", 
            "mensaje": "Merma registrada y stock físico actualizado correctamente"
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error en el registro de merma: {e}")
        return jsonify({"status": "error", "mensaje": str(e)}), 500