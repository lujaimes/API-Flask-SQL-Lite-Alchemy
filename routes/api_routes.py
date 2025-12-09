from flask import Blueprint, request, jsonify
from functools import wraps
from models.db_mdl import Producto, valida_usuario, db, Mercado  # Importar Mercado
from sqlalchemy.exc import IntegrityError
import json

# Define un Blueprint para las rutas API
api_routes = Blueprint('api_routes', __name__)


def require_api_key(f):
    """Decorador para verificar la API Key en los headers."""

    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({"error": "API Key requerida"}), 401

        user = valida_usuario(usuario_in='LDVJF', clave_in='123456')

        if not user or user.api_key != api_key:
            return jsonify({"error": "API Key inválida"}), 401

        return f(*args, **kwargs)

    return decorated


@api_routes.route('/api/productos', methods=['GET'])
@require_api_key
def get_productos():
    try:
        productos = Producto.query.all()
        return jsonify([p.to_dict() for p in productos]), 200
    except Exception as e:
        print(f"Error al obtener productos: {e}")
        return jsonify({"error": "Error interno del servidor al obtener productos"}), 500


@api_routes.route('/api/productos', methods=['POST'])
@require_api_key
def add_producto():
    if not request.is_json:
        return jsonify({"error": "Contenido debe ser JSON"}), 400

    try:
        data = request.get_json()

        if not all(k in data for k in ['nombre', 'precio', 'unidad_de_medida', 'idOrigen']):
            return jsonify({"error": "Faltan campos obligatorios"}), 400

        # *** SOLUCIÓN DEFINITIVA: VERIFICAR SI EL MERCADO EXISTE ***
        mercado = Mercado.query.get(data['idOrigen'])
        if not mercado:
            return jsonify({"error": "ID de Origen (Mercado) no encontrado"}), 400  # 400: Error de cliente

        nuevo_producto = Producto(
            nombre=data['nombre'],
            precio=data['precio'],
            unidad_de_medida=data['unidad_de_medida'],
            idOrigen=data['idOrigen']
        )

        db.session.add(nuevo_producto)
        db.session.commit()
        return jsonify({"mensaje": "Producto insertado con éxito", "id": nuevo_producto.id}), 201

    except IntegrityError:
        db.session.rollback()
        # Este error solo ocurre si el ID Origen existe pero hay un problema más profundo.
        return jsonify({"error": "Error de integridad de la base de datos (clave duplicada, etc.)"}), 500
    except Exception as e:
        db.session.rollback()
        print(f"Error al agregar producto: {e}")
        return jsonify({"error": "Error interno del servidor al agregar producto"}), 500


@api_routes.route('/api/productos/<int:id>', methods=['PUT'])
@require_api_key
def update_producto(id):
    producto = Producto.query.get(id)
    if not producto:
        return jsonify({"error": "Producto no encontrado"}), 404

    if not request.is_json:
        return jsonify({"error": "Contenido debe ser JSON"}), 400

    try:
        data = request.get_json()

        # Opcional: Verificar Mercado si se actualiza idOrigen
        if 'idOrigen' in data:
            mercado = Mercado.query.get(data['idOrigen'])
            if not mercado:
                return jsonify({"error": "ID de Origen (Mercado) no encontrado"}), 400

        producto.nombre = data.get('nombre', producto.nombre)
        producto.precio = data.get('precio', producto.precio)
        producto.unidad_de_medida = data.get('unidad_de_medida', producto.unidad_de_medida)
        producto.idOrigen = data.get('idOrigen', producto.idOrigen)

        db.session.commit()
        return jsonify({"mensaje": "Producto actualizado con éxito", "producto": producto.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error al actualizar producto: {e}")
        return jsonify({"error": "Error interno del servidor al actualizar producto"}), 500


@api_routes.route('/api/productos/<int:id>', methods=['DELETE'])
@require_api_key
def delete_producto(id):
    producto = Producto.query.get(id)
    if not producto:
        return jsonify({"error": "Producto no encontrado"}), 404

    try:
        db.session.delete(producto)
        db.session.commit()
        return jsonify({"mensaje": "Producto eliminado con éxito"}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error al eliminar producto: {e}")
        return jsonify({"error": "Error interno del servidor al eliminar producto"}), 500