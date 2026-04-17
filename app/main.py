from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from app.api import endpoints
from app.models.database import engine
from app.models import models

# Crea todas las tablas en la Base de Datos en el inicio
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Control de Proyectos - Soldadura")

load_dotenv()
# Lee los dominios directamente desde el .env y genera Lista nativa.
origenes = os.environ.get("ALLOWED_ORIGINS", "*").split(",")

# Configuración extendida de CORS (Extracción Segura Env)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origenes if origenes != ["*"] else ["*"],
    allow_credentials=True if origenes != ["*"] else False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ── Migración automática: verificador de esquema robusto ──
def run_migrations():
    from sqlalchemy import text
    
    def column_exists(conn, table_name, column_name):
        res = conn.execute(text(f"PRAGMA table_info({table_name})"))
        columns = [row[1] for row in res.fetchall()]
        return column_name in columns

    def add_column_if_not_exists(conn, table_name, column_name, column_def):
        if not column_exists(conn, table_name, column_name):
            try:
                conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}"))
                conn.commit()
                print(f"✔ Migración aplicada: columna {column_name} añadida en {table_name}.")
            except Exception as e:
                print(f"⚠ Error al añadir {column_name} en {table_name}: {e}")
        else:
            # print(f"DEBUG: Columna {column_name} ya existe en {table_name}.")
            pass

    with engine.connect() as conn:
        try:
            # --- Tabla Proyectos ---
            add_column_if_not_exists(conn, "proyectos", "tipo_duracion", "VARCHAR DEFAULT 'SEMANAS' NOT NULL")
            add_column_if_not_exists(conn, "proyectos", "otros_porcentaje", "REAL DEFAULT 5.0")
            add_column_if_not_exists(conn, "proyectos", "ruta_pdf", "TEXT")
            add_column_if_not_exists(conn, "proyectos", "ruta_foto_final", "TEXT")

            # --- Tabla Avances Semanales ---
            add_column_if_not_exists(conn, "avances_semanales", "tipo_periodo", "VARCHAR DEFAULT 'SEMANA' NOT NULL")
            add_column_if_not_exists(conn, "avances_semanales", "fecha_fin", "VARCHAR")
            add_column_if_not_exists(conn, "avances_semanales", "dias_trabajados", "REAL DEFAULT 0")
            add_column_if_not_exists(conn, "avances_semanales", "ruta_pdf", "TEXT")
            add_column_if_not_exists(conn, "avances_semanales", "rutas_facturas", "TEXT")

            # --- Tabla Mano de Obra ---
            add_column_if_not_exists(conn, "mano_de_obra", "categoria", "VARCHAR DEFAULT 'Mano de Obra'")
            add_column_if_not_exists(conn, "mano_de_obra", "unidad", "VARCHAR DEFAULT ''")
            add_column_if_not_exists(conn, "mano_de_obra", "dias", "REAL DEFAULT 1.0")

            # --- Tabla Materiales Equipos ---
            add_column_if_not_exists(conn, "materiales_equipos", "categoria", "VARCHAR DEFAULT 'Materiales'")
            add_column_if_not_exists(conn, "materiales_equipos", "precio_unitario", "REAL DEFAULT 0.0")
            add_column_if_not_exists(conn, "materiales_equipos", "dias", "REAL DEFAULT 1.0")
            
            print("✔ Verificación de esquema completada con éxito.")
        except Exception as e:
            print(f"⚠ Error general en la verificación de esquema: {e}")

run_migrations()

# Incluimos las rutas definidas en la capa API
app.include_router(endpoints.router)

# --- Montaje de archivos estáticos para acceso a Reportes y Evidencias ---
# Asegura que la carpeta uploads exista físicamente
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(os.path.dirname(BASE_DIR), "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

@app.get("/")
def read_root():
    return {"mensaje": "API de Control de Proyectos operativa"}

