from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text
from models import db
import random
import smtplib
from email.mime.text import MIMEText

# DEFINIMOS EL BLUEPRINT DIRECTAMENTE AQUÍ (Reemplaza el 'from . import clientes_bp')
clientes_bp = Blueprint('clientes', __name__, template_folder='templates')

# =========================
# CONFIG CORREO
# =========================
EMAIL = "gp760642@gmail.com"
PASSWORD = "onql lpox tghm igal"


def enviar_codigo(destinatario, codigo):
    msg = MIMEText(f"Tu código de verificación es: {codigo}")
    msg["Subject"] = "Verificación de cuenta"
    msg["From"] = EMAIL
    msg["To"] = destinatario

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(EMAIL, PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print("Error enviando correo:", e)


# =========================
# REGISTRO
# =========================
@clientes_bp.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        try:
            nombre = request.form.get("nombre", "").strip()
            correo = request.form.get("correo", "").strip().lower()
            telefono = request.form.get("telefono", "").strip()
            password_raw = request.form.get("password", "").strip()

            print("=== REGISTRO CLIENTE ===")
            print("nombre:", nombre)
            print("correo:", correo)
            print("telefono:", telefono)

            if not nombre or not correo or not password_raw:
                flash("Completa todos los campos obligatorios", "error")
                return redirect(url_for("clientes.registro"))

            query = text("""
                SELECT idCliente
                FROM clientes
                WHERE correo = :correo
                LIMIT 1
            """)
            cliente_existente = db.session.execute(
                query, {"correo": correo}
            ).mappings().first()

            print("cliente_existente:", cliente_existente)

            if cliente_existente is not None:
                flash("Este correo ya está registrado", "error")
                return redirect(url_for("clientes.registro"))

            codigo = str(random.randint(100000, 999999))
            password_hash = generate_password_hash(password_raw)

            insert_sql = text("""
                INSERT INTO clientes (
                    nombre,
                    correo,
                    password,
                    telefono,
                    verificado,
                    codigo_verificacion
                )
                VALUES (
                    :nombre,
                    :correo,
                    :password,
                    :telefono,
                    0,
                    :codigo
                )
            """)

            db.session.execute(insert_sql, {
                "nombre": nombre,
                "correo": correo,
                "password": password_hash,
                "telefono": telefono,
                "codigo": codigo
            })
            db.session.commit()

            enviar_codigo(correo, codigo)

            flash("Revisa tu correo para verificar tu cuenta", "success")
            return redirect(url_for("clientes.verificar", correo=correo))

        except Exception as e:
            db.session.rollback()
            print("Error en registro cliente:", e)
            flash(f"Error al registrar: {e}", "error")
            return redirect(url_for("clientes.registro"))

    return render_template("registro.html")


# =========================
# VERIFICACIÓN DE CUENTA
# =========================
@clientes_bp.route("/verificar/<correo>", methods=["GET", "POST"])
def verificar(correo):
    try:
        query = text("""
            SELECT idCliente, correo, codigo_verificacion, verificado
            FROM clientes
            WHERE correo = :correo
            LIMIT 1
        """)
        cliente = db.session.execute(
            query, {"correo": correo}
        ).mappings().first()

        if not cliente:
            flash("Cliente no encontrado", "error")
            return redirect(url_for("clientes.registro"))

        if request.method == "POST":
            codigo = request.form.get("codigo", "").strip()

            if cliente["codigo_verificacion"] == codigo:
                update_sql = text("""
                    UPDATE clientes
                    SET verificado = 1,
                        codigo_verificacion = NULL
                    WHERE correo = :correo
                """)
                db.session.execute(update_sql, {"correo": correo})
                db.session.commit()

                flash("Cuenta verificada, ahora inicia sesión", "success")
                return redirect(url_for("clientes.login"))
            else:
                flash("Código incorrecto", "error")

        return render_template("verificar.html", correo=correo)

    except Exception as e:
        db.session.rollback()
        print("Error en verificación:", e)
        flash(f"Error al verificar: {e}", "error")
        return redirect(url_for("clientes.registro"))


# =========================
# LOGIN
# =========================
@clientes_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            correo = request.form.get("correo", "").strip().lower()
            password = request.form.get("password", "").strip()

            query = text("""
                SELECT idCliente, nombre, correo, telefono, password, verificado
                FROM clientes
                WHERE correo = :correo
                LIMIT 1
            """)
            cliente = db.session.execute(
                query, {"correo": correo}
            ).mappings().first()

            print("=== LOGIN CLIENTE ===")
            print("correo:", correo)
            print("cliente encontrado:", cliente)

            if not cliente:
                flash("Datos incorrectos", "error")
                return render_template("loginClientes.html")

            if not check_password_hash(cliente["password"], password):
                flash("Datos incorrectos", "error")
                return render_template("loginClientes.html")

            if not cliente["verificado"]:
                flash("Primero verifica tu cuenta desde tu correo", "error")
                return redirect(url_for("clientes.verificar", correo=correo))

            codigo = str(random.randint(100000, 999999))

            update_sql = text("""
                UPDATE clientes
                SET codigo_verificacion = :codigo
                WHERE correo = :correo
            """)
            db.session.execute(update_sql, {
                "codigo": codigo,
                "correo": correo
            })
            db.session.commit()

            enviar_codigo(correo, codigo)

            session["temp_cliente"] = correo

            flash("Te enviamos un código de verificación", "success")
            return redirect(url_for("clientes.verificar_login"))

        except Exception as e:
            db.session.rollback()
            print("Error en login cliente:", e)
            flash(f"Error al iniciar sesión: {e}", "error")

    return render_template("loginClientes.html")


# =========================
# VERIFICAR LOGIN
# =========================
@clientes_bp.route("/verificar_login", methods=["GET", "POST"])
def verificar_login():
    correo = session.get("temp_cliente")

    if not correo:
        return redirect(url_for("clientes.login"))

    try:
        query = text("""
            SELECT idCliente, nombre, correo, telefono, codigo_verificacion
            FROM clientes
            WHERE correo = :correo
            LIMIT 1
        """)
        cliente = db.session.execute(
            query, {"correo": correo}
        ).mappings().first()

        if not cliente:
            flash("Cliente no encontrado", "error")
            return redirect(url_for("clientes.login"))

        if request.method == "POST":
            codigo = request.form.get("codigo", "").strip()

            if cliente["codigo_verificacion"] == codigo:
                session.pop("temp_cliente", None)
                session["cliente_id"] = cliente["idCliente"]
                session["cliente_nombre"] = cliente["nombre"]
                session["cliente_telefono"] = cliente["telefono"]

                limpiar_codigo = text("""
                    UPDATE clientes
                    SET codigo_verificacion = NULL
                    WHERE idCliente = :idCliente
                """)
                db.session.execute(limpiar_codigo, {
                    "idCliente": cliente["idCliente"]
                })
                db.session.commit()

                flash("Bienvenido 👋", "success")
                return redirect(url_for("public.menu_digital"))
            else:
                flash("Código incorrecto", "error")

        return render_template("verificar.html", correo=correo)

    except Exception as e:
        db.session.rollback()
        print("Error en verificar login:", e)
        flash(f"Error al verificar login: {e}", "error")
        return redirect(url_for("clientes.login"))


# =========================
# LOGOUT
# =========================
@clientes_bp.route("/logout")
def logout():
    session.pop("cliente_id", None)
    session.pop("cliente_nombre", None)
    session.pop("cliente_telefono", None)
    session.pop("temp_cliente", None)
    flash("Sesión cerrada correctamente", "success")
    return redirect(url_for("clientes.login"))