from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file
from sqlalchemy import text
from models import db
from functools import wraps
import os
import subprocess
import re
from datetime import datetime
from security import generar_y_enviar_2fa, requiere_rol

usuarios_bp = Blueprint('usuarios', __name__, template_folder='templates')

# --- DECORADOR PARA PROTEGER RUTAS ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, inicia sesión para acceder.', 'warning')
            return redirect(url_for('usuarios.login'))
        return f(*args, **kwargs)
    return decorated_function

# --- RUTAS DE AUTENTICACIÓN ---

from security import generar_y_enviar_2fa # Agrega esta importación al inicio

from security import generar_y_enviar_2fa # <-- Agrega esta importación al inicio del archivo

@usuarios_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            query = text("""
                SELECT u.idUsuario, p.nombre, u.password, u.email, r.nombreRol AS rol
                FROM usuarios u
                JOIN empleados e ON u.idEmpleado = e.idEmpleado
                JOIN personas p ON e.idPersona = p.idPersona
                JOIN roles r ON u.idRol = r.idRol
                WHERE u.email = :email AND u.estado = 'activo'
            """)
            user = db.session.execute(query, {"email": email}).mappings().first()
            
            if user and user['password'] == password:
                # CREDENCIALES CORRECTAS -> DISPARAR 2FA
                
                # Guardamos datos temporales para cuando ingrese el código
                session['temp_user_id'] = user['idUsuario']
                session['temp_user_name'] = user['nombre']
                session['temp_user_rol'] = user['rol']
                
                # Intentamos enviar el correo
                if generar_y_enviar_2fa(user['idUsuario'], user['email']):
                    flash('Hemos enviado un código de 6 dígitos a tu correo.', 'info')
                    # Redirigir a la pantalla donde se ingresa el código
                    # (Si aún no tienes esta vista, te marcará error de redirección, pero el correo ya debería llegar)
                    return redirect(url_for('usuarios.verificar_2fa'))
                else:
                    flash('Error al enviar el correo de verificación.', 'danger')
            else:
                flash('Credenciales incorrectas.', 'danger')
        except Exception as e:
            flash(f'Error en el login: {e}', 'danger')
            
    return render_template('login.html')



from datetime import datetime

@usuarios_bp.route('/verificar_2fa', methods=['GET', 'POST'])
def verificar_2fa():
    # Si el usuario intenta entrar aquí sin haber pasado por el login primero
    if 'temp_user_id' not in session:
        return redirect(url_for('usuarios.login'))

    if request.method == 'POST':
        codigo_ingresado = request.form.get('codigo')
        user_id = session['temp_user_id']

        try:
            # Buscamos el código más reciente generado para este usuario
            query = text("""
            SELECT idChallenge, codigo_verificacion, expira_en
            FROM two_factor_challenges
            WHERE idUsuario = :id AND utilizado = 0 AND tipo_token = 'login'
            ORDER BY idChallenge DESC LIMIT 1
        """)
            challenge = db.session.execute(query, {"id": user_id}).mappings().first()

            if challenge:
                # 1. Validar que no haya expirado (pasaron más de 10 min)
                if datetime.now() > challenge['expira_en']:
                    flash('El código ha expirado. Inicia sesión nuevamente.', 'danger')
                    session.pop('temp_user_id', None)
                    return redirect(url_for('usuarios.login'))

                # 2. Validar que el código ingresado sea el correcto
                if challenge['codigo_verificacion'] == codigo_ingresado:
                    # ¡ÉXITO! Marcamos el código como utilizado
                    db.session.execute(text("UPDATE two_factor_challenges SET utilizado = 1 WHERE idChallenge = :idc"), 
                                       {"idc": challenge['idChallenge']})
                    db.session.commit()

                    # Transferimos la sesión temporal a una sesión oficial y activa
                    session['user_id'] = session.pop('temp_user_id')
                    session['user_name'] = session.pop('temp_user_name')
                    session['user_rol'] = session.pop('temp_user_rol')

                    flash(f'¡Bienvenido, {session["user_name"]}!', 'success')
                    return redirect(url_for('index_admin'))
                else:
                    flash('Código incorrecto. Verifica tu correo.', 'danger')
            else:
                flash('No hay códigos pendientes. Inicia sesión.', 'danger')
                return redirect(url_for('usuarios.login'))

        except Exception as e:
            flash(f'Error al verificar: {e}', 'danger')

    # Si es método GET, solo mostramos el formulario
    return render_template('verificar_2fa.html')

@usuarios_bp.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('usuarios.login'))

# --- GESTIÓN DE USUARIOS ---

@usuarios_bp.route('/usuarios/')
@login_required
@requiere_rol(['Administrador']) # <-- AGREGA ESTA LÍNEA
def index():
    try:
        query = text("""
            SELECT u.idUsuario, p.nombre, u.email, r.nombreRol AS rol
            FROM usuarios u
            JOIN empleados e ON u.idEmpleado = e.idEmpleado
            JOIN personas p ON e.idPersona = p.idPersona
            JOIN roles r ON u.idRol = r.idRol
            WHERE u.estado = 'activo' ORDER BY p.nombre ASC
        """)
        usuarios = db.session.execute(query).mappings().all()
        return render_template('usuarios/index.html', usuarios=usuarios, active_page='Employees')
    except Exception as e:
        return f"Error: {e}", 500

@usuarios_bp.route('/usuarios/agregar', methods=['POST'])
@login_required
@requiere_rol(['Administrador']) # <-- AGREGA ESTA LÍNEA
def agregar():
    nombre = request.form.get('nombre')
    email = request.form.get('email')
    password = request.form.get('password')
    rol_nombre = request.form.get('rol')
    try:
        db.session.execute(text("INSERT INTO personas (nombre) VALUES (:n)"), {"n": nombre})
        id_p = db.session.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        db.session.execute(text("INSERT INTO empleados (idPersona, puesto) VALUES (:id, :p)"), {"id": id_p, "p": rol_nombre})
        id_e = db.session.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        id_r = db.session.execute(text("SELECT idRol FROM roles WHERE nombreRol = :r"), {"r": rol_nombre}).scalar()
        db.session.execute(text("INSERT INTO usuarios (idEmpleado, email, password, idRol, estado) VALUES (:e, :em, :pw, :r, 'activo')"),
                           {"e": id_e, "em": email, "pw": password, "r": id_r})
        db.session.commit()
        return redirect(url_for('usuarios.index'))
    except Exception as e:
        db.session.rollback()
        return f"Error al agregar: {e}", 500

@usuarios_bp.route('/usuarios/editar', methods=['POST'])
@login_required
@requiere_rol(['Administrador']) # <-- AGREGA ESTA LÍNEA
def editar():
    id_u = request.form.get('idUsuario')
    nombre = request.form.get('nombre')
    email = request.form.get('email')
    rol_n = request.form.get('rol')
    try:
        db.session.execute(text("UPDATE personas p JOIN empleados e ON p.idPersona = e.idPersona JOIN usuarios u ON e.idEmpleado = u.idEmpleado SET p.nombre = :n WHERE u.idUsuario = :id"), {"n": nombre, "id": id_u})
        id_r = db.session.execute(text("SELECT idRol FROM roles WHERE nombreRol = :r"), {"r": rol_n}).scalar()
        db.session.execute(text("UPDATE usuarios SET email = :e, idRol = :r WHERE idUsuario = :id"), {"e": email, "r": id_r, "id": id_u})
        db.session.commit()
        return redirect(url_for('usuarios.index'))
    except Exception as e:
        db.session.rollback()
        return f"Error al editar: {e}", 500

@usuarios_bp.route('/usuarios/eliminar/<int:id>')
@login_required
@requiere_rol(['Administrador']) # <-- AGREGA ESTA LÍNEA
def eliminar(id):
    try:
        db.session.execute(text("UPDATE usuarios SET estado = 'inactivo' WHERE idUsuario = :id"), {"id": id})
        db.session.commit()
        return redirect(url_for('usuarios.index'))
    except Exception as e:
        db.session.rollback()
        return f"Error al eliminar: {e}", 500

# --- MANTENIMIENTO BD (RESPALDO Y RESTAURACIÓN) ---

@usuarios_bp.route('/respaldar_bd')
@login_required
@requiere_rol(['Administrador']) # <-- AGREGA ESTA LÍNEA
def respaldar_bd():
    if session.get('user_rol') != 'Administrador': 
        return "Acceso denegado", 403
    
    fecha = datetime.now().strftime('%Y-%m-%d_%H-%M')
    filename = f"RESPALDO_TAQUERIA_{fecha}.sql"
    filepath = os.path.join(os.getcwd(), filename)
    
    try:
        env = os.environ.copy()
        env['MYSQL_PWD'] = 'Admin123'
        mysqldump = r'C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe'
        
        cmd = [
            mysqldump, '-u', 'adminDB', 
            '--add-drop-table', '--routines', '--triggers', 
            '--no-tablespaces', '--column-statistics=0', 
            '--set-gtid-purged=OFF', '--skip-comments', 'taqueria'
        ]
        
        # Forzamos encoding utf-8 para que la 'ñ' no se rompa
        res = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        
        if not res.stdout:
            return f"Error en MySQL: {res.stderr}", 500

        # Limpieza profunda de privilegios y definidores
        out = re.sub(r'DEFINER\s*=\s*`[^`]+`@`[^`]+`|DEFINER\s*=\s*[^\s]+', '', res.stdout)
        out = re.sub(r'/\*!([0-9]+)\s+(DEFINER|SET|@@)[^*]*\*/', '', out)
        out = re.sub(r'SET\s+@@(GLOBAL|SESSION)\.[^;]+;', '', out)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(out)
            
        return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e: 
        return f"Error en respaldo: {e}", 500

@usuarios_bp.route('/restaurar_bd', methods=['POST'])
@login_required
@requiere_rol(['Administrador']) # <-- AGREGA ESTA LÍNEA
def restaurar_bd():
    if session.get('user_rol') != 'Administrador': 
        return "Acceso denegado", 403
    
    archivo = request.files['archivo_sql']
    temp = os.path.join(os.getcwd(), 'temp_rest.sql')
    
    try:
        # Intentar leer en UTF-8, si falla por la 'ñ' mal codificada, usar latin-1
        try:
            raw = archivo.read().decode('utf-8')
        except UnicodeDecodeError:
            archivo.seek(0)
            raw = archivo.read().decode('latin-1')
        
        # Filtrado preventivo de líneas de sistema que causan ERROR 1227
        limpias = [l for l in raw.splitlines() if not any(x in l for x in ["SET @@", "GTID_PURGED", "DEFINER"])]
        
        # Inyectamos desactivación de llaves foráneas para evitar ERROR 3730
        script = (
            "SET FOREIGN_KEY_CHECKS = 0;\n"
            "SET SQL_MODE = '';\n" 
            + "\n".join(limpias) + 
            "\nSET FOREIGN_KEY_CHECKS = 1;"
        )
        
        with open(temp, 'w', encoding='utf-8') as f:
            f.write(script)
            
        env = os.environ.copy()
        env['MYSQL_PWD'] = 'Admin123'
        mysql = r'C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe'
        
        with open(temp, 'r', encoding='utf-8') as f:
            subprocess.run([mysql, '-u', 'adminDB', 'taqueria'], env=env, stdin=f)
            
        os.remove(temp)
        flash("✅ Base de datos restaurada correctamente.", "success")
        return redirect(url_for('usuarios.index'))
        
    except Exception as e:
        if os.path.exists(temp): os.remove(temp)
        return f"Error en restauración: {e}", 500