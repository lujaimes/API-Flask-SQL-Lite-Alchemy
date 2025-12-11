import uuid  # AÑADIDO: Necesario para generar api_key y uuid en general
from contextlib import contextmanager
from urllib.parse import quote

# Importaciones de SQLAlchemy (reorganizadas y limpiadas)
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, inspect
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.orm import joinedload

# ----------------------------------------------------
# Configuración de la Base de Datos y el Modelo
# ----------------------------------------------------
DATABASE_USER = "dbflaskinacap"
DATABASE_PASSWD = quote("1N@C@P_alumn05")
DATABASE_HOST = "mysql.flask.nogsus.org"
DATABASE_NAME = "api_alumnos"
DATABASE_URL = f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWD}@{DATABASE_HOST}/{DATABASE_NAME}"
# Inicializa el motor de la base de datos
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# ----------------------------------------------------
# Definición de las clases (Modelo de datos)
# ----------------------------------------------------

class Usuario(Base):
    """Modelo para la tabla ldvjf_usuario, incluye api_key."""
    __tablename__ = 'ldvjf_usuario'
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(Text(100000), index=True)
    apellido = Column(String(150), index=True)
    usuario = Column(String(50), index=True)
    clave = Column(String(50), index=True)
    # CORRECCIÓN: Usar uuid.uuid4().hex para asegurar que el default funcione
    api_key = Column(String(250), index=True, default=lambda: uuid.uuid4().hex)

    def to_dict(self):
        # CORRECCIÓN: 'id' del modelo es 'user_id' en la sesión. NO incluir la clave.
        return {"user_id": self.id, "nombre": self.nombre, "apellido": self.apellido,
                "usuario": self.usuario, "api_key": self.api_key}


# ... (Clase Mercado y Producto permanecen iguales) ...
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
# Sesiones
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
# Función de Inicialización y consultas (Corregido)
# ----------------------------------------------------
def create_db_and_tables():
    # ... (código, corregido y usando uuid importado) ...
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


def valida_usuario(usrname, passwd):

    try:
        with get_db() as db:
            user = db.query(Usuario).filter(Usuario.usuario == usrname).first()

            if user and user.clave == passwd:
                # Generar nueva API Key y actualizarla
                user.api_key = uuid.uuid4().hex  # Usa uuid.uuid4().hex
                db.commit()
                db.refresh(user)
                return user.to_dict()  # Retorna el dict sin la clave

            return None  # Credenciales inválidas

    except Exception as e:
        print(f"Lib: models.py. Func: valida_usuario. Error al listar el usuario: {e}")
        return None  # Debe retornar None para que app.py no falle


def is_db_model_created(tables_to_check):
    # No lo quise quitar
    pass