import random
from datetime import datetime, timedelta
from flask_mail import Message
from sqlalchemy import text
from models import db
from extensions import mail
from functools import wraps
from flask import session, flash, redirect, url_for

# --- 1. FUNCIÓN PARA GENERAR Y ENVIAR 2FA ---
def generar_y_enviar_2fa(user_id, user_email):
    codigo = str(random.randint(100000, 999999))
    expiracion = datetime.now() + timedelta(minutes=10)
    
    try:
        # Invalidar cualquier código anterior (utilizado = 1)
        db.session.execute(text("""
            UPDATE two_factor_challenges 
            SET utilizado = 1 
            WHERE idUsuario = :id AND utilizado = 0
        """), {"id": user_id})
        
        # Guardar el NUEVO código
        query = text("""
            INSERT INTO two_factor_challenges (idUsuario, codigo_verificacion, expira_en)
            VALUES (:id, :code, :exp)
        """)
        db.session.execute(query, {"id": user_id, "code": codigo, "exp": expiracion})
        db.session.commit()
        
        # Enviar el correo
        msg = Message("Código de Acceso - Sistema Taquería", recipients=[user_email])
        msg.body = f"Tu código de seguridad es: {codigo}\nEste código expirará en 10 minutos."
        mail.send(msg)
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"Error al generar 2FA: {e}")
        return False

# --- 2. DECORADOR PARA RESTRINGIR RUTAS POR ROL ---
def requiere_rol(roles_permitidos):
    """
    Verifica que el usuario tenga uno de los roles autorizados.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Verificar si hay una sesión activa y un rol asignado
            if 'user_rol' not in session:
                # Si es un acceso temporal por 2FA, no tiene rol oficial aún
                if 'temp_user_id' in session:
                    return f(*args, **kwargs)
                
                flash('Por favor, inicia sesión para acceder.', 'warning')
                return redirect(url_for('usuarios.login'))
            
            # Verificar si el rol de la sesión está en la lista de permitidos
            if session.get('user_rol') not in roles_permitidos:
                flash('Acceso Denegado: No tienes permisos para esta sección.', 'danger')
                return redirect(url_for('dashboard.index')) # O tu ruta principal
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator