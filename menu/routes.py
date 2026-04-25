import os
import uuid
from flask import Blueprint, render_template, request, jsonify, current_app
from werkzeug.utils import secure_filename
from sqlalchemy import text
from models import db
from security import requiere_rol # [cite: 1]

menu_bp = Blueprint('menu', __name__, template_folder='templates')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    """Verifica si la extensión del archivo es permitida."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS # 

def guardar_imagen_producto(file_storage):
    """Procesa y guarda la imagen en el servidor."""
    if not file_storage or file_storage.filename == '':
        return None # 
    if not allowed_file(file_storage.filename):
        raise ValueError("Formato de imagen no permitido. Usa PNG, JPG, JPEG o WEBP.") # 

    nombre_seguro = secure_filename(file_storage.filename)
    extension = nombre_seguro.rsplit('.', 1)[1].lower()
    nombre_final = f"{uuid.uuid4().hex}.{extension}" # 

    carpeta_destino = os.path.join(current_app.root_path, 'static', 'img', 'productos')
    os.makedirs(carpeta_destino, exist_ok=True) # 

    ruta_fisica = os.path.join(carpeta_destino, nombre_final)
    file_storage.save(ruta_fisica) # 
    return f"/static/img/productos/{nombre_final}" # 

@menu_bp.route('/')
@requiere_rol(['Administrador', 'Cajero']) # [cite: 1]
def lista():
    try:
        query = text("""
            SELECT idProducto, nombre, precio, descripcion, categoria, imagen, estado 
            FROM productos WHERE estado = 'activo' ORDER BY nombre ASC
        """)
        result = db.session.execute(query).mappings().all() # [cite: 1]
        
        # CONVERSIÓN CRÍTICA: Transformar RowMapping a diccionarios serializables
        productos = [dict(row) for row in result] # [cite: 1, 3]
        
        categorias = ['Tacos', 'Gringas', 'Quesadillas', 'Bebidas', 'Postres', 'Paquetes'] # [cite: 1]
        
        return render_template('menu/lista.html', 
                               active_page='Menu', 
                               productos=productos, 
                               categorias=categorias) # [cite: 1]
    except Exception as e:
        print(f"Error al listar menú: {e}")
        return f"Error en el Menú: {e}", 500 # [cite: 11]

@menu_bp.route('/guardar', methods=['POST'])
@requiere_rol(['Administrador']) # [cite: 1]
def guardar():
    try:
        # Se usa request.form para capturar datos de un formulario multipart/form-data
        id_p = request.form.get('id') # 
        nombre = request.form.get('nombre', '').strip() # 
        precio = request.form.get('precio', '').strip() # 
        descripcion = request.form.get('descripcion', '').strip() # 
        categoria = request.form.get('categoria', '').strip() # 
        imagen_file = request.files.get('imagen') # 

        if not nombre or not precio or not categoria:
            return jsonify({"status": "error", "mensaje": "Faltan campos obligatorios"}), 400 # 

        nueva_ruta_imagen = None
        if imagen_file and imagen_file.filename != '':
            nueva_ruta_imagen = guardar_imagen_producto(imagen_file) # 

        if id_p:
            # Obtener imagen actual para mantenerla si no se subió una nueva
            prod_actual = db.session.execute(
                text("SELECT imagen FROM productos WHERE idProducto = :id"), {'id': id_p}
            ).mappings().first()
            
            img_final = nueva_ruta_imagen if nueva_ruta_imagen else (prod_actual['imagen'] if prod_actual else None) # 

            sql = text("""
                UPDATE productos 
                SET nombre = :nom, precio = :pre, descripcion = :des, categoria = :cat, imagen = :img 
                WHERE idProducto = :id
            """) # [cite: 1]
            db.session.execute(sql, {
                'nom': nombre, 'pre': precio, 'des': descripcion, 
                'cat': categoria, 'img': img_final, 'id': id_p
            }) # [cite: 1, 12]
        else:
            sql = text("""
                INSERT INTO productos (nombre, precio, descripcion, categoria, imagen, estado) 
                VALUES (:nom, :pre, :des, :cat, :img, 'activo')
            """) # [cite: 1]
            db.session.execute(sql, {
                'nom': nombre, 'pre': precio, 'des': descripcion, 
                'cat': categoria, 'img': nueva_ruta_imagen
            }) # [cite: 1, 12]
        
        db.session.commit()
        return jsonify({"status": "success", "mensaje": "Producto guardado correctamente"}) # 
    except ValueError as ve:
        return jsonify({"status": "error", "mensaje": str(ve)}), 400 # [cite: 16]
    except Exception as e:
        db.session.rollback()
        print(f"Error MySQL en menú: {e}")
        return jsonify({"status": "error", "mensaje": str(e)}), 500 # [cite: 16]

@menu_bp.route('/eliminar/<int:id>', methods=['POST'])
@requiere_rol(['Administrador']) # [cite: 1]
def eliminar(id):
    try:
        # Eliminación lógica cambiando el estado a inactivo
        sql = text("UPDATE productos SET estado = 'inactivo' WHERE idProducto = :id") # [cite: 1]
        db.session.execute(sql, {'id': id}) # [cite: 1]
        db.session.commit()
        return jsonify({"status": "success", "mensaje": "Producto eliminado"}) # [cite: 15, 16]
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "mensaje": str(e)}), 500 # [cite: 16]