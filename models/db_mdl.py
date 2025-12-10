from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template
from functools import wraps
from models.db_mdl import Producto, get_db, Usuario, Mercado
from sqlalchemy.orm import joinedload # Importación necesaria para get_productos

DATABASE_USER = "dbflaskinacap"
DATABASE_PASSWD = quote("1N@C@P_alumn05")
DATABASE_HOST = "mysql.flask.nogsus.org"
DATABASE_NAME = "api_alumnos"
DATABASE_URL = f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWD}@{DATABASE_HOST}/{DATABASE_NAME}"
#DATABASE_URL = f"mysql+pymysql://dbflaskinacap:P_alumn05@mysql.flask.nogsus.org/api_alumnos"

# Inicializa el motor de la base de datos
engine = create_engine(DATABASE_URL)

# Base declarativa que será la madre de todas nuestras clases de modelos
Base = declarative_base()

# ----------------------------------------------------
# Definición de la clase de la tabla (función que genera la tabla usuario)
# ----------------------------------------------------
class Usuario(Base):
    """Modelo para la tabla ldvjf_usuario, incluye api_key."""
    __tablename__ = 'ldvjf_usuario' #uso del prefijo ldvjf
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(Text(100000), index=True)
    apellido = Column(String(150), index=True)
    usuario = Column(String(50), index=True)
    clave = Column(String(50), index=True)
    api_key = Column(String(250), index=True, default=lambda: str(uuid.uuid4().hex))  # Columna API Key

    def to_dict(self):
        # Corrección: No incluir clave en el diccionario
        return {"user_id": self.id, "nombre": self.nombre, "apellido": self.apellido,
                "usuario": self.usuario, "api_key": self.api_key}

class Mercado(Base):
    """Modelo para la tabla ldvjf_mercados."""
    __tablename__ = 'ldvjf_mercados'
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), index=True)

    productos = relationship("Producto", back_populates="origen_mercado", cascade="all, delete-orphan")

    def to_dict(self):
        return {"id": self.id, "nombre": self.nombre}

class Producto(Base):
    """Modelo para la tabla ldvjf_productos, con clave foránea a Mercado."""
    __tablename__ = 'ldvjf_productos'
    id = Column(Integer, primary_key=True, index=True)
    idOrigen = Column(Integer, ForeignKey('ldvjf_mercados.id'), nullable=False, index=True)
    nombre = Column(String(150), index=True)
    uMedida = Column(String(100), index=True) # Nombre de campo uMedida, debe coincidir con el JSON.
    precio = Column(Integer, index=True)

    origen_mercado = relationship("Mercado", back_populates="productos")

    def to_dict(self):
        return {"id": self.id, "idOrigen": self.idOrigen, "nombre": self.nombre,
                "uMedida": self.uMedida, "precio": self.precio,
                # Incluimos el nombre del mercado para facilitar la lectura en el frontend
                "origen_mercado": self.origen_mercado.nombre if self.origen_mercado else None
                }

# ----------------------------------------------------
# Sesiones locales para interactuar con la DB
# ----------------------------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ----------------------------------------------------
# Función de Control de Conexión (Context Manager)
# ----------------------------------------------------
@contextmanager
def get_db():
    """
    Función que controla la conexión a la base de datos (sesión).
    Garantiza que la sesión se cierre correctamente después de su uso.
    """
    db = SessionLocal()
    try:
        # Entrega la sesión de DB al bloque 'with'
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

# ----------------------------------------------------
# Función de Inicialización y consultas (app.py)
# ----------------------------------------------------

def create_db_and_tables():
    """Crea todas las tablas y el usuario inicial (LDVJF/123456)."""
    Base.metadata.create_all(bind=engine)

    with get_db() as db:
        if not db.query(Usuario).filter(Usuario.usuario == 'LDVJF').first():
            print("Creando usuario 'LDVJF' y mercados iniciales.")

            # Crear usuario de prueba
            admin_user = Usuario(nombre="Usuario", apellido="Validacion", usuario="LDVJF", clave="123456")

            db.add(admin_user)

            # Mercados iniciales
            mercados_iniciales = ["Puerto Montt", "Osorno", "Temuco", "Chillan", "Talca", "Rancagua"]
            for nombre in mercados_iniciales:
                if not db.query(Mercado).filter(Mercado.nombre == nombre).first():
                    db.add(Mercado(nombre=nombre))

            db.commit()
            print("Inicialización completa. Usuario de prueba LDVJF/123456 creado.")
        else:
            print("Tablas y usuario de validación LDVJF ya existen.")


def is_db_model_created(tables_to_check):
    """Verifica si al menos una tabla del modelo ha sido creada."""
    # Aquí es donde DEBES usar la función 'inspect' que importaste:
    inspector = inspect(engine)

    # Comprobamos si la tabla de usuario existe como proxy para saber si el modelo se inicializó
    if 'ldvjf_usuario' in inspector.get_table_names():
        return True
    return False

def valida_usuario (usrname, passwd):
    """
    Valida las credenciales y, si es correcto, genera una nueva API Key y la guarda.
    Usa comparación de texto plano simple.
    """
    try:
        with get_db() as db:
            # Buscar usuario por nombre
            user = db.query(Usuario).filter(Usuario.usuario == usrname).first()

            # Validación simple de texto plano
            if user and user.clave == passwd:
                # Generar nueva API Key y actualizarla
                user.api_key = uuid.uuid4().hex
                db.commit()
                db.refresh(user)
                return user.to_dict()  # Retorna el dict sin la clave

            return None  # Credenciales inválidas

    except Exception as e:
        # CORRECCIÓN CRÍTICA: Retornar None en caso de error de DB para no romper el flujo de app.py
        print(f"Lib: models.py. Func: valida_usuario. Error al listar el usuario: {e}")
        return None # Antes retornaba un dict de error que causaba un fallo