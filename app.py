import secrets
import urllib
from flask import Flask, request, render_template, redirect, url_for, session, json, jsonify
# Importar la función de inicialización de la base de datos de SQLAlchemy
from models.db_mdl import create_db_and_tables, valida_usuario, is_db_model_created, get_db, Usuario
from routes.api_routes import api_routes

# Claves reCAPTCHA obtenidas de Google reCAPTCHA
RECAPTCHA_SITE_KEY = "6Ld8iCcsAAAAAB4UTUBrs2BRKt1zXHDGwZWVf4Fg"
RECAPTCHA_SECRET_KEY = "6Ld8iCcsAAAAAHlzgWMbTon-YA382Ld2g-UvoX1K"

# --- Configuración Inicial de la Aplicación ---
api = Flask(__name__, template_folder='templates')
api.secret_key = secrets.token_hex(24)

# Asignar claves al objeto de configuración de Flask
api.config['RECAPTCHA_SITE_KEY'] = RECAPTCHA_SITE_KEY
api.config['RECAPTCHA_SECRET_KEY'] = RECAPTCHA_SECRET_KEY

api.register_blueprint(api_routes, url_prefix="/api")

# ----------------------------------------------------
# Inicialización de la Base de Datos
# ----------------------------------------------------
# Antes de que se sirva la primera solicitud, asegurar que las tablas existen

@api.before_request
def initialize_database():
    """Llama a la función para crear las tablas de la DB usando SQLAlchemy."""
    try:
        # Se asume que 'users' es 'ldvjf_usuario'
        if not is_db_model_created(["ldvjf_usuario"]):
            create_db_and_tables()
            print("Base de datos y tablas inicializadas con éxito con SQLAlchemy.")
    except Exception as e:
        # Si la DB remota falla, el servidor aún debe iniciar (OperationalError)
        print(f"ERROR: Falló la inicialización de la base de datos: {e}")

# ----------------------------------------------------
# RUTAS PÚBLICAS (Login y Logout
# ----------------------------------------------------
# CORRECCIÓN: Ruta fusionada

@api.route("/", methods=["GET", "POST"])
def login():
    site_key = api.config['RECAPTCHA_SITE_KEY']
    msg_out = ""

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]
        recaptcha_response = request.form.get("g-recaptcha-response")
        captcha_success = False

        if not recaptcha_response:
            msg_out = "Debe resolver el CAPTCHA para continuar."
        else:
            # Validación reCAPTCHA
            # Si la validación pasa: captcha_success = True

            verify_url = "https://www.google.com/recaptcha/api/siteverify"
            data = urllib.parse.urlencode({
                "secret": api.config['RECAPTCHA_SECRET_KEY'],
                "response": recaptcha_response
            }).encode()

            req = urllib.request.Request(verify_url, data=data)
            try:
                response = urllib.request.urlopen(req)
                result = json.loads(response.read().decode())
                captcha_success = result.get("success", False)
            except Exception as e:
                print(f"Error de red/JSON al validar CAPTCHA: {e}")
                msg_out = "Error de conexión al validar CAPTCHA."

            if not captcha_success:
                msg_out = "Verificación reCAPTCHA fallida."

        # 2. Si el CAPTCHA pasó, verificar el usuario
        if captcha_success:
            user = valida_usuario(username, password)  # Retorna dict o None

            if user:
                # 3. Login exitoso
                session["user_id"] = user["user_id"]
                session["api_key"] = user["api_key"]

                # Redirigir a la ruta dashboard (definida abajo)
                return redirect(url_for("dashboard"))
            else:
                # 4. Credenciales incorrectas o fallo de DB en valida_usuario
                msg_out = "Usuario o clave incorrecta."

    # RETORNO FINAL (Para GET o si el POST falló la validación)
    return render_template("login.html", message=msg_out, site_key=site_key)


@api.route("/logout")
def logout():
    try:
        with get_db() as db:
            # USAR EL ID DE LA SESIÓN
            user = db.query(Usuario).filter(Usuario.id == session.get("user_id")).first()

            if user:
                user.api_key = ""  # Limpia la clave API al cerrar sesión
                db.commit()

        session.pop("user_id", None)
        session.pop("api_key", None)
        return redirect(url_for("login"))  # Redirigir a la función login (ruta '/')

    except Exception as e:
        print(f"Error en logout: {e}")
        session.pop("user_id", None)
        session.pop("api_key", None)
        return redirect(url_for("login"))

@api.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_api_key = session.get("api_key")
    return render_template("dashboard.html", api_key=user_api_key)

if __name__ == "__main__":
    api.run(debug=True)