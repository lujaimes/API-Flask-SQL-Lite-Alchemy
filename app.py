import urllib
import secrets
from flask import Flask, request, render_template, redirect, url_for, session, json
# Importar la función de inicialización de la base de datos de SQLAlchemy
from models.db_mdl import create_db_and_tables, valida_usuario, is_db_model_created, get_db, Usuario
from routes.api_routes import api_routes #Corrección

# Claves reCAPTCHA  - obtenida en Google reCAPTCHA
RECAPTCHA_SITE_KEY = "6Ld8iCcsAAAAAB4UTUBrs2BRKt1zXHDGwZWVf4Fg"
RECAPTCHA_SECRET_KEY = "6Ld8iCcsAAAAAHlzgWMbTon-YA382Ld2g-UvoX1K"

# --- Configuración Inicial de la Aplicación ---
api = Flask (__name__, template_folder='templates')

# Generar una clave secreta fuerte para gestionar sesiones
api.secret_key = secrets.token_hex(24)

# Registrar el Blueprint de las rutas de la API
api.register_blueprint(api_routes)

# --- Inicialización de la Base de Datos ---
# Antes de que se sirva la primera solicitud, asegurar que las tablas existen
@api.before_request
def initialize_database():
    """Llama a la función para crear las tablas de la DB usando SQLAlchemy."""
    try:
        if not is_db_model_created(["users", "products"]):
            create_db_and_tables()
            print("Base de datos y tablas inicializadas con éxito con SQLAlchemy.")
    except Exception as e:
        print(f"ERROR: Falló la inicialización de la base de datos: {e}")


# --- RUTAS PÚBLICAS (Login y Logout) ---
#Ruta principal: Dirije al login si no está logra o al dashboar si lo está

@api.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
        #Generar y enviar la página HTML de inicio de sesión al navegador del usuario.
    return render_template("login.html", site_key=RECAPTCHA_SITE_KEY)

# ... (Revisar que 'api_routes' esté importado y registrado) ...
@api.route("/", methods=["GET", "POST"])
def login():
    # 1. Definir la clave del sitio (asegúrate de que esta variable exista)
    site_key = api.config['RECAPTCHA_SITE_KEY']
    msg_out = ""

    if "user_id" in session:
        # CORRECCIÓN: Usar el nombre de endpoint del Blueprint
        return redirect(url_for("api_routes.dashboard"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        recaptcha_response = request.form.get("g-recaptcha-response")

        # Asumimos que result es nulo hasta que se valida
        captcha_success = False

        if not recaptcha_response:
            msg_out = "Debe resolver el CAPTCHA para continuar."
        else:
            # Validación reCAPTCHA (Google)
            verify_url = "https://www.google.com/recaptcha/api/siteverify"

            data = urllib.parse.urlencode({
                "secret": RECAPTCHA_SECRET_KEY,  # Asegúrate de importar RECAPTCHA_SECRET_KEY
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
            # Nota: Verificar que valida_usuario(username, password) usa get_db()
            user = valida_usuario(username, password)

            if user:
                # 3. Login exitoso
                session["user_id"] = user["user_id"]
                session["api_key"] = user["api_key"]

                # Corrección
                return redirect(url_for("api_routes.dashboard"))
            else:
                # 4. Credenciales incorrectas
                msg_out = "Usuario o clave incorrecta."

        # 5. Si el POST falla (CAPTCHA o Credenciales), el flujo continúa al return final

    # RETORNO FINAL (Para GET o si el POST falló la validación)
    # Se utiliza la variable msg_out para mostrar errores.
    return render_template("login.html", message=msg_out, site_key=site_key)


@api.route("/logout")
def logout():
    try:
        with get_db() as db:
            # Corrección
            user = db.query(Usuario).filter(Usuario.id == session.get("user_id")).first()

            if user:
                user.api_key = ""  # Limpia la clave API al cerrar sesión
                db.commit()

        session.pop("user_id", None)
        session.pop("api_key", None)
        return redirect(url_for("home"))  # Redirigir a la ruta principal 'home'

    except Exception as e:
        # En caso de error de DB, simplemente cierra la sesión para no bloquear el logout
        session.pop("user_id", None)
        return redirect(url_for("home"))

#Corrección
@api_routes.route("/dashboard")
def dashboard():
    # 1. Comprobación de seguridad: Si no hay sesión, redirigir al login
    if "user_id" not in session:
        return redirect(url_for("login"))

        # 2. Recuperar la API Key de la sesión
    user_api_key = session.get("api_key")

    # 3. Renderizar y pasar la clave
    return render_template("dashboard.html", api_key=user_api_key)

if __name__ == "__main__":
    api.run(debug=True)