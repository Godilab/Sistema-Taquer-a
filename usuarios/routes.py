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

# ==============================
# 🔑 AUTENTICACIÓN (LOGIN & 2FA)
# ==============================

@usuarios_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            # LEFT JOIN para evitar errores si el idRol es NULL en la DB
            query = text("""
                SELECT u.idUsuario, p.nombre, u.password, u.email, r.nombreRol AS rol
                FROM usuarios u
                JOIN empleados e ON u.idEmpleado = e.idEmpleado
                JOIN personas p ON e.idPersona = p.idPersona
                LEFT JOIN roles r ON u.idRol = r.idRol
                WHERE u.email = :email AND u.estado = 'activo'
            """)
            user = db.session.execute(query, {"email": email}).mappings().first()
            
            if user and user['password'] == password:
                # FLUJO PARA ADMINISTRADOR (2FA OBLIGATORIO)
                if user['rol'] == 'Administrador':
                    session['temp_user_id'] = user['idUsuario']
                    session['temp_user_name'] = user['nombre']
                    session['temp_user_rol'] = user['rol']
                    
                    if generar_y_enviar_2fa(user['idUsuario'], user['email']):
                        flash('Hemos enviado un código a tu correo.', 'info')
                    else:
                        # RESPALDO: Imprimir código en terminal si falla el SMTP
                        res_code = db.session.execute(text("""
                            SELECT codigo_verificacion FROM two_factor_challenges 
                            WHERE idUsuario = :id ORDER BY idChallenge DESC LIMIT 1
                        """), {"id": user['idUsuario']}).mappings().first()
                        
                        print("\n" + "!"*50)
                        print(f"🔑 CÓDIGO DE EMERGENCIA (ADMIN): {res_code['codigo_verificacion']}")
                        print("!"*50 + "\n")
                        flash('Aviso: El código de acceso se imprimió en la terminal.', 'warning')
                    
                    return redirect(url_for('usuarios.verificar_2fa'))
                
                # FLUJO PARA OTROS ROLES
                else:
                    session['user_id'] = user['idUsuario']
                    session['user_name'] = user['nombre']
                    session['user_rol'] = user['rol']
                    flash(f'¡Bienvenido, {user["nombre"]}!', 'success')
                    return redirect(url_for('index_admin'))
            else:
                flash('Credenciales incorrectas.', 'danger')
        except Exception as e:
            flash(f'Error en el acceso: {e}', 'danger')
            
    return render_template('login.html')

@usuarios_bp.route('/verificar_2fa', methods=['GET', 'POST'])
def verificar_2fa():
    if 'temp_user_id' not in session:
        return redirect(url_for('usuarios.login'))

    if request.method == 'POST':
        codigo_ingresado = request.form.get('codigo')
        user_id = session['temp_user_id']

        try:
            query = text("""
                SELECT idChallenge, codigo_verificacion, expira_en
                FROM two_factor_challenges
                WHERE idUsuario = :id AND utilizado = 0 AND tipo_token = 'login'
                ORDER BY idChallenge DESC LIMIT 1
            """)
            challenge = db.session.execute(query, {"id": user_id}).mappings().first()

            if challenge:
                if datetime.now() > challenge['expira_en']:
                    flash('El código ha expirado.', 'danger')
                    return redirect(url_for('usuarios.login'))

                if challenge['codigo_verificacion'] == codigo_ingresado:
                    db.session.execute(text("UPDATE two_factor_challenges SET utilizado = 1 WHERE idChallenge = :idc"), 
                                       {"idc": challenge['idChallenge']})
                    db.session.commit()

                    session['user_id'] = session.pop('temp_user_id')
                    session['user_name'] = session.pop('temp_user_name')
                    session['user_rol'] = session.pop('temp_user_rol')

                    flash('Acceso autorizado.', 'success')
                    return redirect(url_for('index_admin'))
                else:
                    flash('Código incorrecto.', 'danger')
            else:
                flash('No hay códigos pendientes.', 'danger')
                return redirect(url_for('usuarios.login'))
        except Exception as e:
            flash(f'Error de verificación: {e}', 'danger')

    return render_template('verificar_2fa.html')

@usuarios_bp.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('usuarios.login'))

# ==============================
# 👥 GESTIÓN DE USUARIOS
# ==============================

@usuarios_bp.route('/usuarios/')
@login_required
@requiere_rol(['Administrador'])
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
@requiere_rol(['Administrador'])
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
        flash('Usuario agregado correctamente.', 'success')
        return redirect(url_for('usuarios.index'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error al agregar: {e}", "danger")
        return redirect(url_for('usuarios.index'))

@usuarios_bp.route('/usuarios/editar', methods=['POST'])
@login_required
@requiere_rol(['Administrador'])
def editar():
    id_u = request.form.get('idUsuario')
    nombre = request.form.get('nombre')
    email = request.form.get('email')
    rol_n = request.form.get('rol')
    nueva_pw = request.form.get('password')

    try:
        # BLOQUEO DE SEGURIDAD: Si el admin se edita a sí mismo, no permitimos cambiar el rol
        # Esto evita que el único admin se degrade a Cajero o Cocina por error.
        es_auto_edicion = str(id_u) == str(session.get('user_id'))
        
        # 1. Actualizar Nombre
        db.session.execute(text("""
            UPDATE personas p 
            JOIN empleados e ON p.idPersona = e.idPersona 
            JOIN usuarios u ON e.idEmpleado = u.idEmpleado 
            SET p.nombre = :n WHERE u.idUsuario = :id
        """), {"n": nombre, "id": id_u})

        # 2. Lógica de actualización de Usuario
        if es_auto_edicion:
            # Si eres tú, actualizamos todo MENOS el rol
            if nueva_pw and nueva_pw.strip() != "":
                db.session.execute(text("UPDATE usuarios SET email = :e, password = :pw WHERE idUsuario = :id"),
                                   {"e": email, "pw": nueva_pw, "id": id_u})
            else:
                db.session.execute(text("UPDATE usuarios SET email = :e WHERE idUsuario = :id"),
                                   {"e": email, "id": id_u})
            flash('Perfil actualizado (El rol de Administrador está protegido).', 'success')
        else:
            # Si estás editando a otro, procedemos normal incluyendo el cambio de rol
            id_r = db.session.execute(text("SELECT idRol FROM roles WHERE nombreRol = :r"), {"r": rol_n}).scalar()
            if nueva_pw and nueva_pw.strip() != "":
                db.session.execute(text("UPDATE usuarios SET email = :e, idRol = :r, password = :pw WHERE idUsuario = :id"),
                                   {"e": email, "r": id_r, "pw": nueva_pw, "id": id_u})
            else:
                db.session.execute(text("UPDATE usuarios SET email = :e, idRol = :r WHERE idUsuario = :id"),
                                   {"e": email, "r": id_r, "id": id_u})
            flash('Colaborador actualizado correctamente.', 'success')

        db.session.commit()
        return redirect(url_for('usuarios.index'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error al editar: {e}", "danger")
        return redirect(url_for('usuarios.index'))

@usuarios_bp.route('/usuarios/eliminar/<int:id>')
@login_required
@requiere_rol(['Administrador'])
def eliminar(id):
    try:
        # PROTECCIÓN DE CUENTA RAÍZ: No permitir eliminar administradores ni a uno mismo
        query_check = text("""
            SELECT r.nombreRol AS rol FROM usuarios u 
            JOIN roles r ON u.idRol = r.idRol WHERE u.idUsuario = :id
        """)
        user_to_delete = db.session.execute(query_check, {"id": id}).mappings().first()

        if user_to_delete and user_to_delete['rol'] == 'Administrador':
            flash('⚠️ Seguridad: No es posible eliminar cuentas de Administrador.', 'warning')
            return redirect(url_for('usuarios.index'))

        if id == session.get('user_id'):
            flash('No puedes eliminar tu propia cuenta activa.', 'danger')
            return redirect(url_for('usuarios.index'))

        db.session.execute(text("UPDATE usuarios SET estado = 'inactivo' WHERE idUsuario = :id"), {"id": id})
        db.session.commit()
        flash('Usuario dado de baja.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar: {e}", "danger")
    
    return redirect(url_for('usuarios.index'))

# ==============================
# 🛠️ MANTENIMIENTO BD
# ==============================

@usuarios_bp.route('/respaldar_bd')
@login_required
@requiere_rol(['Administrador'])
def respaldar_bd():
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
        
        res = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        
        if not res.stdout:
            return f"Error en MySQL: {res.stderr}", 500

        out = re.sub(r'DEFINER\s*=\s*`[^`]+`@`[^`]+`|DEFINER\s*=\s*[^\s]+', '', res.stdout)
        out = re.sub(r'/\*!([0-9]+)\s+(DEFINER|SET|@@)[^*]*\*/', '', out)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(out)
            
        return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e: 
        return f"Error en respaldo: {e}", 500

@usuarios_bp.route('/restaurar_bd', methods=['POST'])
@login_required
@requiere_rol(['Administrador'])
def restaurar_bd():
    archivo = request.files['archivo_sql']
    temp = os.path.join(os.getcwd(), 'temp_rest.sql')
    
    try:
        try:
            raw = archivo.read().decode('utf-8')
        except UnicodeDecodeError:
            archivo.seek(0)
            raw = archivo.read().decode('latin-1')
        
        limpias = [l for l in raw.splitlines() if not any(x in l for x in ["SET @@", "GTID_PURGED", "DEFINER"])]
        script = "SET FOREIGN_KEY_CHECKS = 0;\n" + "\n".join(limpias) + "\nSET FOREIGN_KEY_CHECKS = 1;"
        
        with open(temp, 'w', encoding='utf-8') as f:
            f.write(script)
            
        env = os.environ.copy()
        env['MYSQL_PWD'] = 'Admin123'
        mysql = r'C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe'
        
        with open(temp, 'r', encoding='utf-8') as f:
            subprocess.run([mysql, '-u', 'adminDB', 'taqueria'], env=env, stdin=f)
            
        os.remove(temp)
        flash("Base de datos restaurada correctamente.", "success")
        return redirect(url_for('usuarios.index'))
    except Exception as e:
        if os.path.exists(temp): os.remove(temp)
        return f"Error en restauración: {e}", 500