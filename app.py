# --- INICIO DEL ARCHIVO app.py ---

from flask import Flask, render_template, request, redirect, url_for, flash, session
from models.db_mdl import db, Usuario, Mercado
from routes.api_routes import api_routes
import os
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import quote_plus  # Necesario para la contraseña con '@'

# ------------------------------------------------
# CONFIGURACIÓN DE LA APLICACIÓN Y BASE DE DATOS
# ------------------------------------------------

# 1. TUS CREDENCIALES DE DB (¡AJUSTAR ESTO CON TUS DATOS!)
DB_USER = 'dbflaskinacap'
DB_PASS_RAW = '1N@C@P_alumn05'
DB_HOST = 'mysql.flask.nogsus.org'
DB_PORT = '3306'
DB_NAME = 'api_alumnos'
# ------------------------------------------------

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu_clave_secreta_aqui'

# 2. CONFIGURACIÓN DEL URI DE LA DB (USA quote_plus)
app.config['SQLALCHEMY_DATABASE_URI'] = \
    f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASS_RAW)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 3. INICIALIZACIÓN DE DB CON LA APP
db.init_app(app)


# ------------------------------------
# 1. Rutas Web (Login y Dashboard)
# ------------------------------------
# ... (Tus rutas web)
# ...

# ------------------------------------
# 2. Inicialización de la DB
# ------------------------------------

def initialize_database(app):
    """Crea las tablas y el usuario de prueba si no existen"""
    try:
        with app.app_context():
            print("Conectando a DB y verificando tablas ldvjf_...")
            # db.drop_all() HA SIDO ELIMINADO PERMANENTEMENTE.
            db.create_all()

            # USUARIO LDVJF/123456
            if not Usuario.query.filter_by(usuario='LDVJF').first():
                print("Creando usuario 'LDVJF' (Login: LDVJF/123456) y mercados iniciales.")
                admin_user = Usuario(nombre="Usuario", apellido="Validacion", usuario="LDVJF")
                admin_user.set_password('123456')
                db.session.add(admin_user)

                # Mercados iniciales
                mercados_iniciales = [
                    "Puerto Montt", "Osorno", "Temuco", "Chillan", "Talca", "Rancagua"
                ]
                for nombre in mercados_iniciales:
                    if not Mercado.query.filter_by(nombre=nombre).first():
                        db.session.add(Mercado(nombre=nombre))

                db.session.commit()
                print("Inicialización completa. Usuario de prueba LDVJF/123456 creado.")
            else:
                print("Tablas y usuario de validación LDVJF ya existen.")

    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")


# REGISTRAR EL BLUEPRINT DE LAS RUTAS API
app.register_blueprint(api_routes)

if __name__ == '__main__':
    initialize_database(app)
    app.run(debug=True)

# --- FIN DEL ARCHIVO app.py ---