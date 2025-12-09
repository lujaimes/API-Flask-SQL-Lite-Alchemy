import uuid
from flask_sqlalchemy import SQLAlchemy
# from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ----------------------------------------------------
# 1. Modelo de Usuario (ldvjf_usuario)
# ----------------------------------------------------
class Usuario(db.Model):
    __tablename__ = 'ldvjf_usuario'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    apellido = db.Column(db.String(150), nullable=False)
    usuario = db.Column(db.String(80), unique=True, nullable=False)
    clave = db.Column(db.String(128), nullable=False)
    api_key = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))

    def set_password(self, password):
        # Nota: Idealmente usar generate_password_hash(password)
        self.clave = password

    def check_password(self, password):
        # Nota: Idealmente usar check_password_hash(self.clave, password)
        return self.clave == password

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'apellido': self.apellido,
            'usuario': self.usuario,
            'api_key': self.api_key
        }


# ----------------------------------------------------
# 2. Modelo de Mercado (ldvjf_mercados)
# ----------------------------------------------------
class Mercado(db.Model):
    __tablename__ = 'ldvjf_mercados'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)


# ----------------------------------------------------
# 3. Modelo de Producto (ldvjf_productos)
# ----------------------------------------------------
class Producto(db.Model):
    __tablename__ = 'ldvjf_productos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    precio = db.Column(db.Integer, nullable=False)
    unidad_de_medida = db.Column(db.String(100))
    # *** CÓDIGO ORIGINAL CON CLAVE FORÁNEA (CORREGIDO) ***
    idOrigen = db.Column(db.Integer, db.ForeignKey('ldvjf_mercados.id'), nullable=False)

    def to_dict(self):
        """Retorna el producto como diccionario."""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'precio': self.precio,
            'unidad_de_medida': self.unidad_de_medida,
            'idOrigen': self.idOrigen,
        }

def valida_usuario(usuario_in, clave_in):
    """Valida usuario y clave para la ruta API."""
    try:
        user = Usuario.query.filter_by(usuario=usuario_in).first()
        if user and user.check_password(clave_in):
            return user
        return None
    except Exception as e:
        print(f"Error en valida_usuario: {e}")
        return None