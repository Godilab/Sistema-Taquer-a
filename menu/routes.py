from flask import Blueprint, render_template, request, jsonify
from sqlalchemy import text
from models import db
from security import requiere_rol

menu_bp = Blueprint('menu', __name__, template_folder='templates')

@menu_bp.route('/')
@requiere_rol(['Administrador', 'Cajero'])
def lista():
    try:
        # 1. Usamos SQL puro para traer los productos
        query = text("SELECT * FROM productos WHERE estado = 'activo' ORDER BY nombre ASC")
        productos = db.session.execute(query).mappings().all()
        
        categorias = ['Tacos', 'Gringas', 'Quesadillas', 'Bebidas', 'Postres', 'Paquetes']
        
        return render_template('menu/lista.html', 
                               active_page='Menu', 
                               productos=productos, 
                               categorias=categorias)
    except Exception as e:
        print(f"Error al listar: {e}")
        return f"Error en el Menú: {e}", 500

@menu_bp.route('/guardar', methods=['POST'])
@requiere_rol(['Administrador'])
def guardar():
    data = request.get_json()
    try:
        id_p = data.get('id')
        if id_p:
            # Lógica de ACTUALIZAR (Editar)
            sql = text("""
                UPDATE productos 
                SET nombre = :nom, precio = :pre, descripcion = :des, categoria = :cat 
                WHERE idProducto = :id
            """)
            db.session.execute(sql, {
                'nom': data['nombre'], 'pre': data['precio'], 
                'des': data['descripcion'], 'cat': data['categoria'], 'id': id_p
            })
        else:
            # Lógica de INSERTAR (Nuevo)
            sql = text("""
                INSERT INTO productos (nombre, precio, descripcion, categoria, estado) 
                VALUES (:nom, :pre, :des, :cat, 'activo')
            """)
            db.session.execute(sql, {
                'nom': data['nombre'], 'pre': data['precio'], 
                'des': data['descripcion'], 'cat': data['categoria']
            })
        
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        print(f"Error MySQL: {e}")
        return jsonify({"status": "error", "mensaje": str(e)}), 500
    

@menu_bp.route('/eliminar/<int:id>', methods=['POST'])
@requiere_rol(['Administrador'])
def eliminar(id):
    try:
        # En lugar de DELETE, hacemos un UPDATE del estado
        sql = text("UPDATE productos SET estado = 'inactivo' WHERE idProducto = :id")
        db.session.execute(sql, {'id': id})
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "mensaje": str(e)}), 500