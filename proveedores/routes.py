from flask import Blueprint, render_template, request, jsonify
from sqlalchemy import text
from models import db
from security import requiere_rol

proveedores_bp = Blueprint('proveedores', __name__, template_folder='templates')

@proveedores_bp.route('/')
@requiere_rol(['Administrador']) 
def lista():
    try:
        query = text("SELECT idProveedor, nombre, telefono, direccion, estado FROM proveedores ORDER BY nombre ASC")
        result = db.session.execute(query).mappings().all()
        
        proveedores = []
        for row in result:
            proveedores.append({
                'id': row['idProveedor'],
                'name': row['nombre'],
                'phone': row['telefono'] or '',
                'address': row['direccion'] or '',
                'active': row['estado'] == 'activo'
            })
            
        return render_template('proveedores/lista.html', 
                               proveedores=proveedores, 
                               active_page='Proveedores')
    except Exception as e:
        return f"Error en proveedores: {e}", 500

@proveedores_bp.route('/guardar', methods=['POST'])
@requiere_rol(['Administrador']) 
def guardar():
    try:
        data = request.get_json()
        id_prov = data.get('id')
        estado = 'activo' if data.get('active', True) else 'inactivo'
        
        params = {
            'nom': data['name'], 'tel': data['phone'], 
            'dir': data['address'], 'est': estado
        }

        if id_prov:
            sql = text("UPDATE proveedores SET nombre=:nom, telefono=:tel, direccion=:dir, estado=:est WHERE idProveedor=:id")
            params['id'] = id_prov
        else:
            sql = text("INSERT INTO proveedores (nombre, telefono, direccion, estado) VALUES (:nom, :tel, :dir, :est)")
        
        db.session.execute(sql, params)
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "mensaje": str(e)}), 500

@proveedores_bp.route('/toggle/<int:id_prov>', methods=['POST'])
@requiere_rol(['Administrador']) 
def toggle_status(id_prov):
    try:
        # Primero obtenemos el estado actual
        res = db.session.execute(text("SELECT estado FROM proveedores WHERE idProveedor = :id"), {'id': id_prov}).fetchone()
        nuevo_estado = 'inactivo' if res[0] == 'activo' else 'activo'
        
        db.session.execute(text("UPDATE proveedores SET estado = :est WHERE idProveedor = :id"), 
                           {'est': nuevo_estado, 'id': id_prov})
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "mensaje": str(e)}), 500