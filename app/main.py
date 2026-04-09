from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
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
            
            if any(col not in columns for col in ["tipo_periodo", "fecha_fin", "dias_trabajados"]):
                conn.commit()
            else:
                print("✔ Columnas validadas. No requieren migración extra.")
        except Exception as e:
            print(f"⚠ Error en migración: {e}")

run_migrations()

# Incluimos las rutas definidas en la capa API
app.include_router(endpoints.router)

@app.get("/")
def read_root():
    return {"mensaje": "API de Control de Proyectos operativa"}

