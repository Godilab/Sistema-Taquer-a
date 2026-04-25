from flask import Flask, render_template, session, redirect, url_for
from datetime import datetime
import locale
from models import db

# --- IMPORTACIONES NUEVAS PARA EL 2FA ---
from extensions import mail
from config import Config

# Importación de Blueprints 
from ventas.routes import ventas_bp
from cocina.routes import cocina_bp
from inventario.routes import inventario_bp
from proveedores.routes import proveedores_bp
from recetas.routes import recetas_bp
from menu.routes import menu_bp
from ventas.mermas.routes import mermas_bp
from ventas.compras.routes import compras_bp
from ventas.finanzas.routes import finanzas_bp
from dashboard_routes import dashboard_bp
from usuarios.routes import usuarios_bp
from public.routes import public_bp
from clientes.routes import clientes_bp

# Configuración de idioma
import locale
SUPPORTED_LOCALES = ["es_ES.UTF-8", "spanish", "es_MX.UTF-8"]
for loc in SUPPORTED_LOCALES:
    try:
        locale.setlocale(locale.LC_TIME, loc)
        break
    except locale.Error:
        continue

def create_app():
    app = Flask(__name__)
    
    # --- CONFIGURACIÓN GLOBAL ---
    # Esto carga tu correo, la BD y la contraseña de aplicación de Google
    app.config.from_object(Config)
    
    db.init_app(app)
    
    # --- INICIALIZACIÓN DEL CORREO ---
    mail.init_app(app)

    # Registro de Blueprints
    app.register_blueprint(public_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(ventas_bp, url_prefix='/ventas')
    app.register_blueprint(cocina_bp, url_prefix='/cocina')
    app.register_blueprint(inventario_bp, url_prefix='/inventario')
    app.register_blueprint(proveedores_bp, url_prefix='/proveedores')
    app.register_blueprint(recetas_bp, url_prefix='/recetas')
    app.register_blueprint(menu_bp, url_prefix='/menu')
    app.register_blueprint(mermas_bp, url_prefix='/mermas')
    app.register_blueprint(compras_bp, url_prefix='/compras')
    app.register_blueprint(finanzas_bp, url_prefix='/finanzas')
    app.register_blueprint(clientes_bp, url_prefix='/clientes')

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html', active_page=None), 404

    @app.route('/admin')
    def index_admin():
        if 'user_id' not in session:
            return redirect(url_for('usuarios.login'))
            
        now = datetime.now()
        contexto = {
            'saludo': 'Bienvenido',
            'fecha_actual': now.strftime("%A, %d de %B %Y"),
            'ventas_hoy': "4,500.00",
            'ordenes_hoy': 24,
            'en_cocina': 3,
            'active_page': 'Home'
        }
        return render_template('index.html', **contexto)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)