from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template
from functools import wraps
from models.db_mdl import Producto, get_db, Usuario, Mercado
from sqlalchemy.orm import joinedload # Importación necesaria para get_productos

# Define Blueprint para las rutas API
api_routes = Blueprint('api_routes', __name__)


def require_api_key(f):
    """Decorador para verificar la API Key en los headers."""

    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({"error": "API Key requerida"}), 401

        # Corrección: Buscar el usuario por la API Key proporcionada en el header
        try:
            with get_db() as db:
                user = db.query(Usuario).filter(Usuario.api_key == api_key).first()
                if not user:
                    return jsonify({"error": "API Key inválida"}), 401

            # 1. Retorno ok: Si el usuario existe, se ejecuta la función original de la ruta
            return f(*args, **kwargs)

        except Exception as e:
            # 2. Bloque except: Captura errores de DB
            print(f"Error en require_api_key (DB/Conexión): {e}")
            return jsonify({"error": "Error interno de autenticación del servidor"}), 500

    # 3. Retorno del decorador: Debe devolver la función envuelta
    return decorated

@api_routes.route('/api/productos', methods=['GET'])
@require_api_key
def get_productos():
    try:
        with get_db() as db:
            # Corrección: Usar la sesión de DB y cargar el mercado para evitar query problem
            productos = db.query(Producto).options(joinedload(Producto.origen_mercado)).all()
            return jsonify([p.to_dict() for p in productos]), 200
    except Exception as e:
        print(f"Error al obtener productos: {e}")
        return jsonify({"error": "Error interno del servidor al obtener productos"}), 500

#GRAN corrección en el metodo
@api_routes.route('/api/productos/<int:id>', methods=['PUT'])
@require_api_key
def update_producto(id): # Asegúrate de que este es el ÚNICO lugar donde se define update_producto
    if not request.is_json:
        return jsonify({"error": "Contenido debe ser JSON"}), 400

    data = request.get_json()

    try:
        with get_db() as db:
            # 1. Obtener el producto
            producto = db.query(Producto).get(id)
            if not producto:
                return jsonify({"error": "Producto no encontrado"}), 404

            # 2. Opcional: Verificar Mercado si se actualiza idOrigen
            if 'idOrigen' in data:
                mercado = db.query(Mercado).get(data['idOrigen'])
                if not mercado:
                    return jsonify({"error": "ID de Origen (Mercado) no encontrado"}), 400

            # 3. Actualizar campos (usa el nombre de columna CORREGIDO: uMedida)
            producto.nombre = data.get('nombre', producto.nombre)
            producto.precio = data.get('precio', producto.precio)
            producto.uMedida = data.get('uMedida', producto.uMedida)
            producto.idOrigen = data.get('idOrigen', producto.idOrigen)

            db.commit()
            return jsonify({"mensaje": "Producto actualizado con éxito", "producto": producto.to_dict()}), 200

    except Exception as e:
        # El bloque 'with get_db()' ya debería manejar el rollback y el close
        # Si ocurre un error, solo lo registramos y devolvemos el 500
        print(f"Error al actualizar producto: {e}")
        return jsonify({"error": "Error interno del servidor al actualizar producto"}), 500

# ... (otras funciones como delete_producto) ...


@api_routes.route('/api/productos/<int:id>', methods=['DELETE'])
@require_api_key
def delete_producto(id):
    try:
        with get_db() as db:
            # CORRECCIÓN: Usar la sesión de DB
            producto = db.query(Producto).get(id)
            if not producto:
                return jsonify({"error": "Producto no encontrado"}), 404

            db.delete(producto)
            db.commit()
            return jsonify({"mensaje": "Producto eliminado con éxito"}), 200

    except Exception as e:
        if 'db' in locals():
            db.rollback()
        print(f"Error al eliminar producto: {e}")
        return jsonify({"error": "Error interno del servidor al eliminar producto"}), 500

#Inicio función dashboard
@api_routes.route("/dashboard")
def dashboard():
    # 1. Comprobación de seguridad: Si no hay sesión, redirigir al login
    if "user_id" not in session:
        # 'login' es el nombre del endpoint de la función login en app.py (nivel principal)
        return redirect(url_for("login"))

        # 2. Recuperar la API Key de la sesión
    user_api_key = session.get("api_key")

    # 3. Renderizar y pasar la clave
    return render_template("dashboard.html", api_key=user_api_key)