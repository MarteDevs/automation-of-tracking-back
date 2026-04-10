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

# Configuración extendida de CORS (Extraccion Segura Env)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origenes,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Migración automática: añadir columna tipo_periodo si no existe ──
def run_migrations():
    from sqlalchemy import text
    with engine.connect() as conn:
        try:
            # Verificar si la columna ya existe en SQLite
            result_proy = conn.execute(text("PRAGMA table_info(proyectos)"))
            columns_proy = [row[1] for row in result_proy.fetchall()]
            if "tipo_duracion" not in columns_proy:
                conn.execute(text(
                    "ALTER TABLE proyectos ADD COLUMN tipo_duracion VARCHAR DEFAULT 'SEMANAS' NOT NULL"
                ))
                conn.commit()
                print("✔ Migración aplicada: columna tipo_duracion añadida en proyectos.")
                
            if "otros_porcentaje" not in columns_proy:
                conn.execute(text(
                    "ALTER TABLE proyectos ADD COLUMN otros_porcentaje REAL DEFAULT 5.0"
                ))
                conn.commit()
                print("✔ Migración aplicada: columna otros_porcentaje añadida en proyectos.")

            if "ruta_pdf" not in columns_proy:
                conn.execute(text("ALTER TABLE proyectos ADD COLUMN ruta_pdf TEXT"))
                conn.commit()
                print("✔ Migración aplicada: columna ruta_pdf añadida en proyectos.")
                
            result = conn.execute(text("PRAGMA table_info(avances_semanales)"))
            columns = [row[1] for row in result.fetchall()]
            if "tipo_periodo" not in columns:
                conn.execute(text(
                    "ALTER TABLE avances_semanales ADD COLUMN tipo_periodo VARCHAR DEFAULT 'SEMANA' NOT NULL"
                ))
                print("✔ Migración aplicada: columna tipo_periodo añadida.")
            if "fecha_fin" not in columns:
                conn.execute(text(
                    "ALTER TABLE avances_semanales ADD COLUMN fecha_fin VARCHAR"
                ))
                print("✔ Migración aplicada: columna fecha_fin añadida.")
            if "dias_trabajados" not in columns:
                conn.execute(text(
                    "ALTER TABLE avances_semanales ADD COLUMN dias_trabajados REAL DEFAULT 0"
                ))
                print("✔ Migración aplicada: columna dias_trabajados añadida.")
            
            if "ruta_pdf" not in columns:
                conn.execute(text("ALTER TABLE avances_semanales ADD COLUMN ruta_pdf TEXT"))
                print("✔ Migración aplicada: columna ruta_pdf añadida en avances_semanales.")
                
            # Migraciones para Costos Fijos (Mano Obra) y Variables (Materiales)
            res_mo = conn.execute(text("PRAGMA table_info(mano_de_obra)"))
            cols_mo = [row[1] for row in res_mo.fetchall()]
            if "categoria" not in cols_mo:
                conn.execute(text("ALTER TABLE mano_de_obra ADD COLUMN categoria VARCHAR DEFAULT 'Mano de Obra'"))
                conn.execute(text("ALTER TABLE mano_de_obra ADD COLUMN unidad VARCHAR DEFAULT ''"))
                conn.execute(text("ALTER TABLE mano_de_obra ADD COLUMN dias REAL DEFAULT 1.0"))
                print("✔ Migración aplicada: columnas extendidas en mano_de_obra.")
            
            res_mat = conn.execute(text("PRAGMA table_info(materiales_equipos)"))
            cols_mat = [row[1] for row in res_mat.fetchall()]
            if "categoria" not in cols_mat:
                conn.execute(text("ALTER TABLE materiales_equipos ADD COLUMN categoria VARCHAR DEFAULT 'Materiales'"))
                conn.execute(text("ALTER TABLE materiales_equipos ADD COLUMN precio_unitario REAL DEFAULT 0.0"))
                conn.execute(text("ALTER TABLE materiales_equipos ADD COLUMN dias REAL DEFAULT 1.0"))
                print("✔ Migración aplicada: columnas extendidas en materiales_equipos.")
            conn.commit()
            if any(col not in columns for col in ["tipo_periodo", "fecha_fin", "dias_trabajados"]):
                conn.commit()
            else:
                print("✔ Columnas validadas. No requieren migración extra.")
        except Exception as e:
            print(f"⚠ Error en migración: {e}")

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

