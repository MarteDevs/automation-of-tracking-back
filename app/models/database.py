from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Crearemos un archivo local llamado "control_soldadura.db" en la raíz
SQLALCHEMY_DATABASE_URL = "sqlite:///./control_soldadura.db"

# connect_args={"check_same_thread": False} es necesario solo para SQLite en FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependencia para inyectar la sesión de la BD en los endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
